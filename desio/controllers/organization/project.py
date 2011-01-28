from desio import api
from desio.lib.base import *
from desio.model import users
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
            
            kwargs['project'] = api.project.get(c.real_user, c.user, c.organization, project=kwargs.get('slug'))
            
            return fn(**kwargs)
            
        return new
    return decorator

class ProjectController(OrganizationBaseController):
    """
    """
    
    @dispatch_on(POST='_create')
    @authorize(CanContributeToOrgRedirect())
    def new(self, **kw):
        c.title = 'New Project'
        return self.render('/organization/project/new.html')
    
    @mixed_response('register')
    def _create(self, **kw):
        
        project = api.project.create(c.real_user, c.user, c.organization, **dict(request.params))
        
        #TODO: get users from request; attach them to project
        
        self.commit()
        
        return {'url': h.url_for(controller='organization/project', action='view', slug=project.slug)}
    
    @has_project()
    @authorize(CanReadProjectRedirect())
    def view(self, slug=None, path=None, project=None, **kw):
        c.project = project
        
        c.title = c.project.name
        
        logger.info('viewing %s/%s' % (slug, path))
        
        return self.render('/organization/project/view.html')