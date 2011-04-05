from datetime import date, timedelta

from desio.model import users, fixture_helpers as fh
from desio.tests import *
from desio import api

from pylons_common.lib.exceptions import *

class TestCreate(TestController):
    
    def test_create(self):
        
        # test registering
        url = url_for(controller='organization/create', action='index')
        response = self.get(url)
        assert '="create"' in response

        username = u'test@example.com'
        subdomain = 'blah'
        post_vars = {
            'default_timezone' : u'-8',
            'password' : u'secret',
            'confirm_password' : u'secret',
            'email' : username,
            'name': 'Bob Jones',
            'subdomain': subdomain,
            'company_name': 'My Company',
        }
        
        response = self.client_async(url, post_vars)
        response = response.results.url
        assert response == 'http://blah.dev.local:5001'
        
        sent_mails = self.get_sent_mails()
        assert 1 == len(sent_mails)
        
        user = Session.query(users.User).filter_by(username=username).first()
        assert user
        
        response = self.get(url_for(controller='organization/home', action='index'), sub_domain=subdomain)
        assert username in response and 'user-logged-in' in response
        
        response = self.get(url_for(controller='auth', action='login'), status=302).follow()
        
        response = self.get(url_for(controller='auth', action='logout'), status=302).follow()
        assert username not in response and 'user-logged-in' not in response
        
        response = self.get(url_for(controller='auth', action='login'), status=200, sub_domain=subdomain)
        
        response = self.post(url_for(controller='auth', action='login'), {'username':username, 'password': 'secret'}, sub_domain=subdomain, status=302)
        
        response = self.get(url_for(controller='organization/home', action='index'), sub_domain=subdomain)
        assert username in response and 'user-logged-in' in response
        