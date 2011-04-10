from desio.api import authorize, enforce, FieldEditor, convert_date
from desio.model import fixture_helpers as fh, Session, users, APP_ROLE_READ, APP_ROLE_WRITE, STATUS_APPROVED, STATUS_REJECTED
from desio import api
from desio.tests import *

from datetime import datetime, timedelta

import formencode
import formencode.validators as fv

from pylons_common.lib.exceptions import *

class TestInvite(TestController):
    
    def test_all(self):
        
        a = fh.create_user(is_admin=True)
        org_owner = fh.create_user()
        inviteme = fh.create_user(email="rando@wowza.com")
        
        org = fh.create_organization(user=org_owner, subdomain='cats', name='CATS!')
        project = fh.create_project(user=org_owner, organization=org, name=u"helloooo")
        change = project.add_change(org_owner, u"/main/project/arnold/foobar.gif", file_path('ffcc00.gif'), u"this is a new change")
        file = change.entity
        self.flush()
        
        email = 'meow@cats.com'
        #invite user not in the system to file
        invite = api.invite.create(a, org_owner, email, entity=file)
        
        #based on email only
        assert self.throws_exception(lambda: api.invite.create(a, org_owner, email, entity=file)).code == err.DUPLICATE
        
        assert invite.role == APP_ROLE_READ
        assert invite.invited_user == None
        assert invite.user == org_owner
        assert invite.invited_email == email
        assert invite.object == file
        
        emails = self.get_sent_mails()
        assert len(emails) == 1
        
        assert api.invite.get(invite.eid) == invite
        
        #need to create a new user to accept
        u = fh.create_user(email=email, username=email)
        self.flush()
        
        api.invite.accept(u, u, invite.eid)
        self.flush()
        Session.refresh(invite)
        
        assert invite.invited_user == u
        assert invite.status == STATUS_APPROVED
        
        #invite user in system to proj
        invite = api.invite.create(org_owner, org_owner, email, project=project)
        
        assert invite.invited_user == u
        assert invite.invited_email == email
        assert invite.object == project
        
        emails = self.get_sent_mails()
        assert len(emails) == 2
        
        api.invite.reject(u, u, invite.eid)
        self.flush()
        Session.refresh(invite)
        
        assert invite.invited_user == u
        assert invite.status == STATUS_REJECTED
        
        #invite user in system to org
        invite = api.invite.create(org_owner, org_owner, email, organization=org, role=APP_ROLE_WRITE)
        
        assert invite.object == org
        
        emails = self.get_sent_mails()
        assert len(emails) == 3
        
        # FAIL
        
        #already invited
        assert self.throws_exception(lambda: api.invite.create(a, org_owner, email, entity=file)).code == err.DUPLICATE
        
        #no params
        ex = self.throws_exception(lambda: api.invite.create(org_owner, org_owner, email)).code
        assert ex# == err.NOT_FOUND
        
        #not in org at all
        assert self.throws_exception(lambda: api.invite.create(inviteme, inviteme, email, organization=org)).code == err.FORBIDDEN
        
        #in org as writer
        assert self.throws_exception(lambda: api.invite.create(u, u, email, entity=file)).code == err.FORBIDDEN
        
        #validation
        assert 'email' in self.throws_exception(lambda: api.invite.create(org_owner, org_owner, '', entity=file)).error_dict
        
        
        