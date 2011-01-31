from datetime import date, timedelta

from desio.model import users, STATUS_APPROVED, STATUS_REJECTED, STATUS_PENDING, fixture_helpers as fh
from desio.model.users import ORGANIZATION_ROLE_ADMIN, ORGANIZATION_ROLE_USER, ORGANIZATION_ROLE_CREATOR 
from desio.tests import *

class TestOrganization(TestController):
    
    def test_attach(self):
        
        normal = fh.create_user()
        reject = fh.create_user()
        
        org = fh.create_organization(subdomain=u'one')
        self.flush()
        
        assert not org.get_organization_user(normal)
        assert not org.get_role(normal)
        
        #add twice to make sure that doesnt break
        orguser = org.attach_user(normal)
        self.flush()
        orguser = org.attach_user(normal)
        self.flush()
        assert orguser.status == STATUS_PENDING
        assert orguser.role == ORGANIZATION_ROLE_USER
        
        #add as rejected
        orguser = org.attach_user(reject, status=STATUS_REJECTED, role=ORGANIZATION_ROLE_ADMIN)
        self.flush()
        assert orguser.status == STATUS_REJECTED
        assert orguser.role == ORGANIZATION_ROLE_ADMIN
        
        #filtering works?
        assert org.get_organization_user(normal).status == STATUS_PENDING
        assert not org.get_organization_user(normal, status=STATUS_APPROVED)
        
        #make sure user is rejected
        assert org.get_organization_user(reject).status == STATUS_REJECTED
        assert org.get_role(reject) == None
        assert org.get_role(reject, status=STATUS_REJECTED) == ORGANIZATION_ROLE_ADMIN
        
        #make sure removal works
        orguser = org.remove_user(reject)
        self.flush()
        assert not org.get_organization_user(reject)
    
    def test_attach_n_approve(self):
        
        normal = fh.create_user()
        
        org = fh.create_organization(subdomain=u'one')
        self.flush()
        
        assert not org.get_organization_user(normal)
        assert not org.get_role(normal)
        
        #add twice to make sure that doesnt break
        orguser = org.attach_user(normal)
        self.flush()
        assert orguser.status == STATUS_PENDING
        assert orguser.role == ORGANIZATION_ROLE_USER
        assert org.get_role(normal) == None
        assert org.get_role(normal, status=STATUS_PENDING) == ORGANIZATION_ROLE_USER
        
        ou = org.approve_user(normal)
        assert ou
        self.flush()
        assert org.get_role(normal) == ORGANIZATION_ROLE_USER
        
        assert org.reject_user(normal)
        self.flush()
        assert org.get_role(normal) == None
        assert org.get_role(normal, status=STATUS_REJECTED) == ORGANIZATION_ROLE_USER
        