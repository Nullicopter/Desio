import os, os.path
import mimetypes as mt
import urlparse
from datetime import datetime, MINYEAR

import sqlalchemy as sa
from sqlalchemy.orm import relationship, backref
from sqlalchemy.sql.expression import func

from desio.model.meta import Session, Base
import hashlib

from pylons_common.lib import exceptions, date, utils
from desio.model import users, STATUS_OPEN, STATUS_COMPLETED, STATUS_INACTIVE, STATUS_APPROVED
from desio.model import STATUS_EXISTS, STATUS_REMOVED, commit, flush
from desio.utils import file_uploaders as fu, image, is_testing

from collections import defaultdict as dd

PROJECT_ROLE_ADMIN = u'admin'
PROJECT_ROLE_READ = u'read'
PROJECT_ROLE_WRITE = u'write'

def get_unique_slug(organization, name, max=100):
    import re
    from pylons_common.lib.utils import uuid

    def gen_slug(input, addon=u''):
        return (u'-'.join(re.findall('[a-z0-9]+', input, flags=re.IGNORECASE)))[:max].lower() + addon
    
    for c in range(20):
        slug = gen_slug(name, addon=(c and unicode(c) or u''))
        project = Session.query(Project
                ).filter(Project.organization==organization
                ).filter(Project.slug==slug
                ).first()
        if not project: return slug
    
    return utils.uuid() #they have 20 projects named similarly, now they get eids!

class ProjectUser(Base):
    """
    Stores a user's role within a project
    """
    __tablename__ = "project_users"

    id = sa.Column(sa.Integer, primary_key=True)
    
    role = sa.Column(sa.Unicode(16), nullable=False)
    status = sa.Column(sa.Unicode(16), nullable=False)
    
    user = relationship("User", backref=backref("project_users", cascade="all"))
    user_id = sa.Column(sa.Integer, sa.ForeignKey('users.id'), nullable=False, index=True)
    
    project = relationship("Project", backref=backref("project_users", cascade="all"))
    project_id = sa.Column(sa.Integer, sa.ForeignKey('projects.id'), nullable=False, index=True)
    
    created_date = sa.Column(sa.DateTime, nullable=False, default=date.now)
    
    def __repr__(self):
        return u'ProjectUser(%s, org:%s, u:%s)' % (self.id, self.project_id, self.user_id)

