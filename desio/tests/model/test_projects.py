from datetime import date, timedelta

from desio.model import fixture_helpers as fh
from desio.model import projects as p, STATUS_APPROVED, STATUS_PENDING, STATUS_COMPLETED, STATUS_OPEN, STATUS_INACTIVE, STATUS_REMOVED
from desio.model.projects import APP_ROLE_READ, APP_ROLE_WRITE, APP_ROLE_ADMIN
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
        self.flush()

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
        assert project.last_modified == project.last_modified_date
        self.flush()
        
    def test_filetree_creation_and_navigation(self):
        """
        Test that on file creation the entire directory structure
        is created and can be browsed.
        """
        user = fh.create_user()
        project = fh.create_project(user=user, name=u"helloooo")
        self.flush()

        filepath = file_path('ffcc00.gif')
        change = project.add_change(user, u"/main/project/arnold/foobar.gif", filepath, u"this is a new change")
        self.flush()

        assert project.get_entities(u"/")[0].name == u"main"
        assert project.get_entities(u"/main/")[0].name == u"project"
        assert project.get_entities(u"/main/project/")[0].name == u"arnold"
        assert project.get_entities(u"/main/project/arnold/")[0].name == u"foobar.gif"
        assert project.get_entities(u"/main/project/arnold/foobar.gif").name == u"foobar.gif"
        entity = project.get_entities(u"/main/project/arnold/foobar.gif")
        entity.delete()
        self.flush()
        assert entity.status == STATUS_REMOVED
        assert entity.name == "%s-%s" % (entity.eid, entity.readable_name)
        assert project.get_entities(u"/main/project/arnold/foobar.gif") == None
        assert project.get_entities(u"/main/project/arnold/%s" % (entity.name), only_status=None).readable_name == u"foobar.gif"

        filepath = file_path('ffcc00.gif')
        change = project.add_change(user, u"/foobar2.gif", filepath, u"this is a new change")
        self.flush()

        for entity in project.get_entities(u'/'):
            assert entity.name # there can be no root.
            assert entity.path == u"/"

        assert project.get_entities(u'/')[0].name == 'foobar2.gif'
        assert project.get_entities(u'/', order_by_field='name')[0].name == 'main'
        assert project.get_entities(u'/', order_by_field='name', desc=False)[0].name == 'foobar2.gif'

        assert project.last_modified > project.last_modified_date
        self.flush()
        
    def test_changes(self):
        """
        Test basic changes functionality
        """
        user = fh.create_user()
        user2 = fh.create_user()
        project = fh.create_project(user=user, name=u"helloooo")
        self.flush()

        filepath = file_path('ffcc00.gif')
        change = project.add_change(user, u"/foobar.gif", filepath, u"this is a new change")
        self.flush()
        assert change.version == 1

        assert project.get_changes(u"/foobar.gif") == [change]
        assert change.url and change.diff_url and change.thumbnail_url

        filepath = file_path('ffcc00.gif')
        change2 = project.add_change(user, u"/foobar.gif", filepath, u"this is a new new change")
        self.flush()
        assert change2.version == 2

        assert project.get_changes(u"/foobar.gif") == [change2, change]


        comment = change.add_comment(user, u'foobar')
        comment1 = change.add_comment(user, u'foobar', 1, 2)
        comment2 = change.add_comment(user, u'foobar', 1, 2, 3, 4)
        comment3 = change.add_comment(user, u'foobar', 1, 2, 3, 4)
        comment3.delete()
        self.flush()
        assert change.get_comments() == [comment, comment1, comment2]
        
        comment_status = comment.completion_status
        assert comment_status
        assert comment_status.comment == comment
        assert comment_status.user == user
        assert comment_status.status == STATUS_OPEN
        assert comment_status.id
        
        cs = comment.set_completion_status(user2, STATUS_OPEN)
        self.flush()
        cs = comment.set_completion_status(user2, STATUS_COMPLETED)
        self.flush()
        cs = comment.set_completion_status(user2, STATUS_OPEN)
        self.flush()
        cs = comment.set_completion_status(user2, STATUS_COMPLETED)
        self.flush()
        assert cs
        assert cs.comment == comment
        assert cs.user == user2
        assert cs.status == STATUS_COMPLETED
        assert cs.id
        
        comment_status = comment.completion_status
        assert comment_status
        assert comment_status.comment == comment
        assert comment_status.user == user2
        assert comment_status.status == STATUS_COMPLETED
        assert comment_status.id
        
        num = change.get_number_comments(status=STATUS_COMPLETED)
        assert num == 1
        
        num = change.get_number_comments(status=STATUS_OPEN)
        assert num == 2
        self.flush()
        
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
                assert e.order_index == 0
            else:
                assert e.extract_type == image.EXTRACT_TYPE_FULL
                assert e.order_index == 0 or e.order_index == 1
            
            assert e.url
            
        assert foundthumb
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
        def get_user_connection(self, user, status=None)
        def get_user_connections(self, status=None)
        def attach_user(self, user, role=APP_ROLE_READ, status=STATUS_APPROVED)
        def remove_user(self, user)
        """
        
        #this guy is not on the user, but he is an admin!
        assert project.get_role(org_owner) == APP_ROLE_ADMIN
        
        assert project.creator == owner
        assert project.get_role(owner) == APP_ROLE_ADMIN
        
        assert project.get_role(rando_no_org) == None
        assert project.get_role(rando) == APP_ROLE_READ
        
        #test attach
        pu = project.attach_user(write, APP_ROLE_WRITE)
        self.flush()
        assert pu.role == APP_ROLE_WRITE
        assert pu.project == project
        assert pu.user == write
        assert pu.status == STATUS_APPROVED
        assert project.get_role(write) == APP_ROLE_WRITE
        assert project.get_user_connection(write).role == APP_ROLE_WRITE
        
        #test set role
        project.attach_user(admin, APP_ROLE_WRITE)
        self.flush()
        assert project.set_role(admin, APP_ROLE_ADMIN)
        self.flush()
        assert project.get_role(admin) == APP_ROLE_ADMIN
        
        #test get project users
        pus = project.get_user_connections(status=STATUS_APPROVED)
        assert len(pus) == 3 #owner, write, admin
        
        #test is_read_open == false
        org.is_read_open = False
        self.flush()
        assert project.get_role(read) == None
        project.attach_user(read, APP_ROLE_READ)
        self.flush()
        assert project.get_role(read) == APP_ROLE_READ
        
        #test remove
        assert project.remove_user(read)
        self.flush()
        
        assert project.get_role(read) == None
        
        #test fail
        assert project.remove_user(rando) == False
        assert project.set_role(rando, APP_ROLE_READ) == False
        self.flush()
