from desio import api
from desio.lib.base import *
from desio.model import users, projects, activity, STATUS_APPROVED, STATUS_PENDING

import formencode
import formencode.validators as fv

import sqlalchemy as sa

class HomeController(OrganizationBaseController):
    """
    """
    
    def index(self):
        
        c.title = "All Projects"
        
        c.project_data = [(p, p.get_entities(only_type=projects.File.TYPE)[:3]) for p in c.projects]
        
        #sort by last time a file in the project was modified
        c.project_data.sort(lambda l, r: cmp(r[0].last_modified, l[0].last_modified))
        
        c.activity = activity.get_activities(organization=c.organization, limit=5)
        
        c.users = [cu for cu in c.organization.get_user_connections(status=None) if cu.status in (STATUS_APPROVED, STATUS_PENDING)]
        c.users.sort(key=lambda cu: cu.user.human_name)
        c.users = c.organization.get_invites(has_user=False) + c.users
        
        return self.render('/organization/home.html')