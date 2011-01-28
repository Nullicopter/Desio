
from desio.lib.base import BaseController, h, c, auth, abort, redirect
from desio.model import users, projects, fixture_helpers as fh, STATUS_APPROVED
class UtilsController(BaseController):

    def load_basic_data(self):
        pw = u'password'
        admin = fh.create_user(username=u'admin', email=u'admin@admin.com', password=pw)
        org = fh.create_organization(user=admin, name=u'Mudhut Software', subdomain='mudhut')
        
        jim = fh.create_user(username=u'jim@reynolds.com', email=u'jim@reynolds.com', password=pw)
        kyle = fh.create_user(username=u'kyle@pants.com', email=u'kyle@pants.com', password=pw)
        joe = fh.create_user(username=u'joe@doe.com', email=u'joe@doe.com', password=pw)
        jethro = fh.create_user(username=u'jethro@walrustitty.com', email=u'jethro@walrustitty.com', password=pw)
        creator = fh.create_user(username=u'creator@creator.com', email=u'creator@creator.com', password=pw)
        unapproved = fh.create_user(username=u'jack@unloved.com', email=u'jack@unloved.com', password=pw)
        self.flush()
        
        org.attach_user(creator, role=users.ORGANIZATION_ROLE_CREATOR, status=STATUS_APPROVED)
        for u in [jim, kyle, joe, jethro]:
            org.attach_user(u, status=STATUS_APPROVED)
        org.attach_user(unapproved)
        
        self.flush()
        
        p1 = fh.create_project(user=creator, organization=org, name='Some Magic App')
        p2 = fh.create_project(user=admin, organization=org, name='Shopping Cart')
        p3 = fh.create_project(user=admin, organization=org, name='Desio')
        
        self.flush()
        
        p1.attach_user(jim, projects.PROJECT_ROLE_READ);
        p1.attach_user(kyle, projects.PROJECT_ROLE_WRITE);
        p1.attach_user(joe, projects.PROJECT_ROLE_ADMIN);
        
        p1.attach_user(jim, projects.PROJECT_ROLE_ADMIN);
        p1.attach_user(jethro, projects.PROJECT_ROLE_WRITE);
        
        self.commit()
        