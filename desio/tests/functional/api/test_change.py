from datetime import date, timedelta

from desio.model import users, fixture_helpers as fh
from desio.tests import *
from desio import api
from desio.utils import image

from pylons_common.lib.exceptions import *

import time

class TestChange(TestController):
    
    def test_get(self):
        
        noob = fh.create_user()
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
        
        self.login(user)
        r = self.client_async(api_url('change', 'get', id=changepng.eid), {})
        assert r.results.change_eid == changepng.eid
        self.logout()
        
        self.login(noob)
        self.post(api_url('change', 'get', id=changepng.eid), {}, status=400)
    
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
    
    def test_activity(self):
        
        user = fh.create_user()
        project = fh.create_project(user=user, name=u"helloooo")
        self.flush()
        self.login(user)
        
        time.sleep(1)
        
        filepath = file_path('ffcc00.gif')
        change = project.add_change(user, u"/foobar.gif", filepath, u"this is a new change")
        self.flush()
        
        time.sleep(1)
        
        filepath = file_path('cs5.png')
        changepng = project.add_change(user, u"/cs5.png", filepath, u"this is a new file")
        
        time.sleep(1)
        
        filepath = file_path('cs5.png')
        changepng = project.add_change(user, u"/cs5.png", filepath, u"this is a new change")
        
        time.sleep(1)
        
        filepath = file_path('cs5.png')
        changepng = project.add_change(user, u"/cs5.png", filepath, u"this is a new change")
        
        self.flush()
        
        all = self.client_async(api_url('activity', 'get', organization=project.organization.eid)).results
        four = self.client_async(api_url('activity', 'get', organization=project.organization.eid, limit='4')).results
        last = self.client_async(api_url('activity', 'get', organization=project.organization.eid, offset=all[2].created_date, limit='4')).results
        
        def p(r):
            print [res.type for res in r]
        
        #p(all)
        #p(four)
        #p(last)
        
        assert len(all) == 5 #['new_version', 'new_version', 'new_file', 'new_file', 'new_project']
        assert four == all[:4]
        assert last == all[3:]
        
        
        
        