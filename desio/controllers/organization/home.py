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
        return self.render('/organization/home.html')