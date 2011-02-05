from datetime import date, timedelta

from desio.model import users, fixture_helpers as fh
from desio.tests import *

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