class Project(Base):
    """
    A Project represents a revisioned tree of files
    """
    __tablename__ = "projects"
    
    id = sa.Column(sa.Integer, primary_key=True)
    eid = sa.Column(sa.String(22), default=utils.uuid, nullable=False, unique=True)

    status = sa.Column(sa.Unicode(16), nullable=False, default=STATUS_APPROVED)
    name = sa.Column(sa.UnicodeText(), nullable=False)
    description = sa.Column(sa.UnicodeText())
    slug = sa.Column(sa.Unicode(128), nullable=False, index=True, unique=True)
    created_date = sa.Column(sa.DateTime, nullable=False, default=date.now)

    #: this is not the modified date of this object but of the entire project
    #: to give idea of activity
    last_modified_date = sa.Column(sa.DateTime, nullable=False, default=date.now)

    organization = relationship("Organization", backref=backref("projects", cascade="all"))
    organization_id = sa.Column(sa.Integer, sa.ForeignKey('organizations.id'), nullable=False, index=True)
    
    creator = relationship("User", backref=backref("created_projects", cascade="all"))
    creator_id = sa.Column(sa.Integer, sa.ForeignKey('users.id'), nullable=False)

    # no duplicate name inside the same organization, it would be hard
    # to distinguish them
    __table_args__ = (sa.UniqueConstraint('organization_id', 'name'), {})

    def __init__(self, **kwargs):
        super(Project, self).__init__(**kwargs)
        if not self.slug:
            self.slug = get_unique_slug(self.organization, kwargs['name'])

        creator = kwargs.get('creator')
        if creator:
            self.attach_user(creator, PROJECT_ROLE_ADMIN)

    @property
    def last_modified(self):
        """
        Return the most recent last_modified date, wether it is the project metadata change
        or one of the entities in it.
        """
        last_changed_file = Session.query(sa.func.max(Entity.last_modified_date)).filter_by(project=self).first()[0]

        if last_changed_file:
            return max(self.last_modified_date, last_changed_file)
        
        return self.last_modified_date
            
    def __repr__(self):
        return "%s%r" % (self.__class__.__name__, (self.id, self.eid, self.name, self.status, self.slug))
            
    def update_activity(self):
        """
        Whenever the project is changed, the code should also update the
        update the activity datetime on it.
        """
        self.last_modified_date = date.now()

    def deactivate(self):
        """
        Deactivate this project. Since there is a unique contraint in the
        organization_id/name tuple we also rename the project using the
        unique eid.
        """
        self.status = STATUS_INACTIVE
        self.name = "%s-%s" % (self.eid, self.name)
        self.update_activity()

    def get_entities(self, filepath=None, only_type=None, only_status=STATUS_EXISTS, order_by_field=u'last_modified_date', desc=True):
        """
        Get all project entities that have the given path and the given name if any.
        And which status is STATUS_EXISTS.

        Optionally that are at the given path or deeper???.

        Note: It is VERY important that filepath ends with / when you want to
        see a directory, otherwise it's interpreted as a filename.

        /foo/bar/gaz <- is a file (returns 1 result)
        /foo/bar/gaz/ <- is a directory (returns contents)
        """

        q = Session.query(Entity)
        q = q.filter_by(project=self)
        name = None
        if filepath is not None:
            path, name = os.path.split(filepath)
            q = q.filter_by(path=path)
        
        if only_status is not None:
            q = q.filter_by(status=only_status)
            
        if only_type:
            q = q.filter_by(type=only_type)

        if name:
            q = q.filter_by(name=name)
            return q.first()
        
        order_by_field = getattr(Entity, order_by_field, Entity.last_modified_date)

        order_by = sa.asc(order_by_field)
        if desc:
            order_by = sa.desc(order_by_field)

        q = q.order_by(order_by)
        return q.all()

    def get_file(self, filepath):
        """
        Get the file object at the given filepath
        """
        path, name = os.path.split(filepath)

        if not name:
            raise exceptions.AppException("Only one complete path is supported: '%s' given" % (filepath,), code=exceptions.NOT_FOUND)

        return self.get_entities(filepath, File.TYPE)

    def add_change(self, user, filepath, temp_contents_filepath, description):
        """
        Check that file exists, if it does add a Change directly.
        If it doesn't exist, create the File and then add the change.
        """
        file_object = self.get_file(filepath)
        
        if file_object is None:
            path, name = os.path.split(filepath)
            file_object = File(path=path,
                               name=name,
                               project=self)
            Session.add(file_object)

        return file_object.add_change(user, temp_contents_filepath, description)
    
    def add_directory(self, user, path):
        """
        Check if dir exists, if so return it. If not create dir.
        """
        dir_object = self.get_entities(path, only_type=Directory.TYPE)
        
        if dir_object:
            return dir_object
        
        path, name = os.path.split(path)
        dir_object = Directory(path=path,
                           name=name,
                           project=self)
        Session.add(dir_object)

        return dir_object
    
    def get_changes(self, filepath):
        """
        Retrieve all the changes to the filepath given related to this project
        """
        file_object = self.get_file(filepath)

        if not file_object:
            return []

        return file_object.get_changes()
    
    ##
    ### User connection stuff
    
    def get_role(self, user, status=STATUS_APPROVED):
        org_role = self.organization.get_role(user)
        if not org_role: return None
        
        #we prolly should standardize roles in the model...
        # this is technically an organization role, but they are the same string.
        if org_role == PROJECT_ROLE_ADMIN: return PROJECT_ROLE_ADMIN
        
        orgu = self.get_project_user(user, status)
        if orgu:
            return orgu.role
        else:
            if self.organization.is_read_open:
                return PROJECT_ROLE_READ
        return None
    
    def set_role(self, user, role):
        """
        Sets a role on an existing user.
        
        Maybe this should implicitly add a user?
        """
        orgu = self.get_project_user(user)
        if orgu:
            orgu.role = role
            return True
        return False
    
    def get_project_user(self, user, status=STATUS_APPROVED):
        """
        Find a single user's membership within this org
        """
        q = Session.query(ProjectUser).filter(ProjectUser.user_id==user.id)
        if status:
            q = q.filter(ProjectUser.status==status)
        return q.filter(ProjectUser.project_id==self.id).first()
    
    def get_project_users(self, status=None):
        """
        Get all memberships in this org.
        """
        q = Session.query(ProjectUser).filter(ProjectUser.project_id==self.id)
        if status and isinstance(status, basestring):
            q = q.filter(ProjectUser.status==status)
        if status and isinstance(status, (list, tuple)):
            q = q.filter(ProjectUser.status.in_(status))
        return q.all()
    
    def attach_user(self, user, role=PROJECT_ROLE_READ, status=STATUS_APPROVED):
        org_user = Session.query(ProjectUser) \
                    .filter(ProjectUser.project==self) \
                    .filter(ProjectUser.user==user).first()
        if org_user:
            org_user.role = role
            org_user.status = status
            return org_user
        
        org_user = ProjectUser(user=user, project=self, role=role, status=status)
        Session.add(org_user)
        return org_user
    
    def remove_user(self, user):
        q = Session.query(ProjectUser).filter(ProjectUser.project_id==self.id)
        q = q.filter(ProjectUser.user_id==user.id)
        orgu = q.first()
        if orgu:
            Session.delete(orgu)
            return True
        return False

