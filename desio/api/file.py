import os, tempfile, mimetypes
from desio.api import enforce, logger, validate, h, authorize, \
                    AppException, ClientException, CompoundException, \
                    abort, FieldEditor, auth, \
                    IsAdmin, MustOwn, IsLoggedIn, CanWriteProject,CanAdminProject, CanReadProject, \
                    CanWriteOrg, CanReadOrg, MustOwn, Or, Exists, CanReadEntity, IsRobot, IsAdmin, CanAdminEntity
from desio.model import users, Session, projects, STATUS_APPROVED, STATUS_PENDING, STATUS_REJECTED, STATUS_COMPLETED, STATUS_OPEN
from desio import utils
from desio.utils import email
import sqlalchemy as sa

import formencode
import formencode.validators as fv

from pylons_common.lib.exceptions import *

EDIT_FIELDS = ['name']
ADMIN_EDIT_FIELDS = []

ID_PARAM = 'file'

class UniqueName(fv.FancyValidator):
    def __init__(self, project, file):
        self.file = file
        self.project = project
    
    def _to_python(self, value, state):
        # we don't support multiple values, so we run a quick check here (we got a webapp where this was a problem)
        if not isinstance(value, unicode):
            raise fv.Invalid('You must supply a valid string.', value, state)

        file = Session.query(projects.Entity
                ).filter(projects.Entity.project==self.project
                ).filter(projects.Entity.path==self.file.path
                ).filter(projects.Entity.name==value
                )
        
        file = file.filter(projects.Entity.id != self.file.id)
        file = file.first()

        if file:
            raise fv.Invalid('A file with this name already exists. Please choose another.', value, state)
        
        return value

@enforce(path=unicode, version=unicode, file=projects.Entity)
def get(real_user, user, project=None, path=None, version=None, file=None):
    """
    Get a file and the latest change. If a version is specified, return that change.
    
    :param version: a change version number or 'all'. if None, will return HEAD
    """
    if file:
        f = file
    else:
        try:
            f = project.get_file(path)
        except AppException, e:
            raise ClientException(e.msg, code=e.code, field='path')
    
    Or(IsRobot(), IsAdmin(), CanReadEntity()).check(real_user, user, entity=f)
    
    #if they want all, give them all changes plus the file in each
    if version == 'all':
        changes = f.get_changes()
        return [(f, ch) for ch in changes]
    elif version:
        try:
            version = int(version)
        except ValueError, e:
            raise ClientException('Version must be an int, "all" or empty', code=INVALID, field='version')
    
    return f, f.get_change(version)

@enforce(file=projects.Entity)
@authorize(CanAdminEntity(param='file'))
def edit(real_user, user, file, **kwargs):
    """
    Editing of the campaigns. Supports editing one param at a time. Uses the FieldEditor
    paradigm.
    """
    editor = Editor(file)
    editor.edit(real_user, user, file, **kwargs)
    Session.flush()
    Session.refresh(file)
    return file

class Editor(FieldEditor):
    def __init__(self, file):
        
        class EditForm(formencode.Schema):
            name = formencode.All(fv.UnicodeString(not_empty=False), UniqueName(file.project, file))
        super(Editor, self).__init__(EDIT_FIELDS, ADMIN_EDIT_FIELDS, EditForm)

    def edit_name(self, real_user, user, u, key, param):
        self._edit_generic('Name', u, key, param)

@enforce(binbody=bool)
@authorize(CanWriteProject())
def upload(real_user, user, project, **kw):
    """
    File is binary in the request body.
    """
    from pylons import request
    fname = utils.to_unicode(request.headers.get('X-Up-Filename'))
    type = utils.to_unicode(request.headers.get('X-Up-Type'))
    path = utils.to_unicode(request.headers.get('X-Up-Path'))
    description = utils.to_unicode(request.headers.get('X-Up-Description'))
    
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
    
    if change.version == 1:
        #email
        users = project.interested_users
        if user in users: users.remove(user)
        email.send(users, 'create_file.txt', {
            'project': project,
            'change': change,
            'creator': user
        })
    else:
        #email
        users = change.entity.interested_users
        if user in users: users.remove(user)
        email.send(users, 'create_change.txt', {
            'project': project,
            'change': change,
            'creator': user
        })
    
    return change.entity, change

@enforce(body=unicode, x=int, y=int, width=int, height=int, change=projects.Change, extract=projects.ChangeExtract, in_reply_to=projects.Comment)
@authorize(
    Or(Exists('change'), Exists('extract'), Exists('in_reply_to')),
    Or(CanReadProject(get_from=['change', 'extract', 'in_reply_to']), CanReadEntity(get_from=['change', 'extract.change', 'in_reply_to.change'])))
def add_comment(real_user, user, body, change=None, extract=None, in_reply_to=None, **kw):
    """
    Add a comment for either a change or an extract.
    """

    commentable = change or extract or in_reply_to.change
    
    comment = commentable.add_comment(user, body, in_reply_to=in_reply_to, **kw)
    
    #email
    if in_reply_to:
        users = in_reply_to.interested_users
        if user in users: users.remove(user)
        email.send(users, 'create_reply.txt', {
            'comment': comment,
            'creator': user,
            'parent_comment': in_reply_to,
            'entity': in_reply_to.change.entity,
            'change': in_reply_to.change,
        })
    else:
        ch = change or extract.change
        entity = ch.entity
        
        users = entity.interested_users
        if user in users: users.remove(user)
        email.send(users, 'create_comment.txt', {
            'comment': comment,
            'entity': entity,
            'change': ch,
            'creator': user
        })
    
    return commentable, comment

@enforce(comment=projects.Comment)
@authorize(Exists('comment'), Or( MustOwn('comment'), CanAdminProject(get_from='comment') ))
def remove_comment(real_user, user, comment, **kw):
    """
    Remove a comment.
    """
    
    comment.delete()
    return True

@enforce(comment=projects.Comment, status=unicode)
@authorize(Exists('comment'), Or( CanWriteProject(get_from='comment'), MustOwn('comment') ))
def set_comment_completion_status(real_user, user, comment, status=None, **kw):
    """
    Set completion status
    """
    class StatusForm(formencode.Schema):
        status = fv.OneOf([STATUS_OPEN, STATUS_COMPLETED], not_empty=True)
    scrubbed = validate(StatusForm, status=status)
    
    return comment.set_completion_status(user, scrubbed.status)

@enforce(change=projects.Change, extract=projects.ChangeExtract, file=projects.File)
@authorize(
    Or( Exists('change'), Exists('extract'), Exists('file') ),
    Or( CanReadProject(get_from=['change', 'file', 'extract']), CanReadEntity(get_from=['change', 'extract.change']), CanReadEntity(param='file') )
)
def get_comments(real_user, user, change=None, extract=None, file=None):
    """
    Get all comments related to the commentable object passed
    """
    commentable = change or extract or file
    return commentable, commentable.get_comments()
    
