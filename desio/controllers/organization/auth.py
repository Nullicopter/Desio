from desio import api
from desio.controllers.auth import AuthController as AuthBaseController
from desio.lib.base import *
from desio.model import users, STATUS_PENDING

import formencode
import formencode.validators as fv

import sqlalchemy as sa

class LoginForm(formencode.Schema):
    username = formencode.All(fv.UnicodeString(not_empty=True), fv.MaxLength(64))
    password = formencode.All(fv.UnicodeString(not_empty=True), fv.MaxLength(32))

class AuthController(AuthBaseController):
    """
    """
    def __before__(self, **kw):
        if kw.get('sub_domain'):
            try:
                c.organization = api.organization.get(subdomain=kw.get('sub_domain'))
            except ClientException, e:
                abort(404, 'No organization')
        if not c.organization:
            #todo, show some special message that says this org doesnt exist
            abort(404, 'No organization')
    
    @mixed_response('register')
    def _do_register(self, **kw):
        
        user = api.user.create(**dict(request.params))
        
        api.organization.attach_user(user, user, c.organization, user, role=users.ORGANIZATION_ROLE_USER, status=STATUS_PENDING)
        
        self.commit()
        
        return {'url': auth.login(user) or '/'}
    
    def pending(self, **kw):
        return self.render('/organization/auth/pending.html')