class Entity(Base):
    """
    An Entity contained in a project
    """
    __tablename__ = "entities"
    
    id = sa.Column(sa.Integer, primary_key=True)
    eid = sa.Column(sa.String(22), default=utils.uuid, nullable=False, unique=True)

    status = sa.Column(sa.String(16), nullable=False, default=STATUS_EXISTS)
    type = sa.Column(sa.String(1), nullable=False)
    path = sa.Column(sa.UnicodeText(), nullable=False)
    name = sa.Column(sa.UnicodeText(), nullable=False)
    
    description = sa.Column(sa.UnicodeText())
    #: this is not the modified date of this object but of the entire set of changes
    #: to give idea of activity
    last_modified_date = sa.Column(sa.DateTime, nullable=False, default=date.now)

    project = relationship("Project", backref=backref("entities", cascade="all"))
    project_id = sa.Column(sa.Integer, sa.ForeignKey('projects.id'), nullable=False, index=True)

    __table_args__ = (sa.UniqueConstraint('path', 'name', 'project_id', 'type'), {})
    __mapper_args__ = {'polymorphic_on': type}

    def __repr__(self):
        return "%s%r" % (self.__class__.__name__, (self.id, self.eid, self.project_id, self.path, self.name, self.status))

    @property
    def full_path(self):
        return os.path.join(self.path, self.name)
    
    def update_activity(self):
        """
        Whenever the project is changed, the code should also update the
        update the activity datetime on it.
        """
        self.last_modified_date = date.now()
        #self.project.update_activity()
    
    def _create_parent_directories(self):
        """
        Check if the parent directory exists and if it doesn't create it.

        self.path is the path part of the full filepath already so name
        here is actually the name of the directory.
        """
        path = self.path.lstrip("/")

        if not path:
            # if path is '' then there's no parent to create because
            # we are at root.
            return

        segments = path.split(u"/")
        current_path = u"/"
        for segment in segments:

            q = Session.query(Directory)
            q = q.filter_by(path=current_path)
            q = q.filter_by(name=segment)
            directory = q.first()

            if not directory:
                directory = Directory(path=current_path, name=segment, project=self.project)
                Session.add(directory)

            current_path = directory.full_path

    @property
    def readable_name(self):
        """
        We mangle the name upon delete to avoid multiple entities with the same
        name. Using this we remove that mangling in order to render it to the
        user.
        """
        if self.status == STATUS_REMOVED:
            return self.name.split(u"-", 1)[1]
        return self.name

    def delete(self):
        """
        Delete an existing entity from the system.
        """
        if self.status == STATUS_REMOVED:
            return
        self.status = STATUS_REMOVED
        self.name = "%s-%s" % (self.eid, self.name)
        self.update_activity()

    def undelete(self):
        """
        Undelete an entity that was previously deleted from the system.
        """
        if self.status == STATUS_EXISTS:
            return

        self.status = STATUS_EXISTS
        self.name = self.name.split(u"-", 1)[1]
        self.update_activity()
        
        
