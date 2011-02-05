from datetime import date, timedelta

from desio.model import fixture_helpers as fh
from desio.model import projects as p, STATUS_APPROVED, STATUS_PENDING, STATUS_COMPLETED, STATUS_OPEN, STATUS_INACTIVE
from desio.model.projects import PROJECT_ROLE_READ, PROJECT_ROLE_WRITE, PROJECT_ROLE_ADMIN
from desio.tests import *
from desio.utils import image

from pylons_common.lib.exceptions import *
import os.path

class TestProjects(TestController):
    def test_project_creation(self):
        """
        Test that you can create a project.
        """
        normal = fh.create_user()
        org = fh.create_organization(subdomain=u'one')
        orguser = org.attach_user(normal)
        self.flush()

        project = p.Project(name=u"foobar",
                            creator=normal,
                            description=u"descripsion",
                            organization=org)
        Session.add(project)
        self.flush()

        assert project.status == STATUS_APPROVED
        assert project.created_date
        assert project.name == u"foobar"
        assert project.description == u"descripsion"
        assert project.id
        assert project.eid
        assert project.organization == org


    def test_simple_project_methods(self):
        """
        Test the Project interface
        """
        user = fh.create_user()
        project = fh.create_project(user=user, name=u"helloooo")
        current = project.last_modified_date
        assert current
        project.update_activity()
        assert project.last_modified_date > current

        assert project.get_entities(u"/") == []
        assert project.get_file(u"/foobrar") == None
        assert project.get_changes(u"/blah") == []

        try:
            project.get_file(u"/")
        except AppException, e:
            assert e.msg.startswith("Only one complete path is supported")

        current = project.last_modified_date
        project.deactivate()
        self.flush()
        assert project.status == STATUS_INACTIVE
        assert project.name == "%s-%s" % (project.eid, u"helloooo")
        assert project.last_modified_date > current
        
    def test_changesets(self):
        """
        Test basic changeset functionality
        """
        user = fh.create_user()
        project = fh.create_project(user=user, name=u"helloooo")
        self.flush()

        filepath = file_path('ffcc00.gif')
        change = project.add_change(user, u"/foobar.gif", filepath, u"this is a new change")
        self.flush()

        assert project.get_changes(u"/foobar.gif") == [change]
        assert change.url and change.diff_url and change.thumbnail_url

        filepath = file_path('ffcc00.gif')
        change2 = project.add_change(user, u"/foobar.gif", filepath, u"this is a new new change")
        self.flush()

        assert project.get_changes(u"/foobar.gif") == [change2, change]

    def test_extracts(self):
        """
        Test basic changeset functionality
        """
        user = fh.create_user()
        project = fh.create_project(user=user, name=u"helloooo")
        self.flush()

        filepath = file_path('headphones.eps')
        change = project.add_change(user, u"/headphones.eps", filepath, u"this is a new change")
        self.flush()
        Session.refresh(change)
        
        extracts = change.change_extracts
        
        assert len(extracts) == 2
        foundthumb = False
        for e in extracts:
            if e.extract_type == image.EXTRACT_TYPE_THUMBNAIL:
                foundthumb = True
                assert e.url == change.thumbnail_url
            else:
                assert e.extract_type == image.EXTRACT_TYPE_FULL
            
            assert e.url
            assert e.order_index == 0
        assert foundthumb
    
    def test_membership(self):
        """
        Test user connection BS
        """
        org_owner = fh.create_user()
        owner = fh.create_user()
        rando_no_org = fh.create_user()
        rando = fh.create_user()
        read = fh.create_user()
        write = fh.create_user()
        admin = fh.create_user()
        org = fh.create_organization(user=org_owner)
        project = fh.create_project(user=owner, organization=org, name=u"helloooo")
        
        # this means anyone in the org has minimum read privileges
        org.is_read_open = True
        
        org.attach_user(rando_no_org, status=STATUS_PENDING)
        for u in [owner, rando, read, write, admin]:
            org.attach_user(u, status=STATUS_APPROVED)
        self.flush();
        
        """
        Testing: 
        def get_role(self, user, status=STATUS_APPROVED)
        def set_role(self, user, role)
        def get_project_user(self, user, status=None)
        def get_project_users(self, status=None)
        def attach_user(self, user, role=PROJECT_ROLE_READ, status=STATUS_APPROVED)
        def remove_user(self, user)
        """
        
        #this guy is not on the user, but he is an admin!
        assert project.get_role(org_owner) == PROJECT_ROLE_ADMIN
        
        assert project.creator == owner
        assert project.get_role(owner) == PROJECT_ROLE_ADMIN
        
        assert project.get_role(rando_no_org) == None
        assert project.get_role(rando) == PROJECT_ROLE_READ
        
        #test attach
        pu = project.attach_user(write, PROJECT_ROLE_WRITE)
        self.flush()
        assert pu.role == PROJECT_ROLE_WRITE
        assert pu.project == project
        assert pu.user == write
        assert pu.status == STATUS_APPROVED
        assert project.get_role(write) == PROJECT_ROLE_WRITE
        assert project.get_project_user(write).role == PROJECT_ROLE_WRITE
        
        #test set role
        project.attach_user(admin, PROJECT_ROLE_WRITE)
        self.flush()
        assert project.set_role(admin, PROJECT_ROLE_ADMIN)
        self.flush()
        assert project.get_role(admin) == PROJECT_ROLE_ADMIN
        
        #test get project users
        pus = project.get_project_users(status=STATUS_APPROVED)
        assert len(pus) == 3 #owner, write, admin
        
        #test is_read_open == false
        org.is_read_open = False
        self.flush()
        assert project.get_role(read) == None
        project.attach_user(read, PROJECT_ROLE_READ)
        self.flush()
        assert project.get_role(read) == PROJECT_ROLE_READ
        
        #test remove
        assert project.remove_user(read)
        self.flush()
        
        assert project.get_role(read) == None
        
        #test fail
        assert project.remove_user(rando) == False
        assert project.set_role(rando, PROJECT_ROLE_READ) == False
