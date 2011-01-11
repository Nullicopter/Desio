from desio import api
from desio.lib.base import *
from desio.model import users

import formencode
import formencode.validators as fv

import sqlalchemy as sa

class OrganizationBaseController(BaseController):
    """
    """
    def __before__(self, **kw):
        c.organization = api.organization.get(subdomain=kw.get('sub_domain'))