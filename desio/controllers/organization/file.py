import os.path
from paste.fileapp import FileApp
from desio import api
from desio.lib.base import *
from desio.lib import modules
from desio.model import users, projects, STATUS_APPROVED
from desio.api import authorize
from desio.controllers.api import v1

import formencode
import formencode.validators as fv

import sqlalchemy as sa

from pylons_common.lib.decorators import *

"""
This controller is special. It is for 'sharing' a file link. The user does not have to
be logged in or a user in the organization to view the file. All they will be able to do
is view the images, and the comments. No downloading, uploading, commenting, marking comments
as completed, etc.
"""

def has_entity():
    
    """
    
    """
    @stackable
    def decorator(fn):
        @zipargs(fn)
        def new(**kwargs):
            
            print kwargs
            kwargs['entity'] = c.entity = Session.query(projects.Entity).filter_by(eid=kwargs.get('id') or u'_NO_').first()
            
            return fn(**kwargs)
            
        return new
    return decorator

class FileController(BaseController):
    """
    """
    
    def __before__(self, **kw):
        #import pdb; pdb.set_trace()
        
        ru, u = (auth.get_real_user(), auth.get_user())
        
        c.organization = Session.query(users.Organization).filter_by(subdomain=kw.get('sub_domain')).first()
        
        if not c.organization:
            abort(404, 'org')
    
    @has_entity()
    @authorize(CanWriteEntityRedirect())
    def delete(self, id=None, entity=None, **kw):
        
        session['notify'] = '%s has been successfully deleted' % entity.name
        session.save()
        
        entity.delete()
        self.commit()
        
        self.redirect(h.url_for(controller='organization/project', action='view', slug=entity.project.slug))
        
    def view(self, project=None, file=None):
        """
        Anyone can view any file right now provided they know the url...
        """
        c.project = Session.query(projects.Project).filter_by(eid=project, organization=c.organization).first()
        if not c.project: abort(404)
        
        c.file = Session.query(projects.File).filter_by(eid=file, project=c.project, type=projects.File.type).first()
        if not c.file: abort(404)
        
        c.user_role = c.user and c.file.get_role(c.user) or None
        
        if c.user_role:
            url = h.url_for(controller='organization/project', slug=c.project.slug, action='view') + c.file.full_path
            redirect(url)
        
        c.sidepanel_tab = True
        c.title = c.file.name
        c.head_change = c.file.get_change()
        
        logger.info('viewing FILE %s' % (c.file))
        
        c.file_dict = v1.file.get().output([(c.file, c.head_change)])
        
        comments = c.head_change.get_comments()
        c.comments = v1.file.get_comments().output((c.head_change, comments))
        
        return self.render('/organization/project/view_file.html')
    