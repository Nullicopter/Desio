from datetime import date, timedelta

from desio.model import users
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
        