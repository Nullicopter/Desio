from desio.api import authorize, enforce, FieldEditor, convert_date
from desio.model import fixture_helpers as fh, Session, users
from desio import api
from desio.tests import *

from datetime import datetime, timedelta

import formencode
import formencode.validators as fv

from pylons_common.lib.exceptions import *

class TestUser(TestController):
    
    def test_set_pref(self, admin=False):
        pass
    
    def test_create(self):
        u = {
            'email': u'omg@wowza.com',
            'password': u'concon',
            'confirm_password': u'concon',
            'default_timezone': -9,
        }
        user = api.user.create(**u)
        self.flush()
        
        def check_user(user, u):
            for k,v in u.items():
                if k not in ['confirm_password', 'password', 'default_timezone']:
                    assert getattr(user, k) == v
            assert user.default_timezone
            assert user.password
        
        check_user(user, u)
        assert user.username == u['email']
        
        u = {
            'email': u'omg@wowzaa.com',
            'username': u'heyman',
            'password': u'concon',
            'confirm_password': u'concon',
            'default_timezone': -9,
            'first_name': u'omg',
            'last_name': u'wowzaa'
        }
        user = api.user.create(**u)
        self.flush()
        check_user(user, u)
        
        #same email
        u = {
            'email': u'omg@wowza.com',
            'username': u'heyman',
            'password': u'concon',
            'confirm_password': u'concon',
            'default_timezone': -9
        }
        assert 'email' in self.throws_exception(lambda: api.user.create(**u)).error_dict
        
        #no password match
        u = {
            'email': u'omg@wowzaasd.com',
            'username': u'heyman',
            'password': u'conco',
            'confirm_password': u'concon',
            'default_timezone': u'-9'
        }
        err = self.throws_exception(lambda: api.user.create(**u)).error_dict
        assert 'confirm_password' in err
    
    def test_edit(self):
        own = fh.create_user()
        rando = fh.create_user()
        a = fh.create_user(is_admin=True)
        self.flush()
        
        u = api.user.edit(own, own, own, first_name='omgwow', default_timezone=0, is_active='f', role='admin')
        
        assert u.id == own.id
        assert u.first_name == 'omgwow'
        assert u.is_active == True
        assert u.role == 'user'
        assert 'London' in u.default_timezone or 'UTC' in u.default_timezone
        
        u = api.user.edit(a, a, own, last_name='yeah')
        assert u.id == own.id
        
        u = api.user.edit(a, a, own, is_active='f', role='admin')
        assert u.id == own.id
        assert u.is_active == False
        assert u.role == 'admin'
        
        assert self.throws_exception(lambda: api.user.edit(rando, rando, own, first_name='m')).code == NOT_FOUND
        assert self.throws_exception(lambda: api.user.edit(a, a, None, first_name='s')).code == NOT_FOUND   

