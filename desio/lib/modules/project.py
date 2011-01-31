from desio import api
from desio.lib.base import *
from desio.model import STATUS_APPROVED
from desio.controllers.api import v1

def project_user_module(real_user, user, organization, project=None):
    """
    """
    # email: user def list
    org_users = api.organization.get_users(real_user, user, organization, status=STATUS_APPROVED)
    user_map = dict([(ou.user.email, v1.user.get().output(ou.user)) for ou in org_users])
    
    #email list for lookup
    emails = [u.user.email for u in org_users]
    
    # list of users in the project and their role
    proj_users = []
    if project:
        proj_users = api.project.get_users(real_user, user, project, status=STATUS_APPROVED)
        proj_users = v1.project.get_users().output(proj_users)
    
    params = {
        'emails': emails,
        'projectUsers': proj_users,
        'userMap': user_map,
        'roleUrl': h.api_url('project', 'set_user_role', project=project and project.eid or None),
        'syncUrl': h.api_url('project', 'attach_users')
    }
    
    return params