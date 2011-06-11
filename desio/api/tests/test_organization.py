from desio.api import authorize, enforce, FieldEditor, convert_date
from desio.model import fixture_helpers as fh, Session, users, STATUS_APPROVED, STATUS_PENDING
from desio.model.users import APP_ROLE_ADMIN, APP_ROLE_READ, APP_ROLE_WRITE 
from desio import api
from desio.tests import *

from datetime import datetime, timedelta

import formencode
import formencode.validators as fv

from pylons_common.lib.exceptions import *

class TestOrganization(TestController):
    
    def test_get(self):
        u, _ = fh.create_user(), fh.create_user()
        
        o = {
            'subdomain': u'mycompany',
            'company_name': u'My company',
            'url': u'http://heyman.com',
        }
        org1 = api.organization.create(u,u, **o)
        
        o = {
            'subdomain': u'meh',
            'company_name': u'WOWZA',
            'url': u'http://heyman.com',
        }
        org2 = api.organization.create(_,_, **o)
        self.flush()
        
        #test api
        orgs = api.organization.get(u,u);
        
        assert len(orgs) == 1
        assert orgs[0] == org1
        
        #test serialized
        self.login(u)
        response = self.client_async(api_url('organization', 'get'), {})
        assert len(response.results) == 1
        assert response.results[0].eid == org1.eid
        
        org2.attach_user(u, status=STATUS_APPROVED)
        self.flush()
        
        #test multiple
        orgs = api.organization.get(u,u);
        assert len(orgs) == 2
        orgs = set([o.eid for o in orgs])
        
        assert org1.eid in orgs
        assert org2.eid in orgs
        
        response = self.client_async(api_url('organization', 'get'), {})
        assert len(response.results) == 2
        
        #test grab single
        orgs = api.organization.get(u,u, organization=org1.eid);
        assert orgs.eid == org1.eid
        
        response = self.client_async(api_url('organization', 'get'), {'organization': org1.eid})
        assert response.results.eid == org1.eid
    
    def test_create(self):
        u = fh.create_user()
        
        o = {
            'subdomain': u'mycompany',
            'company_name': u'My company',
            'url': u'http://heyman.com',
        }
        org = api.organization.create(u,u, **o)
        self.flush()
        assert org.subdomain == o['subdomain']
        assert org.name == o['company_name']
        assert org.url == o['url']
        assert org.is_active == True
        
        l = len(u.organization_users)
        assert l == 1
        orgu = u.organization_users[0]
        assert orgu.user_id == u.id
        assert orgu.organization_id == org.id
        assert orgu.role == users.APP_ROLE_ADMIN
        assert orgu.status == STATUS_APPROVED
        
        o = {
            'subdomain': u'SomeCompany',
            'company_name': u'My company',
        }
        org = api.organization.create(u,u, **o)
        assert org.subdomain == 'somecompany'
        
        o = {
            'subdomain': u'mycompany2',
            'company_name': u'My company',
        }
        org = api.organization.create(u,u, **o)
        self.flush()
        assert org.name
        
        #same subdomain
        o = {
            'subdomain': u'mycompany2',
            'company_name': u'My company',
        }
        assert 'subdomain' in self.throws_exception(lambda: api.organization.create(u,u, **o)).error_dict
        
        #no user
        o = {
            'subdomain': u'mycompany7',
            'company_name': u'My company',
        }
        err = self.throws_exception(lambda: api.organization.create(None, None, o))
        assert err.code
    
    def test_is_unique(self):
        one = fh.create_organization(subdomain=u'one')
        two = fh.create_organization(subdomain=u'two')
        self.flush()
        
        assert self.throws_exception(lambda: api.organization.is_unique('one'))
        assert api.organization.is_unique('three')['is']
        assert api.organization.is_unique('ab-c')['is']
        
        err = self.throws_exception(lambda: api.organization.is_unique('_ []'))
        assert err.message
        err = self.throws_exception(lambda: api.organization.is_unique('-'))
        assert err.message
        err = self.throws_exception(lambda: api.organization.is_unique('-abc'))
        assert err.message
        err = self.throws_exception(lambda: api.organization.is_unique('abc-'))
        assert err.message
    
    def test_edit(self):
        rando = fh.create_user()
        u = fh.create_user()
        org = fh.create_organization(user=u)
        self.flush()
        
        eorg = api.organization.edit(u, u, org, name=u'omgwow', url=u'http://wowza.com', is_active=u'f')
        self.flush()
        
        assert eorg.id == org.id
        assert eorg.name == u'omgwow'
        assert eorg.is_active == True
        assert eorg.url == u'http://wowza.com'
        
        eorg = api.organization.edit(u, u, org, name=u'wowza!')
        self.flush()
        
        assert self.throws_exception(lambda: api.organization.edit(rando, rando, org, name='m')).code ==FORBIDDEN
        assert self.throws_exception(lambda: api.user.edit(u, u, None, first_name='s')).code == NOT_FOUND

    def test_attach_approve(self):
        
        user = fh.create_user()
        creator = fh.create_user()
        admin = fh.create_user()
        rando = fh.create_user()
        org = fh.create_organization(user=admin)
        self.flush()
        
        assert org.get_role(admin) == APP_ROLE_ADMIN
        
        #anyone can attach themselves, but unless admin, they will be user:pending
        assert api.organization.attach_user(user, user, org, user, role=APP_ROLE_ADMIN, status=STATUS_APPROVED)
        self.flush()
        assert org.get_role(user, status=STATUS_PENDING) == APP_ROLE_READ
        
        #approve
        assert api.organization.attachment_approval(admin, admin, org, user)
        self.flush()
        assert org.get_role(user) == APP_ROLE_READ
        
        #approve creator automatically cause I'M AN ADMIN, BITCH
        assert api.organization.attach_user(admin, admin, org, creator, role=APP_ROLE_WRITE, status=STATUS_APPROVED)
        self.flush()
        assert org.get_role(creator) == APP_ROLE_WRITE
        
        #creator tries to add rando. CANNOT
        assert api.organization.attach_user(creator, creator, org, rando, role=APP_ROLE_ADMIN, status=STATUS_APPROVED)
        self.flush()
        assert org.get_role(rando, status=STATUS_PENDING) == APP_ROLE_READ
        
        #everyone tries to approve, and all fail but admin's attempt
        assert self.throws_exception(lambda: api.organization.attachment_approval(user, user, org, rando)).code == FORBIDDEN
        self.flush()
        assert not org.get_role(rando)
        
        assert self.throws_exception(lambda: api.organization.attachment_approval(creator, creator, org, rando)).code == FORBIDDEN
        self.flush()
        assert not org.get_role(rando)
        
        assert api.organization.attachment_approval(admin, admin, org, rando)
        self.flush()
        assert org.get_role(rando) == APP_ROLE_READ
