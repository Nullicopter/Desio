"""
The base Controller API
"""

#careful with the imports. Controllers import * from here...
from pylons import tmpl_context as c, config, app_globals as g, request, response, session
from pylons.controllers.util import redirect, abort

from pylons_common.lib import exceptions, log
from pylons_common import lib as utils
from pylons_common.web import validation
from pylons_common.web.response import *

log.set_default_logger('desio')
from pylons_common.lib.log import logger

import time
import auth
import helpers as h

from formencode import htmlfill
import formencode

from pylons.controllers import WSGIController

from desio.model import meta, users, projects, APP_ROLE_ADMIN, APP_ROLE_READ, APP_ROLE_WRITE
from desio.model.meta import Session

class BaseController(WSGIController):

    def render(self, *args, **kw):
        return render_response(*args, **kw)
    
    def validate(self, validation_class, **kw):
        return validation.validate(validation_class, **kw)
    
    def __call__(self, environ, start_response):
        """Invoke the Controller"""
        # WSGIController.__call__ dispatches to the Controller method
        # the request is routed to. This routing information is
        # available in environ['pylons.routes_dict']
        try:
            self._session = Session
            
            auth.authenticate_basic_auth()
            
            if '_debug_frontend' in request.params:
                #now we can force this no matter the environment.
                c.debug_frontend = request.params['_debug_frontend'] == 'True'
            else:
                c.debug_frontend = not h.is_production()
            
            #this is used by timer proxy and the templates
            c.show_debug = bool(session.get('show_debug'))
            
            request.environ['USER'] = session.get('username', '')
            request.environ['REAL_USER'] = session.get('real_username', '')
            
            # set the start of the rendering
            c.render_start = time.time()
            
            c.requested_url = request.environ.get('PATH_INFO')
            if request.environ.get('QUERY_STRING'):
                c.requested_url += '?' + request.environ['QUERY_STRING']
            logger.info(c.requested_url)

            # Capture IP address in non-ssl mode, so we can use it in SSL mode see ticket #2275
            ip = auth.get_user_ip()
            if not session.get('IP_ADDRESS') and ip:
                session['IP_ADDRESS'] = ip
            elif not session.get('IP_ADDRESS') and request.environ.get('HTTP_RLNCLIENTIPADDR'):
                session['IP_ADDRESS'] = request.environ.get('HTTP_RLNCLIENTIPADDR')
            elif not session.get('IP_ADDRESS') and request.environ.get('REMOTE_ADDR'):
                session['IP_ADDRESS'] = request.environ.get('REMOTE_ADDR')
            
            # Save the first referer we see to store in user record when/if we create one.
            if not session.get('referer'):
                session['referer'] = environ.get('HTTP_REFERER','').decode('utf-8','ignore')
                session.save()
            
            if session.get('notify'):
                c._notify = session['notify']
                del session['notify']
                session.save()
            
            return WSGIController.__call__(self, environ, start_response)
        finally:
            if 'paste.testing_variables' not in request.environ:
                Session.remove()
    
    def _set_session_for_flash_uploads(self):
        '''
        For flash uploads, flash does not pass the cookie forward.
        So, I do it in a request param, then do this crap to reset the proper
        session.
        
        http://groups.google.com/group/pylons-discuss/browse_thread/thread/7814b72df58f788b?pli=1
        '''
        if 'session_cookie' in request.params:

            cookie = request.params['session_cookie']

            logger.info("BF3: Got session cookie '%s', resetting session...." % cookie)

            session_id = str(cookie)
            newsession = session.get_by_id(session_id)

            # Normal pylons session behavior creates a temporary session if none exists.
            # If we don't do that here, and no session exists (such as right after the session store (memcached)
            # is restarted, and one tries to upload a logo w/o logging in), subsequent code will puke.
            # The safest way to fix this would be to emulate pylons behavior, and instantiate a fresh beaker.session.Session object,
            # but I don't know what to pass in for the billions of kwargs it takes, so we'll just use an empty {} for simplicity.
            # If something breaks down the line because it expects Session-specific methods or properties, this is the problem.
            if not newsession:
                logger.info("No session found for key '%s'! Using an empty dictionary..." % cookie)
                newsession = {}

            # Load the registry and replace our global session withthe new one
            registry = request.environ['paste.registry']
            registry.register(session, newsession)

            # Replace the other session reference to look to the new one
            pylons_obj = request.environ['pylons.pylons']
            pylons_obj.session = newsession
    
    def redirect(self, *args, **kw):
        return redirect(*args, **kw)
    
    def add(self, *args, **kwargs):
        self._session.add(*args, **kwargs)
    
    def rollback(self):
        """
        convenience method to rollback the applied data
        """
        self._session.rollback()

    def flush(self, *args):
        """
        convenience method; flush data into transaction
        """
        self._session.flush(*args)
           
    def commit(self):
        """
        convenience method; commit the transaction
        """
        # only do the flushing if we are running functional tests
        if 'paste.testing_variables' in request.environ:
            logger.info('Flushing, not committing...')
            self._session.flush()
        else:
            self._session.commit()


