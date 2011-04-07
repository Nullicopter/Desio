from datetime import date, timedelta

from desio import api
from desio.model import users, STATUS_PENDING
from desio.tests import *
from desio.lib import helpers as h
import desio.model.fixture_helpers as fh

class TestOrganizationHomeController(TestController):
    def test_base(self):
        u = fh.create_user()
        rando = fh.create_user()
        org = fh.create_organization(user=u)
        self.flush()
        
        url = h.get_domain(org.subdomain) + '/'
        
        #TODO: when login working check for user not logged in redir to subdomain login...
        #resp = self.get(url)
        
        self.login(rando)
        resp = self.follow(self.get(url, status=302, sub_domain=org.subdomain))
        
        assert 'org-'+org.subdomain not in resp
        
        self.login(u)
        resp = self.get(url, sub_domain=org.subdomain)
        
        assert 'org-'+org.subdomain in resp

class TestOrganizationAuthController(TestController):
    
    def test_register(self):
        u = fh.create_user()
        org = fh.create_organization(user=u)
        self.flush()
        
        post_vars = {'default_timezone' : u'-8', 'password' : u'secret', 'confirm_password' : u'secret', 'email' : 'bleh@omg.com', 'name': 'Jim Bob'}
        r = self.client_async('/register', post_vars, sub_domain=org.subdomain)
        assert r.results.url == '/'
        
        r = self.get('/', sub_domain=org.subdomain, status=302)
        assert '/pending' in r
        
        user = api.user.get(username='bleh@omg.com')
        
        orgu = org.get_user_connection(user)
        
        assert orgu
        assert orgu.status == STATUS_PENDING