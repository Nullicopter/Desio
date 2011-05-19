import os, tempfile, mimetypes
from desio.api import enforce, logger, validate, h, authorize, abort, auth, IsLoggedIn, \
                    AppException, ClientException, CompoundException, \
                    Or, Exists, CanReadProject, CanReadOrg, CanReadEntity

from desio.model import users, Session, projects, activity
from desio import utils

import formencode
import formencode.validators as fv

from datetime import datetime

from pylons_common.lib.exceptions import *

@enforce(u=users.User, entity=projects.Entity, limit=int, offset=datetime)
@authorize( Or( Exists('organization'), Exists('project'), Exists('entity') ) )
def get(real_user, user, organization=None, project=None, entity=None, u=None, offset=None, limit=5):
    
    if organization:
        CanReadOrg().check(real_user, user, organization=organization)
    if project:
        CanReadProject().check(real_user, user, project=project)
    if entity:
        CanReadEntity().check(real_user, user, entity=entity)

    act = activity.get_activities(organization=organization, project=project, entity=entity, user=u, offset=offset, limit=limit)
    
    return act