from datetime import date, timedelta

from desio.model import users, fixture_helpers as fh, STATUS_PENDING, STATUS_APPROVED
from desio.tests import *
from desio import api

from desio.lib import auth

class TestInviteController(TestController):
    def test_create(self):
        """
        
        """
        
        u = fh.create_user()
        org = fh.create_organization(user=u, subdomain='cats', name='CATS!')
        project = fh.create_project(user=u, organization=org, name=u"helloooo")
        change = project.add_change(u, u"/main/project/arnold/foobar.gif", file_path('ffcc00.gif'), u"this is a new change")
        
        self.flush()
        
        #invite to entity
        invite = api.invite.create(u, u, 'opaskd@asd.com', entity=change.entity)
        self.flush()
        
        #the user doesnt exist, so we will show the register form
        response = self.get(url_for(controller='invite', action='index', id=invite.eid))
        assert 'invite_' + invite.eid in response
        assert 'confirm_password' in response
        assert 'register_user' in response
        
        response = self.client_async(url_for(controller='invite', action='index', id=invite.eid), {}, assert_success=False, status=400)
        
        #try to accept with a different user
        self.login(u)
        response = self.client_async(url_for(controller='invite', action='index', id=invite.eid), {
            'default_timezone': 0,
            'password': 'password',
            'confirm_password': 'password'
        }, assert_success=False, status=400)
        
        #shouldnt work
        Session.refresh(invite)
        assert invite.status == STATUS_PENDING
        assert not invite.invited_user_id
        
        self.logout()
        
        #accept the invite
        response = self.client_async(url_for(controller='invite', action='index', id=invite.eid), {
            'default_timezone': 0,
            'password': 'password',
            'confirm_password': 'password'
        })
        
        assert response.results.url
        
        Session.refresh(invite)
        assert invite.status == STATUS_APPROVED
        assert invite.invited_user
        
        self.logout()
        
        ##
        # invite him to the org
        ##
        
        invite = api.invite.create(u, u, 'opaskd@asd.com', organization=org)
        self.flush()
        
        assert invite.status == STATUS_PENDING
        assert invite.invited_user_id
        
        response = self.get(url_for(controller='invite', action='index', id=invite.eid))
        assert 'invite_' + invite.eid in response
        assert 'confirm_password' not in response
        assert 'login_user' in response
        
        #accept the invite
        response = self.client_async(url_for(controller='invite', action='index', id=invite.eid), {
            'password': 'password'
        })
        
        assert response.results.url == 'http://%s.dev.local:5001/' % org.subdomain
        
        Session.refresh(invite)
        assert invite.status == STATUS_APPROVED
        assert invite.invited_user
        
        response = self.get(url_for(controller='organization/home', action='index'), sub_domain=org.subdomain, status=200)
        assert 'user-logged-in' in response