class OrganizationBaseController(BaseController):
    """
    Controllers that extend this base controller are guaranteed a user is logged into
    an organization that he has at the ver least, read access to. It will set a few
    variables in the context for you:
    
    c.organization: the organization being viewed
    c.real_user: the logged in user
    c.user: the pretend or logged in user
    c.user_role: the user's role in this org
    c.is_org_admin: do they have role == admin?
    c.is_org_creator: Are they a creator?
    c.is_org_*: if we add more roles, we should add them here for easy checking in the templates
    """
    def __before__(self, **kw):
        from desio import api
        from desio.model import STATUS_PENDING
        
        ru, u = (auth.get_real_user(), auth.get_user())
        
        auth.RedirectOnFail(api.IsLoggedIn(), url='/login').check(ru, u)
        
        try:
            c.organization = api.organization.get(subdomain=kw.get('sub_domain'))
        except ClientException, e:
            abort(404)
        
        c.user_role = c.organization.get_role(c.user)
        c.is_org_admin = c.user_role in [APP_ROLE_ADMIN]
        c.is_org_creator = c.user_role in [APP_ROLE_ADMIN, APP_ROLE_WRITE]
        c.is_org_user = bool(c.user_role)
        
        self.projects = c.projects = api.project.get(c.real_user, c.user, c.organization)
        
        self._check_role()
    
    def _check_role(self):
        from desio import api
        from desio.model import STATUS_PENDING
        
        def tohome(*a, **k):
            orgu = c.organization.get_user_connection(c.user, status=None)
            if orgu and orgu.status == STATUS_PENDING:
                return '/pending'
            
            return config.get('pylons_url') or '/'
        
        if not self.projects:
            auth.RedirectOnFail(api.CanReadOrg(), fn=tohome).check(c.real_user, c.user, organization=c.organization)

"""
This may be confusing. Here are some authorization classes, specific to the controllers.
They are different than the api classes in that they are dependent on the context variables
that are placed by the base controller. They also redirect on failed test.
"""
class HasOrgRole(object):
    
    def __init__(self, *roles, **kw):
        self.roles = roles
        self.url = kw.get('url') or '/'
    
    def check(self, real_user, user, **kwargs):
        
        if c.user_role not in self.roles:
            redirect(self.url)
        
        return True

class CanReadOrgRedirect(HasOrgRole):
    """
    They can read all the projects they have access to. They can see org activity, etc.
    """
    def __init__(self, **kw):
        super(CanReadOrgRedirect, self).__init__(
            APP_ROLE_ADMIN, APP_ROLE_WRITE, APP_ROLE_READ,
            **kw)

class CanContributeToOrgRedirect(HasOrgRole):
    """
    They can create and modify projects and membership in projects.
    """
    def __init__(self, **kw):
        super(CanContributeToOrgRedirect, self).__init__(
            APP_ROLE_ADMIN, APP_ROLE_WRITE, **kw)

class CanAdminOrgRedirect(HasOrgRole):
    """
    They are an organization admin. They can edit CC information, organization membership, they
    can read/write all projects.
    """
    def __init__(self, **kw):
        super(CanAdminOrgRedirect, self).__init__(APP_ROLE_ADMIN, **kw)

"""
Project role decorators
"""

class HasProjectRole(object):
    """
    """
    def __init__(self, *roles, **kw):
        self.roles = roles
        self.url = kw.get('url') or '/'
    
    def check(self, real_user, user, project=None, **kwargs):
        
        if project and project.get_role(user) in self.roles:
            return True
        
        redirect(self.url)

class CanReadProjectRedirect(HasProjectRole):
    """
    They can read all the projects they have access to. They can see org activity, etc.
    """
    def __init__(self, **kw):
        super(CanReadProjectRedirect, self).__init__(
            APP_ROLE_ADMIN, APP_ROLE_WRITE, APP_ROLE_READ,
            **kw)

class CanWriteProjectRedirect(HasProjectRole):
    """
    They can create and modify projects and membership in projects.
    """
    def __init__(self, **kw):
        super(CanWriteProjectRedirect, self).__init__(
            APP_ROLE_ADMIN, APP_ROLE_WRITE, **kw)

class CanAdminProjectRedirect(HasProjectRole):
    """
    They are an organization admin. They can edit CC information, organization membership, they
    can read/write all projects.
    """
    def __init__(self, **kw):
        super(CanAdminProjectRedirect, self).__init__(APP_ROLE_ADMIN, **kw)


"""
Entity role decorators
"""

class HasEntityRole(object):
    """
    """
    def __init__(self, *roles, **kw):
        self.roles = roles
        self.url = kw.get('url') or '/'
    
    def check(self, real_user, user, entity=None, **kwargs):
        
        if entity and entity.get_role(user) in self.roles:
            return True
        
        redirect(self.url)

class CanReadEntityRedirect(HasEntityRole):
    """
    They can read all the projects they have access to. They can see org activity, etc.
    """
    def __init__(self, **kw):
        super(CanReadEntityRedirect, self).__init__(
            APP_ROLE_ADMIN, APP_ROLE_WRITE, APP_ROLE_READ,
            **kw)

class CanWriteEntityRedirect(HasEntityRole):
    """
    They can create and modify projects and membership in projects.
    """
    def __init__(self, **kw):
        super(CanWriteEntityRedirect, self).__init__(
            APP_ROLE_ADMIN, APP_ROLE_WRITE, **kw)

class CanAdminEntityRedirect(HasEntityRole):
    """
    They are an organization admin. They can edit CC information, organization membership, they
    can read/write all projects.
    """
    def __init__(self, **kw):
        super(CanAdminEntityRedirect, self).__init__(APP_ROLE_ADMIN, **kw)