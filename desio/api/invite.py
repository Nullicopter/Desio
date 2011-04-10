import os, tempfile, mimetypes
from desio.api import enforce, logger, validate, h, authorize, abort, auth, IsLoggedIn, \
                    AppException, ClientException, CompoundException, Or, Exists, \
                    CanWriteProject, CanAdminProject, CanReadProject, \
                    CanWriteOrg, CanReadOrg, CanAdminOrg, \
                    CanWriteEntity, CanReadEntity, CanAdminEntity

from desio.model import users, Session, projects, STATUS_APPROVED, STATUS_PENDING, \
                    STATUS_REJECTED, STATUS_COMPLETED, STATUS_OPEN, \
                    APP_ROLE_READ, APP_ROLES, commit
from desio import utils
from desio.utils import email as email_mod

import sqlalchemy as sa

import formencode
import formencode.validators as fv

from pylons_common.lib.exceptions import *

ID_PARAM = 'invite'

@enforce(role=unicode, email=unicode)
@authorize(
    Or( Exists('entity'), Exists('project'), Exists('organization') ),
    Or( CanAdminEntity(), CanAdminProject(), CanAdminOrg() )
)
def create(real_user, user, email, entity=None, project=None, organization=None, role=APP_ROLE_READ):
    
    class Form(formencode.Schema):
        email = formencode.All(fv.Email(not_empty=True), fv.MaxLength(256))
        role = fv.OneOf(APP_ROLES, not_empty=True)
    validate(Form, role=role, email=email)
    
    obj = entity or project or organization
    try:
        invite = users.Invite.create(user, email, obj, role=role)
        commit()
    except AppException, e:
        if e.code == DUPLICATE:
            raise ClientException('%s has already been invited to %s' % (email, obj.name), DUPLICATE)
        raise ClientException(e.msg, e.code)
    
    email_mod.send(invite.invited_user or email, 'invite.txt', {
        'invite': invite,
        'invitee': user
    })
    return invite

@enforce(invite=users.Invite)
def get(invite):
    return invite

@enforce(invite=users.Invite)
@authorize(IsLoggedIn())
def accept(real_user, user, invite):
    invite.accept(user)
    return True

@enforce(invite=users.Invite)
@authorize(IsLoggedIn())
def reject(real_user, user, invite):
    invite.reject()
    return True