class Directory(Entity):
    """
    A directory, mainly used to display directories and ease the querying.

    Doesn't really have any functionality except fetching files that are
    inside it and helping in navigating a source tree.
    """
    TYPE = u'd'
    __mapper_args__ = {'polymorphic_identity': TYPE}
    
class File(Entity):
    """
    A File is the basic unit of each project
    """
    TYPE = u'f'
    __mapper_args__ = {'polymorphic_identity': TYPE}
    _comment_attribute = 'file'

    def __init__(self, *args, **kwargs):
        super(File, self).__init__(*args, **kwargs)
        self._create_parent_directories()
        
    def get_changes(self):
        """
        Fetch change for this file.
        """
        q = Session.query(Change)
        q = q.filter_by(entity=self)
        q = q.filter_by(project=self.project)
        q = q.order_by(sa.desc(Change.version))
        return q.all()
    
    def get_change(self, version=None):
        """
        Fetch single change for this file.
        """
        q = Session.query(Change)
        q = q.filter_by(entity=self)
        q = q.filter_by(project=self.project)
        
        #get HEAD if no change eid specified.
        if version:
            q = q.filter_by(version=version)
        else:
            q = q.order_by(sa.desc(Change.version))
        
        return q.first()
    
    def add_change(self, user, temp_contents_filepath, description):
        """
        Introduce a new change in the given changeset using the file stored
        at temp_contents_filepath with the given description for the change.
        """
        size = 0
        if temp_contents_filepath:
            size = os.stat(temp_contents_filepath).st_size

        change = Change(description=description,
                        size=size,
                        entity=self,
                        project=self.project,
                        creator=user)
        Session.add(change)
        Session.flush()
        change.set_contents(temp_contents_filepath)
        self.update_activity()
        return change
    
    def get_comments(self):
        """
        Get the comments associated with this change(_extract).
        """
        q = Session.query(Comment)
        q = q.filter_by(status=STATUS_EXISTS)
        q = q.join(Change)
        q = q.filter(Change.entity_id==self.id)
        q = q.order_by(sa.asc(Comment.created_date))
        return q.all()

class Uploadable(object):
    """
    This is a base class so I can use uploading junk in the change extract too.
    I do not care about the name. If you dont like it, feel free to change.
    """
    
    _uploaders = {
        'file': fu.LocalUploader,
        's3': fu.S3Uploader
    }

    @property
    def uploader(self):
        """
        Get the proper uploader given the current configuration in ini files.
        """
        from pylons import config
        files_storage = config['files_storage']
        url = urlparse.urlsplit(files_storage)
        return self._uploaders[url.scheme](files_storage)

class Commentable(object):
    """
    Share the code to comment on a Change or ChangeExtract and use _comment_attribute
    to indicate the field in the Comment that references back to the subclass.
    """
    _comment_attribute = None

    def add_comment(self, user, body, x=None, y=None, width=None, height=None, in_reply_to=None):
        """
        Add a new comment to this ChangeExtract.
        """
        comment = Comment(creator=user, body=body, x=x, y=y, width=width, height=height, in_reply_to=in_reply_to, **{self._comment_attribute: self})
        Session.add(comment)
        return comment

    def get_comments(self):
        """
        Get the comments associated with this change(_extract).
        """
        q = Session.query(Comment)
        q = q.filter_by(status=STATUS_EXISTS)
        q = q.filter_by(**{self._comment_attribute: self})
        q = q.order_by(sa.asc(Comment.created_date))
        return q.all()

    
