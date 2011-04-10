from datetime import date, timedelta

from desio.model import users, fixture_helpers as fh, APP_ROLE_READ
from desio.tests import *

from pylons_common.lib.exceptions import *

class TestInit(TestController):
    
    def test_create(self):
        """
        Verifies that an ApiPrologueException is handled properly
        """
        u = fh.create_user()
        org = fh.create_organization(user=u, subdomain='cats', name='CATS!')
        project = fh.create_project(user=u, organization=org, name=u"helloooo")
        change = project.add_change(u, u"/main/project/arnold/foobar.gif", file_path('ffcc00.gif'), u"this is a new change")
        
        self.flush()
        
        self.login(u)
        
        response = self.client_async(api_url('invite', 'create', entity=change.entity.eid), {
            'email': 'something@asdpo.com',
            'role': APP_ROLE_READ
        })
        assert response.results.eid