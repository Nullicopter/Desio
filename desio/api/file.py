import os, tempfile, mimetypes
from desio.api import enforce, logger, validate, h, authorize, \
                    AppException, ClientException, CompoundException, \
                    abort, FieldEditor, auth, \
                    IsAdmin, MustOwn, IsLoggedIn, CanWriteProject,CanAdminProject, CanReadProject, \
                    CanContributeToOrg, CanReadOrg
from desio.model import users, Session, projects, STATUS_APPROVED, STATUS_PENDING, STATUS_REJECTED
import sqlalchemy as sa

import formencode
import formencode.validators as fv

from pylons_common.lib.exceptions import *

ID_PARAM = 'file'

@enforce(path=unicode, version=unicode)
@authorize(CanReadProject())
def get(real_user, user, project, path, version=None):
    """
    Get a file and the latest change. If a version is specified, return that change.
    
    :param version: a change eid
    """
    try:
        f = project.get_file(path)
    except AppException, e:
        raise ClientException(e.msg, code=e.code, field='path')
    
    return f, f.get_change(version)

@enforce(binbody=bool)
@authorize(CanReadProject())
def upload(real_user, user, project, **kw):
    """
    File is binary in the request body.
    """
    from pylons import request
    fname = request.headers.get('X-Up-Filename')
    type = request.headers.get('X-Up-Type')
    path = request.headers.get('X-Up-Path')
    description = request.headers.get('X-Up-Description')
    
    if not fname or not type or not path: return None

    ext = None
    if type:
        ext = mimetypes.guess_extension(type)
        if not ext:
            _, ext = os.path.splitext(fname)
        ext = ext or ''
    
    f, tmpname = tempfile.mkstemp(ext)
    #why is this returning an int on my machine? Supposed to be a file pointer.
    if isinstance(f, int):
        f = open(tmpname, 'wb')
    
    #this is inefficient. Pylons supposedly already creates a tmp file. We are instead
    #reading the thing into memory. I'm lazy until this beomes an issue (prolly soon)
    #V: please make this not suck
    f.write(request.environ['wsgi.input'].read())
    f.close()
    
    change = project.add_change(user, os.path.join(path, fname), tmpname, u'')
    
    return change.entity, change
