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

@enforce(garbage=bool)
@authorize(CanReadProject())
def get(real_user, user, project, path):
    p, name = os.path.split(path)
    q = Session.query(projects.File)
    q = q.filter_by(path=p)
    q = q.filter_by(name=name)
    return q.first()
    

@enforce(binbody=bool)
@authorize(CanReadProject())
def upload(real_user, user, project, **kw):
    """
    """
    from pylons import request
    print request.headers
    fname = request.headers.get('X-Up-Filename')
    type = request.headers.get('X-Up-Type')
    path = request.headers.get('X-Up-Path')
    description = request.headers.get('X-Up-Description')
    
    if not fname or not type or not path: return None

    ext = None
    if type:
        ext = mimetypes.guess_extension(type)
    
    f, tmpname = tempfile.mkstemp(ext)
    #why is this returning an int on my machine? Supposed to be a file pointer.
    if isinstance(f, int):
        f = open(tmpname, 'wb')
    
    print tmpname
    
    #this is inefficient. Pylons supposedly already creates a tmp file. We are instead
    #reading the thing into memory. I'm lazy until this beomes an issue (prolly soon)
    f.write(request.environ['wsgi.input'].read())
    f.close()
    
    #fileObj = project.add_change(os.path.join(path, fname), tmpname, u'')
    
    return True