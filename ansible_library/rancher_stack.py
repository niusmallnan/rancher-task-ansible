#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division, print_function)

import os
import gdapi
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_bytes

try:
    import http.client as http_client
except ImportError:
    # Python 2
    import httplib as http_client


def get_file_content(module, path):
    b_path = to_bytes(path, errors='surrogate_or_strict')
    content = None
    if os.path.isfile(b_path):
        with open(b_path, "r") as content_file:
            content = content_file.read()
    if not content:
        msg = "Failed to read file: %s" % path
        module.fail_json(msg=msg)
    return content

def get_client(params):
    rancher_parameters = params["rancher_parameters"]
    client = gdapi.Client(**rancher_parameters)
    del params["rancher_parameters"]
    return client

def get_env_and_stack(client, params):
    env_id = params["env_id"]
    stack_name = params["stack_name"]
    env = client.by_id_project(env_id)
    stacks = env.environments(name=stack_name)
    if len(stacks) == 0:
        return (env, None)
    return env, stacks[0]

def check_stack(client, module):
    params = module.params
    env, stack = get_env_and_stack(client, params)
    if not stack:
        return {"checked": False}
    if params["ignore_empty_env"] and len(env.hosts()) == 0:
        return {"checked": True}

    if params["should_health_state"] and stack.healthState != params["should_health_state"]:
        msg = "Failed to check env: %s, stack: %s, healthState: %s" % (env.id,
                                                                       stack.name,
                                                                       stack.healthState)
        module.fail_json(msg=msg)
    if params["should_state"] and stack.state != params["should_state"]:
        msg = "Failed to check env: %s, stack: %s, state: %s" % (env.id,
                                                                 stack.name,
                                                                 stack.state)
        module.fail_json(msg=msg)
    return {"checked": True}

def stop_stack(client, module):
    params = module.params
    env, stack = get_env_and_stack(client, params)
    if len(env.hosts()) == 0:
        return {"stopped": True}
    if stack.healthState == 'healthy':
        stack.deactivateservices()
    return {"stopped": stack.healthState=="unhealthy"}

def start_stack(client, module):
    params = module.params
    env, stack = get_env_and_stack(client, params)
    if len(env.hosts()) == 0:
        return {"active": True}
    if stack.healthState == 'unhealthy':
        stack.activateservices()
    return {"active": stack.healthState=="healthy"}

def upgrade_stack(client, module):
    params = module.params
    env, stack = get_env_and_stack(client, params)
    if not stack:
        msg = "Stack is not found, env: %s, stack: %s" % (params["env_id"],
                                                          params["stack_name"])
        module.fail_json(msg=msg)

    if stack.state == "active":
        if stack.externalId == params["external_id"]:
            return {"upgraded": True}

        docker_compose = get_file_content(module, params["docker_compose"])
        rancher_compose = get_file_content(module, params["rancher_compose"])

        stack.upgrade(dockerCompose=docker_compose,
                      rancherCompose=rancher_compose,
                      environment=params["environment"],
                      externalId=params["external_id"])
    return {"upgraded": stack.state=="upgraded"}

def finish_upgrade(client, module):
    params = module.params
    env, stack = get_env_and_stack(client, params)
    if stack.state == 'upgraded':
        stack.finishupgrade()
    return {"active": stack.state=="active"}


def main():

    fields = {
        "rancher_parameters": {"required": True, "type": "dict"},
        "stack_name": {"required": True, "type": "str"},
        "env_id": {"required": True, "type": "str"},
        "action": {"required": True, "type": "str"},
        "debug": {"required": False, "default": False, "type": "bool" },

        # for stack check
        "should_health_state": {"required": False, "type": "str"},
        "should_state": {"required": False, "type": "str"},
        "ignore_empty_env": {"required": False, "default": False, "type": "bool" },

        # for stack upgrade
        "docker_compose": {"required": False, type:"path"},
        "rancher_compose": {"required": False, type:"path"},
        "environment": {"required": False, "default": {}, "type": "dict"},
        "external_id": {"required": False, "type": "str"},
    }

    choice_map = {
        "check": check_stack,
        "deactivateservices": stop_stack,
        "activateservices": start_stack,
        "upgrade": upgrade_stack,
        "finish_upgrade": finish_upgrade,
    }

    module = AnsibleModule(argument_spec=fields)
    if module.params["debug"]:
        http_client.HTTPConnection.debuglevel = 1

    client = get_client(module.params)
    result = choice_map.get(module.params['action'])(client, module)
    module.exit_json(changed=False, meta=result)


if __name__ == '__main__':
    main()
