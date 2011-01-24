"""
To help you writing tests. Should be able to create each type of object in the system
with no other inputs. 
"""
from desio.model import Session, users, STATUS_APPROVED, STATUS_PENDING, STATUS_REJECTED
from desio.model import projects
from pylons_common.lib import utils
import random

def create_unique_str(pre=u'', extra=u"\u00bf"):
    """
    @param pre: The string to prefix the unique string with. Defaults to
                nothing.
    @param extra: The string to append to the unique string. Default to a
                  unicode character.
    @return: A unique string.
    """
    return u"%s%s%s" % (pre, utils.uuid(), extra)

def create_email_address():

    return create_unique_str(u'email') + u"@email.com"

def create_str(length=None):
        
        letters = u'abcdefghijklmnopqrstuvwxyz1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        key = []
        
        l = length or random.randint(30, 50)
        
        for i in range(l):
            key.append(letters[random.randint(0, len(letters)-1)])
        
        return u''.join(key)

def create_user(is_admin=False, **kw):

    kw.setdefault("email", create_email_address())
    kw.setdefault("username", create_unique_str(u'user', extra=u''))
    kw.setdefault("password", u'testpassword')
    
    if is_admin:
        kw.setdefault("role", users.ROLE_ADMIN)
    else:
        kw.setdefault("role", users.ROLE_USER)

    user = users.User(**kw)
    Session.add(user)
    Session.flush()
    return user

def create_organization(user=None, role=users.ORGANIZATION_ROLE_ADMIN, status=STATUS_APPROVED, **kw):
    """
    create an org and will attach a user to it. If no user specified, will make one.
    """
    kw.setdefault("name", create_unique_str(u'org'))
    kw.setdefault("url", u'http://%s.com' % create_unique_str(u'url'))
    kw.setdefault("subdomain", create_str(length=10))
    
    user = user or create_user()
    
    org = users.Organization(**kw)
    Session.add(org)
    
    #connect user to org as admin of org
    org_user = org.attach_user(user, role=role, status=status)
    Session.flush()
    
    return org

def create_project(user=None, organization=None, role=users.ORGANIZATION_ROLE_ADMIN, **kw):
    kw.setdefault("name", create_unique_str(u'project'))
    kw.setdefault("description", create_unique_str(u"description"))
    kw.setdefault("status", STATUS_APPROVED)

    org = organization or create_organization(user, role)

    project = projects.Project(organization=org, **kw)
    Session.add(project)
    Session.flush()

    return project
    
