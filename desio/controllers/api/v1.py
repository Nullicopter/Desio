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
            d = itemize(u, 'id', 'email', 'username', 'is_active', 'default_timezone')
            d['name'] = u.human_name
            return d
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
    
    class get_users:
        def output(self, org_users):
            return [{'user': user.get().output(ou.user), 'role': ou.role, 'status': ou.status} for ou in org_users]

class project:
    class remove_user: pass
    class set_user_role: pass
    
    class create:
        def output(self, proj):
            return project.get().output(proj)
    
    class edit:
        def output(self, proj):
            return project.get().output(proj)
    
    class get: 
        def output(self, proj):
            return itemize(proj, 'eid', 'name', 'description', 'slug')
    
    class attach_user:
        def output(self, org_user):
            return {'user': user.get().output(org_user.user), 'role': org_user.role, 'status': org_user.status}
    
    class attach_users:
        def output(self, org_users):
            return project.get_users().output(org_users)
    
    class get_users:
        def output(self, org_users):
            return [project.attach_user().output(ou) for ou in org_users]

class file:
    class upload: pass