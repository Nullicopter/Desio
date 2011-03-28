
from desio.lib.base import BaseController, h, c, auth, abort, redirect
from desio.model import users, projects, fixture_helpers as fh, STATUS_APPROVED

from desio import api

import os.path, tempfile, shutil

p = os.path.dirname
datadir = os.path.join(p(p(p(__file__))), 'tests', 'test_data')
def file_path(f):
    #copy cause our shit moves files.
    p = os.path.join(datadir, f)
    _, name = tempfile.mkstemp()
    shutil.copyfile(p, name)
    return name

class UtilsController(BaseController):

    def load(self):
        pw = u'password'
        admin = fh.create_user(username=u'admin', email=u'admin@admin.com', password=pw, role=u'admin')
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
        
        p2.attach_user(jim, projects.PROJECT_ROLE_ADMIN);
        p2.attach_user(jethro, projects.PROJECT_ROLE_WRITE);
        
        self.flush()
        
        filepath = file_path('headphones.eps')
        change1 = p1.add_change(joe, u"/headphones.eps", filepath, u"My headphones file")
        
        filepath = file_path('headphones.eps')
        change2 = p1.add_change(kyle, u"/headphones.eps", filepath, u"My headphones file again")
        self.flush()
        
        extract1 = change1.change_extracts[0]
        extract2 = change2.change_extracts[0]
        print change2.change_extracts
        
        _, c1 = api.file.add_comment(admin, admin, 'This is on version one', extract=extract1.id, x=40, y=50, width=50, height=50)
        _, c1 = api.file.add_comment(kyle, kyle, 'I dont know what to do about that', extract=extract1.id, x=100, y=75, width=50, height=50)
        
        # have admin, kyle, jim and joe
        _, c1 = api.file.add_comment(admin, admin, 'I think we should put blue in here.', extract=extract2.id, x=40, y=50, width=50, height=50)
        _, c2 = api.file.add_comment(kyle, kyle, 'I dont like this thing', extract=extract2.id, x=200, y=300, width=50, height=50)
        _, c3 = api.file.add_comment(jim, jim, 'Yeah, I see what you\'re doing there!', extract=extract2.id, x=250, y=100, width=40, height=50)
        _, c4 = api.file.add_comment(joe, joe, 'This comment has no coordinates', extract=extract2.id)
        self.flush()
        
        api.file.add_comment(kyle, kyle, 'Nah, I like red better.', change=change2.eid, in_reply_to=c1.eid)
        api.file.add_comment(joe, joe, 'How about green?', change=change2.eid, in_reply_to=c1.eid)
        api.file.add_comment(kyle, kyle, 'My reply i asdio oiajsdoi oasod  asdj io oaisd io asod oasodj oajs doi jaiosdio aoisd oiasdio aiosd oijasdio aiodiojsddp  aosd!', change=change2.eid, in_reply_to=c2.eid)
        
        api.file.add_comment(jim, jim, 'But it has a reply', change=change2.eid, in_reply_to=c4.eid)
        
        self.commit()


