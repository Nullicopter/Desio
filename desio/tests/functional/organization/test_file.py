from datetime import date, timedelta

from desio.model import users, fixture_helpers as fh
from desio.tests import *
from desio import api

from pylons_common.lib.exceptions import *

class TestFile(TestController):
    
    def test_view(self):
        
        user = fh.create_user()
        project = fh.create_project(user=user, name=u"helloooo")
        self.flush()

        filepath = file_path('ffcc00.gif')
        change = project.add_change(user, u"/foobar.gif", filepath, u"this is a new change")
        self.flush()
        
        #no user logged in. Intentional
        r = self.get(url_for(controller='organization/file',
                             action='view',
                             project=project.eid,
                             file=change.entity.eid),
                     sub_domain=project.organization.subdomain)
        
        assert r
        assert 'file_' + project.eid + '_' + change.entity.eid in r
        
        #rando
        rando = fh.create_user()
        self.flush()
        self.login(rando)
        r = self.get(url_for(controller='organization/file',
                             action='view',
                             project=project.eid,
                             file=change.entity.eid),
                     sub_domain=project.organization.subdomain)
        
        assert r
        assert 'file_' + project.eid + '_' + change.entity.eid in r
        
        #real user redirects
        self.login(user)
        r = self.follow(self.get(url_for(controller='organization/file',
                             action='view',
                             project=project.eid,
                             file=change.entity.eid),
                     sub_domain=project.organization.subdomain, status=302),
                    sub_domain=project.organization.subdomain)
        
        assert r
        assert 'project_' + project.slug + '_' + change.entity.name in r
        