class Change(Base, Uploadable, Commentable):
    """
    Every single change to a File through a changeset is also added to this table
    to query them later when the user needs to see the history of changes to a
    specific file.
    """
    __tablename__ = "changes"
    _comment_attribute = "change"

    id = sa.Column(sa.Integer, primary_key=True)
    eid = sa.Column(sa.String(22), default=utils.uuid, nullable=False, unique=True)
    status = sa.Column(sa.String(16), nullable=False, default=STATUS_EXISTS)

    description = sa.Column(sa.UnicodeText())
    created_date = sa.Column(sa.DateTime, nullable=False, default=date.now)
    size = sa.Column(sa.Integer(), nullable=False, default=0)
    diff_size = sa.Column(sa.Integer(), nullable=False, default=0)
    version = sa.Column(sa.Integer(), nullable=False)
    
    entity = relationship("File", backref=backref("changes", cascade="all"))
    entity_id = sa.Column(sa.Integer, sa.ForeignKey('entities.id'), nullable=False, index=True)

    project = relationship("Project", backref=backref("changes", cascade="all"))
    project_id = sa.Column(sa.Integer, sa.ForeignKey('projects.id'), nullable=False, index=True)

    creator = relationship("User", backref=backref("created_changes", cascade="all"))
    creator_id = sa.Column(sa.Integer, sa.ForeignKey('users.id'), nullable=False)

    __table_args__ = (sa.UniqueConstraint('entity_id', 'project_id', 'version'), {})
    
    def __init__(self, *args, **kwargs):
        version = kwargs.get('version', None)
        super(Change, self).__init__(*args, **kwargs)

        if version is None:
            version = self._get_next_version()

        self.version = version

    def _get_next_version(self):
        """
        Retrieve the next version for this change.
        """
        current_head = self.entity.get_change()
        if current_head:
            return current_head.version + 1
        return 1
        
    def _get_base_url_path(self):
        """
        Base url for diff and change payloads. Files are organized in a tree like this:

        files/  ORGANIZATION_EID   /   PROJECT_EID   /   FILE_EID   /
        """
        return "/".join(["files",
                        self.entity.project.organization.eid,
                        self.entity.project.eid,
                        self.entity.eid])
    
    @property
    def number_comments(self):
        return self.get_number_comments()
    
    def get_number_comments(self, status=None):
        if not status:
            return Session.query(sa.func.count(Comment.id)).filter_by(change_id=self.id).first()[0]
        
        
        date = Session.query(func.max(CommentStatus.created_date).label('date')).filter(CommentStatus.comment_id==Comment.id)
        date = date.group_by(CommentStatus.comment_id)
        
        q = Session.query(func.count(Comment.id)).outerjoin(CommentStatus)
        q = q.filter(Comment.change_id==self.id).filter(Comment.status!=STATUS_REMOVED)
        q = q.filter(Comment.in_reply_to_id==None)
        
        if status == STATUS_OPEN:
            q = q.filter(sa.or_(
                CommentStatus.id==None,
                sa.and_(CommentStatus.created_date==date.subquery().columns.date, CommentStatus.status==status)
            ))
            print q
            return q.scalar()
        else:
            q = q.filter(
                sa.and_(CommentStatus.created_date==date.subquery().columns.date, CommentStatus.status==status)
            )
            print q
            return q.scalar()
    
    @property
    def url(self):
        """
        The url/path to the specific File change recorded in history.

        Inside the specific file directory every change uses its eid and the
        extension of the File that it is part of.

        Note: if you change the extension of the file, all of the past
        revisions will be lost since we rely on the ext to never change.
        A different file extension requires a different file.
        """
        path = self._get_base_url_path()
        ext = os.path.splitext(self.entity.name)[1]
        return "/".join([path, self.eid]) + ext

    @property
    def diff_url(self):
        """
        Use name mangling to get binary diff from last revision
        """
        path = self._get_base_url_path()
        return "/".join([path, self.eid]) + ".diff"

    @property
    def thumbnail_url(self):
        """
        Use name mangling to get the thumbnail url
        
        Note that this simply matches up with that in the corresponding ChangeExtract
        object. Thumbnails are stored as change extracts, and they are stored with the
        format <type>-<order_index>-<change_eid>.png
        """
        path = self._get_base_url_path()
        return "/".join([path, "thumbnail-0-" + self.eid]) + ChangeExtract.ext
        
    def set_contents(self, tmp_contents_filepath):
        """
        Upload the changed file to its location, generate a diff if it's not.
        """
        
        self.uploader.set_contents(tmp_contents_filepath, self.url)
        
        #doing this inline for now. At some point this will be split out and done async
        self._gen_extracts(self.url)
    
    def _gen_extracts(self, tmp_contents_filepath):
        """
        Will generate the file extracts for this change. The extracts include the thumbnail.
        
        This will eventually be async.
        """
        
        #this is really ghetto.
        if not is_testing():
            import subprocess
            commit()
            proj_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            cmd = [
                'python',
                os.path.join(proj_root, 'desio', 'backend', 'run_extract.py'),
                os.path.join(proj_root, 'development.ini'),
                self.eid,
                os.path.join(self.uploader.base_path, tmp_contents_filepath)
            ]
            subprocess.call(cmd)
        else:
            #not running this as an external process so we dont have to commit.
            from desio.backend import run_extract
            print 'Generating extracts for testing env'
            run_extract.gen_extracts(self, os.path.join(self.uploader.base_path, tmp_contents_filepath))
    
