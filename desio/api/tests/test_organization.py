from desio.api import authorize, enforce, FieldEditor, convert_date
from desio.model import fixture_helpers as fh, Session, users, STATUS_APPROVED
from desio import api
from desio.tests import *

from datetime import datetime, timedelta

import formencode
import formencode.validators as fv

from pylons_common.lib.exceptions import *

class TestOrganization(TestController):
    
    def test_create(self):
        u = fh.create_user()
        
        o = {
            'subdomain': u'mycompany',
            'name': u'My company',
            'url': u'http://heyman.com',
        }
        org = api.organization.create(u,u, **o)
        self.flush()
        assert org.subdomain == o['subdomain']
        assert org.name == o['name']
        assert org.url == o['url']
        assert org.is_active == True
        
        l = len(u.organization_users)
        assert l == 1
        orgu = u.organization_users[0]
        assert orgu.user_id == u.id
        assert orgu.organization_id == org.id
        assert orgu.role == users.ORGANIZATION_ROLE_ADMIN
        assert orgu.status == STATUS_APPROVED
        
        o = {
            'subdomain': u'mycompany2',
            'name': u'My company',
        }
        org = api.organization.create(u,u, **o)
        self.flush()
        assert org.name
        
        #same subdomain
        o = {
            'subdomain': u'mycompany2',
            'name': u'My company',
        }
        assert 'subdomain' in self.throws_exception(lambda: api.organization.create(u,u, **o)).error_dict
        
        #no user
        o = {
            'subdomain': u'mycompany7',
            'name': u'My company',
        }
        err = self.throws_exception(lambda: api.organization.create(None, None, o))
        assert err.code
    
    def test_is_unique(self):
        one = fh.create_organization(subdomain=u'one')
        two = fh.create_organization(subdomain=u'two')
        self.flush()
        
        assert not api.organization.is_unique('one')
        assert api.organization.is_unique('three')
        assert api.organization.is_unique('ab-c')
        
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
        
        assert eorg.id == org.id
        assert eorg.name == u'omgwow'
        assert eorg.is_active == True
        assert eorg.url == u'http://wowza.com'
        
        assert self.throws_exception(lambda: api.Organization.edit(rando, rando, org, name='m')).code == FORBIDDEN
        assert self.throws_exception(lambda: api.user.edit(a, a, None, first_name='s')).code == NOT_FOUND

