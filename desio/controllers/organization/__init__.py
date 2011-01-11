from desio import api
from desio.lib.base import *
from desio.model import users

import formencode
import formencode.validators as fv

import sqlalchemy as sa

class OrganizationController(BaseController):
    """
    """
    def __before__(self, **kw):
        if kw.get('sub_domain'):
            c.organization = api.organization.get(subdomain=kw.get('sub_domain'))
    
    @dispatch_on(POST='_do_login')
    def login(self):
        c.title = 'Login!'
        
        if auth.is_logged_in():
            self.redirect('/')
        
        return self.render('/auth/login.html');
    
    @mixed_response('login')
    def _do_login(self, **kw):
        
        scrubbed = self.validate(LoginForm, **dict(request.params))
        
        url = auth.authenticate(**scrubbed)
        
        self.commit()
        return {'url': url or '/'}
    
    @dispatch_on(POST='_do_register')
    def register(self):
        c.title = 'Register'
        
        if auth.is_logged_in():
            self.redirect('/')
        
        return self.render('/auth/register.html');
    
    @mixed_response('register')
    def _do_register(self, **kw):
        
        user = api.user.create(**dict(request.params))
        
        self.commit()
        
        return {'url': auth.login(user) or '/'}
    
    def logout(self):
        auth.logout()
        
        return self.redirect('/')