class ChangeExtract(Base, Uploadable, Commentable):
    """
    Every file can have extra data attached to them, for example a .png
    could be exploded to multiple files. One specific page is identified
    via Change.eid + FileExtra.order_index inside the original file.
    """
    __tablename__ = "change_extracts"
    _comment_attribute = "change_extract"
    
    id = sa.Column(sa.Integer, primary_key=True)

    order_index = sa.Column(sa.Integer, nullable=False)
    extract_type = sa.Column(sa.Unicode(64), nullable=False)
    description = sa.Column(sa.UnicodeText())
    
    change = relationship("Change", backref=backref("change_extracts", cascade="all"))
    change_id = sa.Column(sa.Integer, sa.ForeignKey('changes.id'), nullable=False, index=True)
    
    #right now, all extracts have a png type.
    ext = '.png'
    
    def __repr__(self):
        return '%s(%s, %s, %s)' % (self.__class__.__name__, self.id, self.order_index, self.extract_type)
    @property
    def project(self):
        return self.change.project
    
    def _get_base_url_path(self):
        """
        Base url for diff and change payloads. Files are organized in a tree like this:

        files/  ORGANIZATION_EID   /   PROJECT_EID   /   FILE_EID   /
        
        Ben sez: feel free to move these. I didnt know what you had in mind for structure.
        Note: this is quite a few queries to get a path :/
        """
        return "/".join(["files",
                        self.change.entity.project.organization.eid,
                        self.change.entity.project.eid,
                        self.change.entity.eid])
    
    def add_comment(self, user, body, **kw):
        """
        Add a new comment to this ChangeExtract.
        """
        comment = super(ChangeExtract, self).add_comment(user, body, **kw)
        
        #we need to set this so we can pull all comments for a specific change
        comment.change = self.change
        
        return comment
    
    @property
    def url(self):
        """
        The url/path to the specific File change recorded in history.

        Inside the specific file directory every change uses its eid and the
        extension of the File that it is part of.

        Note: if you change the extension of the file, all of the past
        revisions will be lost since we rely on the ext to never change.
        A different file extension requires a different file.
        """
        path = self._get_base_url_path()
        return "/".join([path, "%s-%d-%s" % (self.extract_type, self.order_index, self.change.eid)]) + self.ext
    
    def set_contents(self, tmp_contents_filepath):
        """
        Url is optinal
        """
        self.uploader.set_contents(tmp_contents_filepath, self.url)

