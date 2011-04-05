from desio.lib.base import *
from desio.model import users
from desio import api
from desio.api import IsNotLoggedIn, authorize
from desio.utils import email

import pylons

from pylons_common.lib.utils import extract

import formencode
import formencode.validators as fv

import sqlalchemy as sa

class CreateController(BaseController):
    """
    """
    
    @authorize(auth.RedirectOnFail(IsNotLoggedIn(), url='/'))
    def __before__(self, **k):
        pass
    
    @dispatch_on(POST='_do_create')
    def index(self):
        return self.render('/organization/create.html')
    
    @mixed_response('index')
    def _do_create(self, **kw):
        user_params = extract(request.params, 'name', 'email', 'password', 'confirm_password', 'default_timezone')
        user = api.user.create(**user_params)
        
        org_params = {
            'name': request.params.get('company_name'),
            'subdomain': request.params.get('subdomain')
        }
        org = api.organization.create(user, user, **org_params)
        
        self.commit()
        
        email.send(user, 'new_organization.txt', {
            'organization': org
        })
        
        return {'url': auth.login(user) or pylons.config.get('subdomain_url') % (org.subdomain)}
