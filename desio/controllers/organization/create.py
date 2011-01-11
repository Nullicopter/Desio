from desio import api
from desio.lib.base import *
from desio.model import users

import formencode
import formencode.validators as fv

import sqlalchemy as sa

class CreateController(BaseController):
    """
    """
    
    @dispatch_on(POST='_do_create')
    def index(self):
        #stub
        pass
    
    @mixed_response('index')
    def _do_create(self, **kw):
        
        return {'url': url or '/'}