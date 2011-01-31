from desio import api
from desio.lib.base import *
from desio.lib import modules
from desio.model import users, projects, STATUS_APPROVED
from desio.api import authorize

import formencode
import formencode.validators as fv

import sqlalchemy as sa

from pylons_common.lib.decorators import *

def has_project():
    
    """
    
    """
    @stackable
    def decorator(fn):
        @zipargs(fn)
        def new(**kwargs):
            
            kwargs['project'] = c.project = api.project.get(c.real_user, c.user, c.organization, project=kwargs.get('slug'))
            
            if c.project:
                c.project_role = c.project.get_role(c.user)
                c.is_project_admin = c.user_role in [projects.PROJECT_ROLE_ADMIN]
                c.is_project_writer = c.user_role in [projects.PROJECT_ROLE_ADMIN, projects.PROJECT_ROLE_WRITE]
                c.is_project_reader = c.project_role != None
            
            return fn(**kwargs)
            
        return new
    return decorator

class ProjectController(OrganizationBaseController):
    """
    """
    
    @authorize(CanContributeToOrgRedirect())
    def new(self, **kw):
        c.title = 'New Project'
        c.project_user_module_params = modules.project.project_user_module(c.real_user, c.user, c.organization)
        return self.render('/organization/project/new.html')
    
    @has_project()
    @authorize(CanReadProjectRedirect())
    def view(self, slug=None, path=None, project=None, **kw):
        c.title = project.name
        
        logger.info('viewing %s/%s' % (slug, path))
        
        return self.render('/organization/project/view.html')
    
    
    ##
    ### project settings (Should be separate controller...)
    ##
    
    def settings_index(self, **kw):
        return self.settings_general(**kw)
    
    @has_project()
    @authorize(CanContributeToOrgRedirect())
    def settings_users(self, project=None, **kw):
        c.tab = 'Users'
        c.title = project.name + ' Settings'
        c.project_user_module_params = modules.project.project_user_module(c.real_user, c.user, c.organization, project=project)
        return self.render('/organization/project/settings/users.html')
    
    @has_project()
    @authorize(CanContributeToOrgRedirect())
    def settings_general(self, project=None, **kw):
        c.tab = 'General'
        c.title = project.name + ' Settings'
        
        return self.render('/organization/project/settings/general.html')