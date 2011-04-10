import os, tempfile, mimetypes
from desio.api import enforce, logger, validate, h, authorize, \
                    AppException, ClientException, CompoundException, \
                    abort, FieldEditor, auth, \
                    IsAdmin, MustOwn, IsLoggedIn, CanWriteProject,CanAdminProject, CanReadProject, \
                    CanWriteOrg, CanReadOrg, MustOwn, Or, Exists
from desio.model import users, Session, projects, STATUS_APPROVED, STATUS_PENDING, STATUS_REJECTED, STATUS_COMPLETED, STATUS_OPEN
from desio import utils
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
    
    :param version: a change version number or 'all'. if None, will return HEAD
    """
    try:
        f = project.get_file(path)
    except AppException, e:
        raise ClientException(e.msg, code=e.code, field='path')
    
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

@enforce(binbody=bool)
@authorize(CanReadProject())
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
    
    return change.entity, change

@enforce(body=unicode, x=int, y=int, width=int, height=int, change=projects.Change, extract=projects.ChangeExtract, in_reply_to=projects.Comment)
@authorize(Or(Exists('change'), Exists('extract'), Exists('in_reply_to')), CanReadProject(get_from=['change', 'extract', 'in_reply_to']))
def add_comment(real_user, user, body, change=None, extract=None, in_reply_to=None, **kw):
    """
    Add a comment for either a change or an extract.
    """

    commentable = change or extract or in_reply_to.change
    return commentable, commentable.add_comment(user, body, in_reply_to=in_reply_to, **kw)

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
@authorize(Or(Exists('change'), Exists('extract'), Exists('file')), CanReadProject(get_from=['change', 'file', 'extract']))
def get_comments(real_user, user, change=None, extract=None, file=None):
    """
    Get all comments related to the commentable object passed
    """
    commentable = change or extract or file
    return commentable, commentable.get_comments()
    
