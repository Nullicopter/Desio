from desio.api import authorize, enforce, FieldEditor, convert_date
from desio.model import fixture_helpers as fh, Session, users, projects, STATUS_APPROVED, STATUS_PENDING, STATUS_OPEN
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
    
    def test_edit(self):
        p = fh.create_project()
        u = p.creator
        assert p
        assert p.name
        assert p.description
        
        fetched_p = api.project.edit(u, u, p.eid, name=u'my new name')
        assert fetched_p.id == p.id
        assert p.name == u'my new name'
        
        #same name as before!
        fetched_p = api.project.edit(u, u, p.eid, name=u'my new name')
        assert fetched_p.id == p.id
        assert p.name == u'my new name'
        
        fetched_p = api.project.edit(u, u, p.eid, description=u'new desc!!!')
        assert fetched_p.id == p.id
        assert p.description == u'new desc!!!'
    
    def test_get(self):
        org_owner = fh.create_user()
        rando_no_org = fh.create_user()
        owner = fh.create_user()
        rando = fh.create_user()
        read = fh.create_user()
        org = fh.create_organization(user=org_owner)
        project1 = fh.create_project(user=owner, organization=org, name=u"helloooo")
        project2 = fh.create_project(user=owner, organization=org, name=u"omgwow")
        project3 = fh.create_project(user=owner, organization=org, name=u"heyman")
        
        org.is_read_open = True
        
        for u in [owner, rando, read]:
            org.attach_user(u, status=STATUS_APPROVED)
        
        project1.attach_user(read)
        project2.attach_user(read)
        self.flush()
        
        assert len(api.project.get(owner, owner, org)) == 3
        assert len(api.project.get(read, read, org)) == 3
        assert self.throws_exception(lambda: len(api.project.get(rando_no_org, rando_no_org, org))).code == FORBIDDEN
        
        org.is_read_open = False
        self.flush();
        
        assert len(api.project.get(org_owner, org_owner, org)) == 3
        assert len(api.project.get(owner, owner, org)) == 3
        assert len(api.project.get(read, read, org)) == 2
        assert len(api.project.get(rando, rando, org)) == 0
        assert self.throws_exception(lambda: len(api.project.get(rando_no_org, rando_no_org, org))).code == FORBIDDEN
        
        self.flush();
    
    def test_get_structure(self):
        """
        """
        user = fh.create_user()
        project = fh.create_project(user=user, name=u"kadkoasdok")
        self.flush()

        filepath = file_path('ffcc00.gif')
        change = project.add_change(user, u"/foobar.gif", filepath, u"this is a new change")
        filepath = file_path('ffcc00.gif')
        change = project.add_change(user, u"/stuff/things.gif", filepath, u"this is a new change")
        filepath = file_path('ffcc00.gif')
        change = project.add_change(user, u"/stuff/cats/kitten.gif", filepath, u"this is a new change")
        filepath = file_path('headphones.eps')
        change = project.add_change(user, u"/stuff/headphones.eps", filepath, u"Mah headphones")
        self.flush()
        
        s = api.project.get_structure(user, user, project, '/')
        assert len(s) == 2
        assert s[0][0].name == ''
        assert s[0][0].path == '/'
        
        file, ch = s[0][1][0]
        assert file.name == 'foobar.gif'
        
        s = api.project.get_structure(user, user, project, '/stuff/')
        assert len(s) == 2
        
        s = api.project.get_structure(user, user, project, '/notthere/')
        assert s == None
    
    def test_membership(self):
        org_owner = fh.create_user()
        owner = fh.create_user()
        rando = fh.create_user()
        read = fh.create_user()
        write = fh.create_user()
        org = fh.create_organization(user=org_owner)
        project = fh.create_project(user=owner, organization=org, name=u"helloooo")
        
        org.is_read_open = False
        
        for u in [owner, rando, read, write]:
            org.attach_user(u, status=STATUS_APPROVED)
        self.flush();
        
        """
        def attach_user(real_user, user, project, u, role=users.ORGANIZATION_ROLE_USER)
        def remove_user(real_user, user, project, u)
        def set_user_role(real_user, user, project, u, role)
        def get_users(real_user, user, project, status=None)
        """
        
        assert api.project.attach_user(org_owner, org_owner, project, write, projects.PROJECT_ROLE_WRITE)
        self.flush()
        
        assert project.get_role(write) == projects.PROJECT_ROLE_WRITE
        
        assert api.project.set_user_role(owner, owner, project, write, projects.PROJECT_ROLE_ADMIN)
        self.flush()
        
        assert project.get_role(write) == projects.PROJECT_ROLE_ADMIN
        
        pus = api.project.get_users(org_owner, org_owner, project)
        assert len(pus) == 2
        
        assert api.project.remove_user(org_owner, org_owner, project, write)
        self.flush()
        
        assert project.get_role(write) == None
        
        #attach write again
        assert api.project.attach_user(org_owner, org_owner, project, write, projects.PROJECT_ROLE_WRITE)
        self.flush()
        
        ex = self.throws_exception(lambda: api.project.attach_user(write, write, project, read, projects.PROJECT_ROLE_READ))
        assert 'project' == ex.field
        ex = self.throws_exception(lambda: api.project.remove_user(read, read, project, write))
        assert 'project' == ex.field
        ex = self.throws_exception(lambda: api.project.set_user_role(read, read, project, write, projects.PROJECT_ROLE_READ))
        assert 'project' == ex.field
        
        ex = self.throws_exception(lambda: api.project.attach_user(owner, owner, project, None, projects.PROJECT_ROLE_READ))
        assert ex.code == NOT_FOUND
        ex = self.throws_exception(lambda: api.project.attach_user(owner, owner, None, read, projects.PROJECT_ROLE_READ))
        assert ex.code == NOT_FOUND
        ex = self.throws_exception(lambda: api.project.attach_user(owner, owner, project, read, None))
        assert 'role' in ex.error_dict