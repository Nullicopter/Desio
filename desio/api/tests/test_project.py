from desio.api import authorize, enforce, FieldEditor, convert_date
from desio.model import fixture_helpers as fh, Session, users, STATUS_APPROVED, STATUS_PENDING, STATUS_OPEN
from desio import api
from desio.tests import *

from datetime import datetime, timedelta

import formencode
import formencode.validators as fv

from pylons_common.lib.exceptions import *

class TestProject(TestController):
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

        p = {'name': u'HellaProject',
             'description': u'No description for HellaProject'}
        project = api.project.create(u, u, org, **p)
        self.flush()
        assert project.eid
        assert project.status == STATUS_OPEN
        assert project.name == p['name']
        assert project.description == p['description']
        assert project.created_date
        assert project.last_modified_date
        assert project.organization == org
