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
        
        assert len(project.organization.get_projects(user)) == 1
        
        project.deactivate(user)
        self.flush()
        assert project.status == STATUS_INACTIVE
        assert project.name == "%s-%s" % (project.eid, u"helloooo")
        assert project.last_modified_date > current
        assert project.last_modified == project.last_modified_date
        self.flush()
        
        assert len(project.organization.get_projects(user)) == 0
        
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
    
    def test_interested_users_project(self):
        """
        Test basic changes functionality
        """
        user = fh.create_user()
        user2 = fh.create_user()
        user3 = fh.create_user()
        user4 = fh.create_user()
        project = fh.create_project(user=user, name=u"helloooo")
        self.flush()
        
        project.organization.attach_user(user2)
        project.organization.attach_user(user3)
        project.organization.attach_user(user4)
        self.flush()
        
        #user created it
        users = project.interested_users
        assert user3 not in users
        assert user2 not in users
        assert user in users
        
        #attach user2
        project.attach_user(user2)
        self.flush()
        
        users = project.interested_users
        assert user3 not in users
        assert user2 in users
        assert user in users

        filepath = file_path('ffcc00.gif')
        change = project.add_change(user3, u"/foobar.gif", filepath, u"this is a new change")
        self.flush()
        
        #user3 added a file
        
        users = project.interested_users
        assert user4 not in users
        assert user3 in users
        assert user2 in users
        assert user in users
        
        comment = change.add_comment(user4, u'foobar')
        self.flush()
        
        #user 4 commented, but that doesnt mean he is interested in the project
        users = project.interested_users
        assert user4 not in users
        assert user3 in users
        assert user2 in users
        assert user in users
    
    def test_interested_users_file(self):
        """
        Test basic changes functionality
        """
        user = fh.create_user()
        user2 = fh.create_user()
        user3 = fh.create_user()
        user4 = fh.create_user()
        project = fh.create_project(user=user, name=u"helloooo")
        self.flush()
        
        project.organization.attach_user(user2)
        project.organization.attach_user(user3)
        project.organization.attach_user(user4)
        self.flush()
        
        filepath = file_path('ffcc00.gif')
        change = project.add_change(user4, u"/foobar.gif", filepath, u"this is a new change")
        self.flush()
        file = change.entity
        
        #user created it
        users = file.interested_users
        assert user4 in users
        assert user3 not in users
        assert user2 not in users
        assert user not in users
        
        #attach user3
        file.attach_user(user3)
        self.flush()
        
        users = file.interested_users
        assert user4 in users
        assert user3 in users
        assert user2 not in users
        assert user not in users

        
        
        #user2 added a comment
        comment = change.add_comment(user2, u'foobar')
        self.flush()
        
        users = file.interested_users
        assert user4 in users
        assert user3 in users
        assert user2 in users
        assert user not in users
        
        #user 2 interested in his own comment
        users = comment.interested_users
        assert user4 not in users
        assert user3 not in users
        assert user2 in users
        assert user not in users
        
        #user added a reply
        reply = change.add_comment(user, u'foobar', in_reply_to=comment)
        self.flush()
        
        users = file.interested_users
        assert user4 in users
        assert user3 in users
        assert user2 in users
        assert user in users
        
        print user, user2, user3, user4
        
        users = comment.interested_users
        assert user4 not in users
        assert user3 not in users
        assert user2 in users
        assert user in users

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
        assert change.parse_status == image.PARSE_STATUS_COMPLETED
        assert change.parse_type == image.PARSE_TYPE_IMAGEMAGICK

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
        
        
        #makesure a fireworks png gets the right parse status and type
        filepath = file_path('cs5.png')
        change = project.add_change(user, u"/cs5.png", filepath, u"this is a new change")
        self.flush()
        assert change.version == 1
        assert change.parse_status == image.PARSE_STATUS_PENDING
        assert change.parse_type == image.PARSE_TYPE_FIREWORKS_CS5
        
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
        Test user connection BS, everyone is in the org
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
    
    def test_membership_complex(self):
        
        org_owner = fh.create_user()
        owner = fh.create_user()
        
        u = [fh.create_user() for i in range(5)]
        
        org = fh.create_organization(user=org_owner)
        org.attach_user(owner, status=STATUS_APPROVED)
        
        project1 = fh.create_project(user=org_owner, organization=org, name=u"helloooo")
        project2 = fh.create_project(user=org_owner, organization=org, name=u"jioasdjio")
        
        change1 = project1.add_change(org_owner, u"/main/project/arnold/foobar.gif", file_path('ffcc00.gif'), u"this is a new change")
        change2 = project1.add_change(owner, u"/main/project/arnold/foobarblah.gif", file_path('ffcc00.gif'), u"this is a new change 2")
        change3 = project2.add_change(owner, u"/main/project/arnold/meh.gif", file_path('ffcc00.gif'), u"this is a new change 3")
        
        file1, file2, file3 = change1.entity, change2.entity, change3.entity
        
        # this means anyone in the org has minimum read privileges
        org.is_read_open = True
        
        self.flush()
        
        assert org.get_role(u[0]) == None
        assert project1.get_role(u[0]) == None
        assert file1.get_role(u[0]) == None
        
        # only org_owner and owner are in the org. Everyone else is an invite.
        
        # attach to project read
        project1.attach_user(u[0], APP_ROLE_READ)
        self.flush()
        
        assert org.get_role(u[0]) == None
        assert project1.get_role(u[0]) == APP_ROLE_READ
        assert project2.get_role(u[0]) == None
        assert file1.get_role(u[0]) == APP_ROLE_READ
        assert file2.get_role(u[0]) == APP_ROLE_READ
        assert file3.get_role(u[0]) == None
        
        # attach to file 
        file1.attach_user(u[1], APP_ROLE_WRITE)
        self.flush()
        
        assert org.get_role(u[1]) == None
        assert project1.get_role(u[1]) == None
        assert project2.get_role(u[1]) == None
        assert file1.get_role(u[1]) == APP_ROLE_WRITE
        assert file2.get_role(u[1]) == None
        assert file3.get_role(u[1]) == None
        
        # attach to file write, project read
        project1.attach_user(u[2], APP_ROLE_READ)
        file1.attach_user(u[2], APP_ROLE_WRITE)
        self.flush()
        
        assert org.get_role(u[2]) == None
        assert project1.get_role(u[2]) == APP_ROLE_READ
        assert project2.get_role(u[2]) == None
        assert file1.get_role(u[2]) == APP_ROLE_WRITE
        assert file2.get_role(u[2]) == APP_ROLE_READ
        assert file3.get_role(u[2]) == None
        
        # attach to file read, project write, org admin
        org.attach_user(u[2], APP_ROLE_READ, status=STATUS_APPROVED)
        self.flush()
        
        assert org.get_role(u[2]) == APP_ROLE_READ
        assert project1.get_role(u[2]) == APP_ROLE_READ
        assert project2.get_role(u[2]) == APP_ROLE_READ
        assert file1.get_role(u[2]) == APP_ROLE_WRITE
        assert file2.get_role(u[2]) == APP_ROLE_READ
        assert file3.get_role(u[2]) == APP_ROLE_READ
        
        # attach to file read, project write
        project1.attach_user(u[3], APP_ROLE_WRITE)
        file1.attach_user(u[3], APP_ROLE_READ)
        self.flush()
        
        assert org.get_role(u[3]) == None
        assert project1.get_role(u[3]) == APP_ROLE_WRITE
        assert project2.get_role(u[3]) == None
        assert file1.get_role(u[3]) == APP_ROLE_WRITE
        assert file2.get_role(u[3]) == APP_ROLE_WRITE
        assert file3.get_role(u[3]) == None
        
        # attach to file read, project write, org admin
        org.attach_user(u[3], APP_ROLE_ADMIN, status=STATUS_APPROVED)
        self.flush()
        
        assert org.get_role(u[3]) == APP_ROLE_ADMIN
        assert project1.get_role(u[3]) == APP_ROLE_ADMIN
        assert project2.get_role(u[3]) == APP_ROLE_ADMIN
        assert file1.get_role(u[3]) == APP_ROLE_ADMIN
        assert file2.get_role(u[3]) == APP_ROLE_ADMIN
        assert file3.get_role(u[3]) == APP_ROLE_ADMIN
        