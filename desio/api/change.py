import tempfile

from desio.api import enforce, logger, validate, h, authorize, \
                    AppException, ClientException, CompoundException, \
                    abort, FieldEditor, auth, \
                    IsAdmin, MustOwn, IsLoggedIn, CanWriteProject,CanAdminProject, CanReadProject, \
                    CanWriteOrg, CanReadOrg, Exists, Or, IsRobot, CanReadEntity
from desio.model import users, Session, projects, activity, STATUS_APPROVED, STATUS_PENDING, STATUS_REJECTED
from desio.utils import email, to_unicode
import sqlalchemy as sa
import os.path

import formencode
import formencode.validators as fv

from pylons_common.lib.exceptions import *
from pylons_common.lib.utils import uuid

EDIT_FIELDS = ['parse_status']

ID_PARAM = 'change'

@enforce(change=projects.Change, parse_type=[unicode], parse_status=[unicode])
@authorize(Or(IsRobot(), CanReadEntity(get_from=['change'])))
def get(real_user, user, change=None, parse_type=None, parse_status=None):
    
    if change:
        return change

    if not parse_status and not parse_type:
        raise ClientException('either parse_type or parse_status')
    
    q = Session.query(projects.Change)
    if parse_type:
        q = q.filter(projects.Change.parse_type.in_(parse_type))
    
    if parse_status:
        q = q.filter(projects.Change.parse_status.in_(parse_status))
    
    q = q.order_by(sa.asc(projects.Change.created_date))
    
    return q.all()

@enforce()
@authorize(Or(IsAdmin(), IsRobot()))
def edit(real_user, user, change, **kwargs):
    """
    Editing of the campaigns. Supports editing one param at a time. Uses the FieldEditor
    paradigm.
    """
    editor = Editor()
    editor.edit(real_user, user, change, **kwargs)
    Session.flush()
    Session.refresh(change)
    return change

class Editor(FieldEditor):
    def __init__(self):
        
        class EditForm(formencode.Schema):
            parse_status = fv.UnicodeString(not_empty=False)
        
        super(Editor, self).__init__(EDIT_FIELDS, [], EditForm)

    def edit_parse_status(self, real_user, user, ch, key, param):
        self._edit_generic('Status', ch, key, param)

@enforce()
@authorize(IsRobot())
def upload_extract(real_user, user, change, **kw):
    """
    File is binary in the request body.
    """
    
    from pylons import request
    order_index = int(to_unicode(request.headers.get('X-Up-Order-Index')))
    type = to_unicode(request.headers.get('X-Up-Type'))
    
    if not type: return None
    
    f, tmpname = tempfile.mkstemp('png')
    if isinstance(f, int):
        f = open(tmpname, 'wb')
    
    #this is inefficient. Pylons supposedly already creates a tmp file. We are instead
    #reading the thing into memory. I'm lazy until this beomes an issue (prolly soon)
    #V: please make this not suck
    f.write(request.environ['wsgi.input'].read())
    f.close()
    
    new = False
    change_extract = Session.query(projects.ChangeExtract).filter_by(change=change, extract_type=type, order_index=order_index).first()
    if not change_extract:
        new = True
        change_extract = projects.ChangeExtract(change=change, extract_type=type, order_index=order_index)
        Session.add(change_extract)
    
    change_extract.set_contents(tmpname)
    
    return new and 'new' or 'existing'