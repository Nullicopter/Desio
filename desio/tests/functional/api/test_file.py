from datetime import date, timedelta

from desio.model import users, fixture_helpers as fh
from desio.tests import *
from desio import api

from pylons_common.lib.exceptions import *

class TestFile(TestController):
    
    def test_get(self):
        
        user = fh.create_user()
        project = fh.create_project(user=user, name=u"helloooo")
        self.flush()
        self.login(user)

        filepath = file_path('ffcc00.gif')
        change = project.add_change(user, u"/foobar.gif", filepath, u"this is a new change")
        self.flush()
        
        r = self.client_async(api_url('file', 'get', project=project.eid), {'path': u"/foobar.gif"})
        #print r.results
        
        assert r.results
        assert r.results.name
        assert r.results.eid
        assert r.results.version
        assert r.results.path
        assert r.results.extracts
    
    def test_comments(self):
        
        user = fh.create_user()
        project = fh.create_project(user=user, name=u"helloooo")
        self.flush()
        self.login(user)

        filepath = file_path('ffcc00.gif')
        change = project.add_change(user, u"/foobar.gif", filepath, u"this is a new change")
        self.flush()
        
        extract = change.change_extracts[0]
        
        _, c1 = api.file.add_comment(user, user, project.eid, 'My comment!', extract=extract.id, x=23, y=345, width=10, height=20)
        _, c2 = api.file.add_comment(user, user, project.eid, 'My comment 2!', extract=extract.id)
        _, c3 = api.file.add_comment(user, user, project.eid, 'My comment 3!', extract=extract.id, x=23, y=345, width=10, height=20)
        self.flush()
        
        _, r1 = api.file.add_comment(user, user, project.eid, 'My reply2!', change=change.eid, in_reply_to=c1.eid)
        _, r2 = api.file.add_comment(user, user, project.eid, 'My reply!', change=change.eid, in_reply_to=c2.eid)
        self.flush()
        
        r = self.client_async(api_url('file', 'get_comments', project=project.eid, change=change.eid), {})
        
        r = r.results
        assert r.comments
        assert len(r.comments) == 3
        
        assert r.comments[0].eid == c1.eid
        assert len(r.comments[0].replies) == 1
        assert r.comments[0].replies[0].eid == r1.eid
