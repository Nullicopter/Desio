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
    
    def index(self, **kw):
        return self.users(**kw)
    
    @authorize(CanEditOrgRedirect())
    def general(self, **kw):
        c.tab = 'General'
        c.title = 'General Settings'
        return self.render('/organization/settings/general.html')
    
    @authorize(CanEditOrgRedirect())
    def users(self, **kw):
        c.tab = 'Users'
        c.title = 'User Settings'
        c.users = api.organization.get_users(c.real_user, c.user, c.organization, ','.join([STATUS_APPROVED, STATUS_PENDING]))
        return self.render('/organization/settings/users.html')