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
        
        invite = api.invite.create(u, u, 'opaskd@asd.com', entity=change.entity)
        self.flush()
        
        response = self.get(url_for(controller='invite', action='index', id=invite.eid))
        assert 'invite_' + invite.eid in response
        
        response = self.client_async(url_for(controller='invite', action='index', id=invite.eid), {}, assert_success=False, status=400)
        
        self.login(u)
        response = self.client_async(url_for(controller='invite', action='index', id=invite.eid), {
            'default_timezone': 0,
            'password': 'password',
            'confirm_password': 'password'
        }, assert_success=False, status=400)
        
        Session.refresh(invite)
        assert invite.status == STATUS_PENDING
        assert not invite.invited_user_id
        
        self.logout()
        
        response = self.client_async(url_for(controller='invite', action='index', id=invite.eid), {
            'default_timezone': 0,
            'password': 'password',
            'confirm_password': 'password'
        })
        
        assert response.results.url
        print response.results.url
        
        Session.refresh(invite)
        assert invite.status == STATUS_APPROVED
        assert invite.invited_user

        response = self.get(response.results.url, sub_domain=org.subdomain)
        print response
        
        