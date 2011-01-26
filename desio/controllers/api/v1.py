"""
"""

from pylons_common.lib.utils import itemize
from desio.api import CanReadOrg

class error:
    class explode: pass
    class explode_no_auth: pass
    class jserror: pass

class user:
    class pretend: pass
    class masquerade: pass
    class stop_pretending: pass
    
    class edit:
        def output(self, u):
            return user.get().output(u)
    class get:
        def output(self, u):
            return itemize(u, 'email', 'display_username', 'is_active', 'first_name', 'last_name', 'default_timezone')
    class set_pref: pass

class organization:
    
    class attach_user: pass
    class remove_user: pass
    class attachment_approval: pass
    class set_user_role: pass
    
    class edit:
        def output(self, o):
            return organization.get().output(o)
    
    class get:
        def output(self, org):
            return itemize(org, 'subdomain', 'name')

class project:
    class create: pass
    class get: pass
