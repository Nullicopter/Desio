from desio.lib.base import *

class IndexController(BaseController):
    """
    """
    def index(self, **k):
        
        user = auth.get_user()
        
        if user:
            c.organizations = user.get_organizations()
            
            c.projects = user.get_projects()
            # we only show the projects that the user cant get to any other way.
            # if they dont have a role in the parent, then they are relegated to the project.
            c.projects = [p for p in c.projects if not p.organization.get_role(user)]
            
            c.files = user.get_entities()
            # we only show the files that the user cant get to any other way.
            c.files = [f for f in c.files if not f.project.get_role(user)]
            
            
            if len(c.organizations) == 1 and not c.projects and not c.files:
                redirect(h.url_for(sub_domain=c.organizations[0].subdomain, controller='organization/home', action='index'))
            
            if len(c.projects) == 1 and not c.organizations and not c.files:
                p = c.projects[0]
                #redirect(h.url_for(sub_domain=p.organization.subdomain, controller='organization/project', action='view', slug=p.slug))
                redirect(h.url_for(sub_domain=p.organization.subdomain, controller='organization/home', action='index'))
            
            if len(c.files) == 1 and not c.organizations and not c.projects:
                f = c.files[0]
                p = f.project
                o = p.organization
                redirect(h.url_for(sub_domain=o.subdomain, controller='organization/project', action='view', slug=p.slug, path=f.full_path[1:]))
            
            return self.render('/index/dash.html')
            
        return self.render('/index/index.html')

