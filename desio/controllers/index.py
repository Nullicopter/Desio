from desio.lib.base import *

class IndexController(BaseController):
    """
    """
    def index(self, **k):
        
        user = auth.get_user()
        
        if user:
            c.organizations = user.get_organizations()
            if len(c.organizations) == 1:
                redirect(h.url_for(sub_domain=c.organizations[0].subdomain, controller='organization/home', action='index'))
        
        return self.render('/index/index.html')

