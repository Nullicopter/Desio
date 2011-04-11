from desio.lib.base import *
from desio.model.users import INVITE_TYPE_ENTITY, INVITE_TYPE_ORGANIZATION, INVITE_TYPE_PROJECT
from desio.model import STATUS_APPROVED, STATUS_PENDING
from desio import api

from pylons_common.lib.utils import extract

class InviteController(BaseController):
    """
    """
    
    @dispatch_on(POST='_handle_invite')
    def index(self, id=None, **k):
        """
        
        """
        invite = api.invite.get(id)
        
        if not invite: abort(404)
        
        c.invite = invite
        
        if invite.status == STATUS_PENDING:
            
            url = self._get_url(invite)
            
            if auth.get_user() and c.user.email.lower() != invite.invited_email.lower():
                logger.info('%s logged in already, logging out and redirecting' % c.user)
                auth.logout()
                redirect(h.url_for(action='index', id=id))
            
            elif auth.get_user(): #user is logged in and has the same email
                logger.info('%s logged in already, has same email address as ' % invite.invited_email)
                invite.accept(c.user)
                self.commit()
                redirect(url)

        return self.render('/invite/index.html')
    
    @mixed_response('index')
    def _handle_invite(self, id=None, **k):
        
        invite = api.invite.get(id)
        if not invite: abort(404)
        
        url = None
        
        if invite.status == STATUS_PENDING:
            
            url = self._get_url(invite)
            user = auth.get_user()
            
            if not user:
                
                params = extract(request.params, 'name', 'password', 'confirm_password', 'default_timezone')
                params['email'] = params['username'] = invite.invited_email
                
                logger.info('No user, creating one with %s' % params)
                
                user = api.user.create(**params)
                self.flush()
                
                auth.login(user, False)
            else:
                logger.info('User already logged in %s, not creating' % (user))
            
            if user and user.email.lower() == invite.invited_email.lower():
                logger.info('Accepting Invite %s as %s' % (invite, user))
                api.invite.accept(user, user, invite)
            else:
                raise exceptions.ClientException('Logout Please', exceptions.INVALID)
            
            self.commit()
            
        return {'url': url or '/'}
        
        
    def _get_url(self, invite):
        
        url = None
        if invite.type == INVITE_TYPE_ENTITY:
            url = h.subdomain_url(invite.object.project.organization.subdomain,
                                  controller='organization/project', slug=invite.object.project.slug, action='view') + invite.object.full_path
        
        elif invite.type == INVITE_TYPE_PROJECT:
            url = h.subdomain_url(invite.object.project.organization.subdomain,
                                  controller='organization/project', slug=invite.object.project.slug, action='view')
        
        elif invite.type == INVITE_TYPE_PROJECT:
            url = h.subdomain_url(invite.object.project.organization.subdomain)
        
        return url
        
