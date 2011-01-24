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

        p = {'name': u' Hella Project! ye$ah   man_',
             'description': u'No description for HellaProject'}
        project = api.project.create(u, u, org, **p)
        self.flush()
        assert project.eid
        assert project.slug == 'hella-project-ye-ah-man'
        assert project.status == STATUS_APPROVED
        assert project.name == p['name']
        assert project.description == p['description']
        assert project.created_date
        assert project.last_modified_date
        assert project.organization == org

        fetched_p = api.project.get(u, u, org)
        assert fetched_p == [project]

        fetched_p = api.project.get(u, u, org, project.eid)
        assert fetched_p == project
        
        fetched_p = api.project.get(u, u, org, project.slug)
        assert fetched_p == project

        org1 = fh.create_organization()
        assert self.throws_exception(lambda : api.project.get(u, u, org1)).code == FORBIDDEN
        assert self.throws_exception(lambda : api.project.get(u, u, org1, u'fakeeid')).code == FORBIDDEN
        assert self.throws_exception(lambda : api.project.get(u, u, org, u'fakeeid')).code == NOT_FOUND

        err = self.throws_exception(lambda : api.project.create(u, u, org, **p))
        assert 'A project with this name already exists. Please choose another' in err.msg
        
        p['name'] = u'Hella Project! ye$ah   man'
        project = api.project.create(u, u, org, **p)
        self.flush()
        assert project.slug == 'hella-project-ye-ah-man1'
