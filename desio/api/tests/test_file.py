from datetime import date, timedelta

from desio import api
from desio.model import users, fixture_helpers as fh
from desio.tests import *

from pylons_common.lib.exceptions import *

class TestFile(TestController):
    
    def test_get(self):
        
        user = fh.create_user()
        project = fh.create_project(user=user, name=u"helloooo")
        self.flush()

        filepath = file_path('ffcc00.gif')
        change = project.add_change(user, u"/foobar.gif", filepath, u"this is a new change")
        self.flush()
        
        r, change = api.file.get(user, user, project.eid, path=u"/foobar.gif")
        #print r.results
        
        assert r.name
        assert r.eid
        assert change.version
        assert r.path
        assert change.change_extracts
    
    def test_comments(self):
        
        user = fh.create_user()
        project = fh.create_project(user=user, name=u"helloooo")
        self.flush()
        self.login(user)

        filepath = file_path('ffcc00.gif')
        change = project.add_change(user, u"/foobar.gif", filepath, u"this is a new change")
        self.flush()
        
        extract = change.change_extracts[0]
        
        _extract, comment = api.file.add_comment(user, user, project.eid, 'My comment!', extract=extract.id, x=23, y=345, width=10, height=20)
        self.flush()
        
        assert _extract == extract
        assert comment.change == change
        assert comment.change_extract == extract
        
        assert comment.body == u'My comment!'
        assert comment.eid
        assert comment.x == 23
        assert comment.y == 345
        assert comment.width == 10
        assert comment.height == 20
        
        _, reply = api.file.add_comment(user, user, project.eid, 'My reply!', change=change.eid, in_reply_to=comment.eid)
        self.flush()
        
        assert reply
        assert reply.in_reply_to == comment
        assert reply.eid
        
        assert comment.replies
        assert len(comment.replies) == 1
        
        _change, comments = api.file.get_comments(user, user, project.eid, change=change.eid)
        
        assert change == _change
        assert len(comments) == 2
        assert comments[0] == comment
        assert comments[1] == reply
        assert comments[0].replies[0] == reply
