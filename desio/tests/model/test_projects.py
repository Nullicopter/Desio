from datetime import date, timedelta

from desio.model import fixture_helpers as fh
from desio.model import projects as p, STATUS_APPROVED, STATUS_PENDING, STATUS_COMPLETED, STATUS_OPEN, STATUS_INACTIVE
from desio.model.projects import PROJECT_ROLE_READ, PROJECT_ROLE_WRITE, PROJECT_ROLE_ADMIN
from desio.tests import *

from pylons_common.lib.exceptions import *


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
                            creator=normal,
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

        assert project.get_changesets() == []
        assert project.get_changesets(1) == None
        assert project.get_changesets(5) == []

        current = project.last_modified_date
        changeset = project.add_changeset(user, u"foobar")
        self.flush()
        assert project.last_modified_date > current
        assert changeset

        assert changeset.order_index == 1
        assert changeset.user == user
        assert changeset.description == u"foobar"
        assert changeset.project == project
        assert changeset.status == STATUS_OPEN
        assert changeset.is_open

        assert project.get_changesets() == [changeset]
        assert project.get_changesets(1) == changeset
        assert project.get_changesets(5) == [changeset]

        assert self.throws_exception(lambda : project.add_changeset(user, u"blah")).code == FORBIDDEN
        assert self.throws_exception(lambda : project.add_changeset(user, u"blah")
                                     ).msg.startswith("Somebody is modifying project")
        current = project.last_modified_date
        changeset.complete()
        self.flush()
        assert project.last_modified_date > current
        assert changeset.status == STATUS_COMPLETED
        
        changeset2 = project.add_changeset(user, u"newone")
        self.flush()

        assert project.get_changesets() == [changeset2, changeset]
        assert project.get_changesets(1) == changeset2
        assert project.get_changesets(5) == [changeset2, changeset]

        assert changeset2.order_index - 1 == changeset.order_index


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
        changeset = project.add_changeset(user, u"foobar")
        self.flush()

        filepath = self.mktempfile("foobar.jpg", "helloooooo")
        change = changeset.add_change(u"/foobar.jpg", filepath, u"this is a new change in a changeset")
        self.flush()
    
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
