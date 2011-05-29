from desio import api
from desio.lib.base import *
from desio.model import users, STATUS_APPROVED, STATUS_REJECTED, STATUS_PENDING
from desio.api import authorize

import formencode
import formencode.validators as fv

import sqlalchemy as sa

class SettingsController(OrganizationBaseController):
    """
    Organization settings like user's, org name, subdomain, etc
    """
    def __before__(self, **kw):
        super(SettingsController, self).__before__(**kw)
        
        c.projects = api.project.get(c.real_user, c.user, c.organization)
    
    def index(self, **kw):
        return self.users(**kw)
    
    @authorize(CanAdminOrgRedirect())
    def general(self, **kw):
        c.tab = 'Organization'
        c.title = '%s Organization Settings' % c.organization.name
        
        c.invites = Session.query(users.Invite).filter_by(object_id=c.organization.id, type=users.INVITE_TYPE_ORGANIZATION, status=STATUS_PENDING).all()
        c.users = api.organization.get_users(c.real_user, c.user, c.organization, ','.join([STATUS_APPROVED, STATUS_PENDING]))
        
        return self.render('/organization/settings/general.html')