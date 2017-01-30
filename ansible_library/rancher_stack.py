#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division, print_function)

import gdapi
from ansible.module_utils.basic import AnsibleModule

try:
    import http.client as http_client
except ImportError:
    # Python 2
    import httplib as http_client


def get_client(params):
    rancher_parameters = params["rancher_parameters"]
    client = gdapi.Client(**rancher_parameters)
    del params["rancher_parameters"]
    return client

def check_stack(client, module):
    params = module.params
    env_id = params["env_id"]
    stack_name = params["stack_name"]
    env = client.by_id_project(env_id)
    stacks = env.environments(name=stack_name)
    if len(stacks) == 0:
        return {"checked": False}
    stack = stacks[0]
    if stack.healthState != params["should_health_state"]:
        msg = "Failed to check env: %s, stack: %s, healthState: %s" % (env_id,
                                                                       stack_name,
                                                                       stack.healthState)
        module.fail_json(msg=msg)

def stop_stack(client, params):
    pass

def upgrade_stack(client, params):
    pass

def finish_upgrade(client, params):
    pass


def main():

    fields = {
        "rancher_parameters": {"required": True, "type": "dict"},
        "stack_name": {"required": True, "type": "str"},
        "env_id": {"required": True, "type": "str"},
        "action": {"required": True, "type": "str"},
        "debug": {"required": False, "default": False, "type": "bool" },

        # for stack check
        "should_health_state": {"required": False, "default": "healthy", "type": "str"},
    }

    choice_map = {
        "check": check_stack,
        "stop": stop_stack,
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