class CommentStatus(Base):
    __tablename__ = "comment_statuses"
    
    id = sa.Column(sa.Integer, primary_key=True)
    
    status = sa.Column(sa.String(16), nullable=False, default=STATUS_OPEN)

    created_date = sa.Column(sa.DateTime, nullable=False, default=date.now)
    
    user = relationship("User", backref=backref("comment_statuses", cascade="all"))
    user_id = sa.Column(sa.Integer, sa.ForeignKey('users.id'), nullable=False, index=True)

    comment = relationship("Comment", backref=backref("comment_statuses", cascade="all"))
    comment_id = sa.Column(sa.Integer, sa.ForeignKey('comments.id'), index=True)
    

class Comment(Base):
    __tablename__ = "comments"
    
    id = sa.Column(sa.Integer, primary_key=True)
    eid = sa.Column(sa.String(22), default=utils.uuid, nullable=False, unique=True)
    
    status = sa.Column(sa.String(16), nullable=False, default=STATUS_EXISTS)

    x = sa.Column(sa.Integer)
    y = sa.Column(sa.Integer)
    width = sa.Column(sa.Integer)
    height = sa.Column(sa.Integer)
    
    body = sa.Column(sa.UnicodeText(), nullable=False)
    created_date = sa.Column(sa.DateTime, nullable=False, default=date.now)
    edit_date = sa.Column(sa.DateTime, nullable=False, default=date.now, onupdate=date.now)
    
    creator = relationship("User", backref=backref("created_comments", cascade="all"))
    creator_id = sa.Column(sa.Integer, sa.ForeignKey('users.id'), nullable=False, index=True)

    change = relationship("Change", backref=backref("comments", cascade="all"))
    change_id = sa.Column(sa.Integer, sa.ForeignKey('changes.id'), index=True)

    change_extract = relationship("ChangeExtract", backref=backref("comments", cascade="all"))
    change_extract_id = sa.Column(sa.Integer, sa.ForeignKey('change_extracts.id'), index=True)

    in_reply_to = relationship("Comment", backref=backref("replies", cascade="all"), remote_side="Comment.id")
    in_reply_to_id = sa.Column(sa.Integer, sa.ForeignKey('comments.id'), nullable=True, index=True)
    
    @property
    def project(self):
        return self.change.project
    
    @property
    def completion_status(self):
        """
        Users can 'complete' comments.
        
        This will get the most recent row from CommentStatus.
        Should be either 'open' or 'completed'
        """
        cs = Session.query(CommentStatus).filter_by(comment_id=self.id).order_by(sa.desc(CommentStatus.created_date)).first()
        if not cs:
            #create a default
            cs = CommentStatus(user=self.creator, created_date=self.created_date, status=STATUS_OPEN, comment=self)
            Session.add(cs)
            Session.flush()
        return cs
    
    def set_completion_status(self, user, status):
        cs = CommentStatus(user=user, status=status, comment=self)
        Session.add(cs)
        return cs
    
    @property
    def position(self):
        """
        Return a 4-tuple with x, y, width, height that can be used to draw a rectangle.

        If x or y are None it actually returns None because no rectangle can be drawn.

        If width and height are None but not x, y it returns predefined width/height
        """
        if self.x is None or self.y is None:
            return None

        if self.width is None or self.height is None:
            return (self.x, self.y, 50, 50)

        return self.x, self.y, self.width, self.height
    
    def delete(self):
        """
        Soft deletes a comment.
        """
        self.status = STATUS_REMOVED
