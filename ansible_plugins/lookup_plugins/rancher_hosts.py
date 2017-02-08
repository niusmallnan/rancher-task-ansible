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

            for host in client.list_host():
                # FIXME
                if host.agentState is None and host.state == "active":
                    host.agentState = "active"

                ret.append({"id": host.id,
                            "name": host.name or host.hostname,
                            "state": host.state,
                            "agentState": host.agentState})

        return ret
