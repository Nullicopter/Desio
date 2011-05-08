from datetime import date, timedelta

from desio.model import users, fixture_helpers as fh
from desio.tests import *
from desio import api
from desio.utils import image

from pylons_common.lib.exceptions import *

class TestChange(TestController):
    
    def test_get(self):
        
        user = fh.create_user()
        bot = fh.create_user()
        bot.role = users.ROLE_ROBOT
        project = fh.create_project(user=user, name=u"helloooo")
        self.flush()
        self.login(bot)

        filepath = file_path('ffcc00.gif')
        change = project.add_change(user, u"/foobar.gif", filepath, u"this is a new change")
        self.flush()
        
        filepath = file_path('cs5.png')
        changepng = project.add_change(user, u"/cs5.png", filepath, u"this is a new change")
        self.flush()
        
        r = self.client_async(api_url('change', 'get', id=changepng.eid), {})
        
        assert r.results
        assert r.results.change_eid == changepng.eid
        assert r.results.parse_type == image.PARSE_TYPE_FIREWORKS_CS5
        assert r.results.parse_status == image.PARSE_STATUS_PENDING
        
        r = self.client_async(api_url('change', 'get'), {'parse_type': image.PARSE_TYPE_FIREWORKS_CS5})
        assert len(r.results) == 1
        assert r.results[0].change_eid == changepng.eid
        
        r = self.client_async(api_url('change', 'get'), {'parse_status': image.PARSE_STATUS_PENDING})
        assert len(r.results) == 1
        assert r.results[0].change_eid == changepng.eid
        
        r = self.client_async(api_url('change', 'get'), {'parse_type': image.PARSE_TYPE_FIREWORKS_CS5+','+image.PARSE_TYPE_IMAGEMAGICK})
        assert len(r.results) == 2
        assert r.results[0].change_eid == change.eid
        assert r.results[1].change_eid == changepng.eid
    
    def test_edit(self):
        
        user = fh.create_user()
        bot = fh.create_user()
        bot.role = users.ROLE_ROBOT
        project = fh.create_project(user=user, name=u"helloooo")
        self.flush()
        self.login(bot)
        
        filepath = file_path('cs5.png')
        changepng = project.add_change(user, u"/cs5.png", filepath, u"this is a new change")
        self.flush()
        
        assert changepng.parse_status == image.PARSE_STATUS_PENDING
        
        r = self.client_async(api_url('change', 'edit', id=changepng.eid), {'parse_status':image.PARSE_STATUS_IN_PROGRESS})
        
        assert r.results.parse_status == image.PARSE_STATUS_IN_PROGRESS
        
        Session.refresh(changepng)
        
        assert changepng.parse_status == image.PARSE_STATUS_IN_PROGRESS
        