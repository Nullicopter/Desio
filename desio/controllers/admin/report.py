
from desio import api
from desio.utils import relative_date_str
from desio.lib.base import *
from desio.controllers.admin import AdminController

from desio.model import users, activity

import formencode
import formencode.validators as fv

NOT_REPORTS = ['flush', 'commit', 'rollback']
class ReportController(AdminController):
    
    def __before__(self, *a, **kw):
        c.tab = 'Reports'
        auth.get_user()
        auth.get_real_user()
        
    def index(self, *a, **kw):
        c.title = 'Reports'
        
        root = ReportController
        modules = [getattr(root, name) for name in dir(root) if getattr(root, name).__doc__ and not name.startswith('_') and name not in NOT_REPORTS]
        c.modules = {}
        for m in modules:
            lines = m.__doc__.strip().split('\n')
            if len(lines) < 1: continue
            
            cat, name = lines[0].split(':')
            cat = cat.strip()
            name = name.strip()
            
            if cat not in c.modules:
                c.modules[cat] = []
            
            c.modules[cat].append((name, h.url_for(controller='admin/report', action=m.__name__)))
        
        return self.render('/admin/report/index.html')
    
    def organizations(self, *a, **kw):
        """
        General: Organizations
        
        A report that shows all of the orgs in the system
        """
        c.title = 'Organizations'
        
        orgs = Session.query(users.Organization).all()
        data = [(o, o.subdomain, o.creator, o.created_date, o.is_active) for o in orgs]
        
        c.params = {}
        c.params['table'] = {
            'columns': ['Organization', 'Subdomain', 'Creator', 'Created', 'Active'],
            'data': data
        }
        
        return self.render('/admin/report/generic.html')
    
    def users(self, *a, **kw):
        """
        General: Users
        
        A report that shows all of the orgs in the system
        """
        c.title = 'Users'
        
        us = Session.query(users.User).all()
        data = [(u, u.email, u.role, u.created_date, u.last_login_date, u.is_active) for u in us]
        
        c.params = {}
        c.params['table'] = {
            'columns': ['User', 'Email', 'Role', 'Created', 'Last Logged In', 'Active'],
            'data': data
        }
        
        return self.render('/admin/report/generic.html')
    
    def activity(self, *a, **kw):
        """
        General: Activity Feed
        
        A report showing all activity on the site.
        """
        c.title = 'Activity'
        
        act = activity.get_activities(limit=100) #last 100
        
        data = [(a.organization, relative_date_str(a.created_date), a.type, a.get_message(), a.user) for a in act]
        
        c.params = {}
        c.params['table'] = {
            'columns': ['Org', 'When', 'Type', 'Str', 'User'],
            'data': data
        }
        
        return self.render('/admin/report/generic.html')
    
    @dispatch_on(POST='_add_beta_email')
    def betaemails(self, *a, **kw):
        """
        General: Beta List Emails
        
        A report showing all the people who requested a beta invite
        """
        c.title = 'Beta Emails'
        
        us = Session.query(users.BetaEmail).all()
        data = [(u.eid, u.email, u.creator, u.created_date) for u in us]
        
        c.params = {}
        c.params['table'] = {
            'columns': ['eid', 'Email', 'Creator', 'Created'],
            'data': data
        }
        
        return self.render('/admin/report/betaemails.html')
    
    @mixed_response(sync_error_action='betaemails')
    def _add_beta_email(self, *a, **kw):
        
        class IForm(formencode.Schema):
            sid = formencode.All(fv.UnicodeString(not_empty=True))
            email = formencode.All(fv.Email(not_empty=True))
        
        sc = self.validate(IForm, **dict(request.params))
        be = users.BetaEmail.create(None, sc.email, creator=auth.get_real_user(), send_email=False)
        
        self.commit()
        
        return {'be': be and be.id or None}