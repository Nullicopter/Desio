from datetime import date, timedelta

from desio.model import fixture_helpers as fh
from desio.model import projects as p, STATUS_APPROVED, STATUS_COMPLETED, STATUS_OPEN, STATUS_INACTIVE
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


    def test_project_methods(self):
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
        
