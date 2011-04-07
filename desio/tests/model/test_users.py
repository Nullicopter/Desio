from datetime import date, timedelta

from desio.model import users, STATUS_APPROVED, STATUS_REJECTED, STATUS_PENDING, fixture_helpers as fh
from desio.model.users import APP_ROLE_ADMIN, APP_ROLE_READ, APP_ROLE_WRITE
from desio.tests import *

class TestOrganization(TestController):
    
    def test_attach(self):
        
        normal = fh.create_user()
        reject = fh.create_user()
        
        org = fh.create_organization(subdomain=u'one')
        self.flush()
        
        assert not org.get_user_connection(normal)
        assert not org.get_role(normal)
        
        #add twice to make sure that doesnt break
        orguser = org.attach_user(normal)
        self.flush()
        orguser = org.attach_user(normal)
        self.flush()
        assert orguser.status == STATUS_PENDING
        assert orguser.role == APP_ROLE_READ
        
        #add as rejected
        orguser = org.attach_user(reject, status=STATUS_REJECTED, role=APP_ROLE_ADMIN)
        self.flush()
        assert orguser.status == STATUS_REJECTED
        assert orguser.role == APP_ROLE_ADMIN
        
        #filtering works?
        assert org.get_user_connection(normal).status == STATUS_PENDING
        assert not org.get_user_connection(normal, status=STATUS_APPROVED)
        
        #make sure user is rejected
        assert org.get_user_connection(reject).status == STATUS_REJECTED
        assert org.get_role(reject) == None
        assert org.get_role(reject, status=STATUS_REJECTED) == APP_ROLE_ADMIN
        
        #make sure removal works
        orguser = org.remove_user(reject)
        self.flush()
        assert not org.get_user_connection(reject)
    
    def test_attach_n_approve(self):
        
        normal = fh.create_user()
        
        org = fh.create_organization(subdomain=u'one')
        self.flush()
        
        assert not org.get_user_connection(normal)
        assert not org.get_role(normal)
        
        #add twice to make sure that doesnt break
        orguser = org.attach_user(normal)
        self.flush()
        assert orguser.status == STATUS_PENDING
        assert orguser.role == APP_ROLE_READ
        assert org.get_role(normal) == None
        assert org.get_role(normal, status=STATUS_PENDING) == APP_ROLE_READ
        
        ou = org.approve_user(normal)
        assert ou
        self.flush()
        assert org.get_role(normal) == APP_ROLE_READ
        
        assert org.reject_user(normal)
        self.flush()
        assert org.get_role(normal) == None
        assert org.get_role(normal, status=STATUS_REJECTED) == APP_ROLE_READ
    
    def test_invite(self):
        t = (AppException,)
        
        uorg = fh.create_user()
        uproj = fh.create_user()
        ufile = fh.create_user()
        
        user = fh.create_user()
        project = fh.create_project(user=user, name=u"helloooo")
        self.flush()
        org = project.organization

        filepath = file_path('ffcc00.gif')
        change = project.add_change(user, u"/main/project/arnold/foobar.gif", filepath, u"this is a new change")
        entity = change.entity
        
        def fu(email):
            return Session.query(users.User).filter_by(email=email).first()
        
        #invite non-user to org
        email = 'orgu@blah.com'
        inv = users.Invite.create(user, email, org, users.APP_ROLE_WRITE)
        self.flush()
        
        assert inv.invited_email == email
        assert inv.invited_user == None
        assert inv.user == user
        assert inv.role == users.APP_ROLE_WRITE
        assert inv.type == users.INVITE_TYPE_ORGANIZATION
        assert inv.object_id == org.id
        assert inv.status == STATUS_PENDING
        
        assert inv.object == org
        
        assert self.throws_exception(lambda: inv.accept(), types=t).code == err.INVALID #no user
        assert self.throws_exception(lambda: inv.accept(uorg), types=t).code == err.INVALID #email no match
        
        iu = fh.create_user(username=email, email=email)
        self.flush()
        
        assert org.get_role(iu) == None
        
        inv.accept(iu)
        self.flush()
        Session.refresh(inv)
        
        assert inv.invited_email == email
        assert inv.invited_user == iu
        assert inv.user == user
        assert inv.type == users.INVITE_TYPE_ORGANIZATION
        assert inv.object_id == org.id
        assert inv.status == STATUS_APPROVED
        
        assert inv.object == org
        assert org.get_role(iu) == users.APP_ROLE_WRITE
        
        assert self.throws_exception(lambda: users.Invite.create(user, email, org, users.APP_ROLE_WRITE), types=t).code == err.DUPLICATE
        
        #invite non-user to project
        email = 'orgp@blah.com'
        inv = users.Invite.create(user, email, project, users.APP_ROLE_ADMIN)
        self.flush()
        
        assert inv.role == users.APP_ROLE_ADMIN
        assert inv.type == users.INVITE_TYPE_PROJECT
        assert inv.object_id == project.id
        assert inv.object == project
        
        iu = fh.create_user(username=email, email=email)
        self.flush()
        
        assert project.get_role(iu) == None
        
        inv.accept(iu)
        self.flush()
        Session.refresh(inv)
        
        assert inv.invited_user == iu
        assert project.get_role(iu) == users.APP_ROLE_ADMIN
        assert org.get_role(iu) == None
        
        #invite non-user to entity
        email = 'orgf@blah.com'
        inv = users.Invite.create(user, email, entity, users.APP_ROLE_READ)
        self.flush()
        
        assert inv.type == users.INVITE_TYPE_ENTITY
        assert inv.object_id == entity.id
        assert inv.object == entity
        
        iu = fh.create_user(username=email, email=email)
        self.flush()
        
        assert entity.get_role(iu) == None
        
        inv.accept(iu)
        self.flush()
        Session.refresh(inv)
        
        assert inv.invited_user == iu
        assert entity.get_role(iu) == users.APP_ROLE_READ
        assert org.get_role(iu) == None
        assert project.get_role(iu) == None
        