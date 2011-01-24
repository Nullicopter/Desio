
from desio import api
from desio.lib.base import *

from desio.model import users

class InspectController(BaseController):
    
    def __before__(self, *a, **kw):
        c.tab = 'Search'
        auth.get_user()
        auth.get_real_user()
        
    def user(self, *a, **kw):
        c.obj = api.user.get(c.real_user, c.user, request.params.get('eid'))
        c.title = 'User %s:%s' % (c.obj.id, c.obj.username)
        
        """
        id               | integer                     | not null default nextval('users_id_seq'::regclass)
        is_active        | boolean                     | not null
        default_timezone | character varying(40)       | not null
        last_login_date  | timestamp without time zone | 
        created_date     | timestamp without time zone | not null
        updated_date     | timestamp without time zone | not null
        """
        
        c.edit_url = h.api_url('user', 'edit', id=c.obj.id)
        """
        {
            'attr': name of field
            'value': if specified, will use instead of obj.attr
            'label': label in attr table. if not specified will use attr name
            'edit': type: True (uses the attr type), 'str', 'int', 'date', 'bool', ['list of selects']
            'format': the js formatter 'number', 'dollar', etc...
        }
        """
        c.attrs = [
            {'attr': 'username', 'edit' : True},
            {'attr': 'email'},
            {'attr': 'role', 'edit' : [users.ROLE_ENGINEER, users.ROLE_ADMIN, users.ROLE_USER]},
            {'attr': 'is_active', 'edit' : True},
            {'attr': 'first_name', 'edit' : True},
            {'attr': 'created_date'},
            {'attr': 'last_name', 'edit' : True},
            {'attr': 'updated_date'},
            {'attr': 'default_timezone', 'label': 'Timezone'},
            {'attr': 'last_login_date'},
        ]
        
        c.user_orgs = c.obj.get_organization_users(status=None)
        
        return self.render('/admin/inspect/user.html')
    
    def organization(self, *a, **kw):
        
        c.obj = api.organization.get(request.params.get('eid'))
        c.title = 'Org %s:%s' % (c.obj.id, c.obj.name)
        
        c.edit_url = h.api_url('organization', 'edit', id=c.obj.id)
        """
        {
            'attr': name of field
            'value': if specified, will use instead of obj.attr
            'label': label in attr table. if not specified will use attr name
            'edit': type: True (uses the attr type), 'str', 'int', 'date', 'bool', ['list of selects']
            'format': the js formatter 'number', 'dollar', etc...
        }
        """
        c.attrs = [
            {'attr': 'name', 'edit' : True},
            {'attr': 'creator'},
            {'attr': 'subdomain', 'edit' : True},
            {'attr': 'is_active', 'edit' : True},
            
            {'attr': 'created_date'}
        ]
        
        c.org_users = api.organization.get_users(c.real_user, c.user, c.obj)
        
        return self.render('/admin/inspect/organization.html')