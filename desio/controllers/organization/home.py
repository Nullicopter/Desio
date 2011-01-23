from desio import api
from desio.lib.base import *
from desio.model import users

import formencode
import formencode.validators as fv

import sqlalchemy as sa

class HomeController(OrganizationBaseController):
    """
    """
    
    def index(self):
        c.projects = api.project.get(c.real_user, c.user, c.organization)
        
        return self.render('/organization/home.html')