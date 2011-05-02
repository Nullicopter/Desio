from datetime import date, timedelta

from desio.model import fixture_helpers as fh, activity
from desio.model import projects as p, STATUS_APPROVED, STATUS_PENDING, STATUS_COMPLETED, STATUS_OPEN, STATUS_INACTIVE, STATUS_REMOVED
from desio.model.projects import APP_ROLE_READ, APP_ROLE_WRITE, APP_ROLE_ADMIN
from desio.tests import *
from desio.utils import image

from pylons_common.lib.exceptions import *
import os.path

class TestActivity(TestController):
    def test_project_creation(self):
        
        normal = fh.create_user()
        u2 = fh.create_user()
        org = fh.create_organization(subdomain=u'one')
        orguser = org.attach_user(normal)
        orguser = org.attach_user(u2)
        self.flush()

        project = p.Project(name=u"foobar",
                            creator=normal,
                            description=u"description",
                            organization=org)
        Session.add(project)
        self.flush()
        
        project2 = p.Project(name=u"meh",
                            creator=u2,
                            description=u"description",
                            organization=org)
        Session.add(project2)
        self.flush()
        
        act = activity.get_activities(organization=org)
        
        assert len(act) == 2
        assert act[0].type == activity.NewProject.TYPE
        assert act[0].project == project2
        assert act[0].get_message()
        assert act[1].type == activity.NewProject.TYPE
        assert act[1].project == project
        assert act[1].get_message()
        
        act = activity.get_activities(project=project)
        assert len(act) == 1
        assert act[0].type == activity.NewProject.TYPE
        assert act[0].project == project
        assert act[0].get_message()
        
        act = activity.get_activities(user=normal)
        assert len(act) == 1
        assert act[0].type == activity.NewProject.TYPE
        assert act[0].project == project
        assert act[0].get_message()
    
    def test_project_add_change(self):
        
        u = fh.create_user()
        org = fh.create_organization(subdomain=u'one')
        orguser = org.attach_user(u)
        self.flush()

        project = p.Project(name=u"foobar",
                            creator=u,
                            description=u"description",
                            organization=org)
        Session.add(project)
        
        filepath = file_path('ffcc00.gif')
        change = project.add_change(u, u"/main/project/arnold/foobar.gif", filepath, u"this is a new change")
        self.flush()
        
        act = activity.get_activities(organization=org)
        assert len(act) == 2
        assert act[0].type == activity.NewFile.TYPE
        assert act[0].get_message()
        
        filepath = file_path('ffcc00.gif')
        change = project.add_change(u, u"/main/project/arnold/foobar.gif", filepath, u"this is a new change")
        self.flush()
        
        act = activity.get_activities(organization=org)
        assert len(act) == 3
        assert act[0].type == activity.NewVersion.TYPE
        assert act[0].get_message()
        
        comment = change.add_comment(u, "This is a comment")
        self.flush()
        
        reply = change.add_comment(u, "This is a reply", in_reply_to=comment)
        self.flush()
        
        act = activity.get_activities(organization=org)
        assert len(act) == 5
        assert act[0].type == activity.NewReply.TYPE
        assert act[0].get_message()
        assert act[1].type == activity.NewComment.TYPE
        assert act[1].get_message()
        
        comment.set_completion_status(u, STATUS_COMPLETED)
        self.flush()
        comment.set_completion_status(u, STATUS_OPEN)
        self.flush()
        
        act = activity.get_activities(organization=org)
        assert len(act) == 7
        assert act[0].type == activity.CommentComplete.TYPE
        assert 'uncompleted' in act[0].get_message()
        assert act[1].type == activity.CommentComplete.TYPE
        assert 'completed' in act[1].get_message()