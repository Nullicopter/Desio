from datetime import date, timedelta

from desio.model import users
from desio.tests import *
from desio.lib import helpers as h
import desio.model.fixture_helpers as fh

class TestIndexController(TestController):
    
    def test_index(self):
        u = fh.create_user()
        
        r = self.get('/', status=200)
        
        self.login(u)
        r = self.get('/', status=200)
        
        org = fh.create_organization(user=u)
        self.flush()
        
        #one org; redir to the org home page
        r = self.get('/', status=302)
        assert org.subdomain in r
        
        org2 = fh.create_organization(user=u)
        self.flush()
        
        #one org; redir to the org home page
        r = self.get('/', status=200)
        assert 'org-'+org.subdomain not in r
        assert 'org-'+org2.subdomain not in r
        