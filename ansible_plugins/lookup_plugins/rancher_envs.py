from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


HAVE_RANCHER_CLIENT=False
try:
    import gdapi
    HAVE_RANCHER_CLIENT=True
except ImportError:
    pass

from ansible.errors import AnsibleError
from ansible.plugins.lookup import LookupBase


class LookupModule(LookupBase):

    def run(self, terms, variables=None, **kwargs):

        if not HAVE_RANCHER_CLIENT:
            raise AnsibleError("Can't LOOKUP(rancher_envs): module gdapi is not installed")

        ret = []
        for term in terms:
            rancher_url = term["url"]
            access_key = term["access_key"]
            secret_key = term["secret_key"]

            client = gdapi.Client(url=rancher_url,
                                  access_key=access_key,
                                  secret_key=secret_key)

            for env in client.list_project(all=True):
                # filter inactive envs
                if env.state != "active":
                    continue
                ret.append({"id": env.id,
                            "name": env.name,
                            "state": env.state})

        return ret
