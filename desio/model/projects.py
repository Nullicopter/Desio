import os
import mimetypes as mt
import urlparse

import sqlalchemy as sa
from sqlalchemy.orm import relationship, backref

from desio.model.meta import Session, Base
import hashlib

from pylons_common.lib import exceptions, date, utils
from desio.model import users, STATUS_OPEN, STATUS_COMPLETED, STATUS_INACTIVE, STATUS_APPROVED
from desio.model import STATUS_EXISTS, STATUS_REMOVED
from desio.utils import file_uploaders as fu

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
    slug = sa.Column(sa.Unicode(128), nullable=False, index=True)
    created_date = sa.Column(sa.DateTime, nullable=False, default=date.now)

    #: this is not the modified date of this object but of the entire project
    #: to give idea of activity
    last_modified_date = sa.Column(sa.DateTime, nullable=False, default=date.now)

    organization = relationship("Organization", backref=backref("projects", cascade="all"))
    organization_id = sa.Column(sa.Integer, sa.ForeignKey('organizations.id'), nullable=False, index=True)

    # no duplicate name inside the same organization, it would be hard
    # to distinguish them
    __table_args__ = (sa.UniqueConstraint('organization_id', 'name'), {})

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

    def get_changesets(self, limit=None):
        """
        Returns changesets from most recent to least recent.
        """
        q = Session.query(Changeset)
        q = q.order_by(sa.desc(Changeset.order_index), sa.desc(Changeset.created_date))
        if limit:
            q = q.limit(limit)

        if limit == 1:
            return q.first()
        return q.all()

    def add_changeset(self, user, description):
        """
        Add a new changeset to the project with the given description
        from the given user.
        """
        last_changeset = self.get_changesets(1)
        if last_changeset and last_changeset.status == STATUS_OPEN:
            raise exceptions.ClientException("Somebody is modifying project %s right now. Wait or Coordinate."  % (self.name,), exceptions.FORBIDDEN)        

        new_order_index = 1
        if last_changeset:
            new_order_index = last_changeset.order_index + 1

        changeset = Changeset(user=user,
                              description=description,
                              order_index=new_order_index,
                              project=self)
        Session.add(changeset)

        self.update_activity()
        return changeset

    def get_file(self, filepath):
        """
        Get a file object given a filepath
        """
        path, name = os.path.split(filepath)

        q = Session.query(File)
        q = q.filter_by(name=name)
        q = q.filter_by(path=path)
        q = q.filter_by(project=self)

        return q.first()

    def get_project_files(self, changeset, path=None):
        """
        Get all project files that have a STATUS_EXISTS or are older than Changeset.

        Optionally that are at the given path or deeper???.
        Maybe I should re-introduce directories too, created when creating Files.
        """
    
    
class Changeset(Base):
    """
    A Changeset puts together all the changes to a project that happened
    at the same time and by the same user.
    
    Changesets are ordered by order_index and by creation_date to enable
    the ability to resolve conflicts.
    """
    __tablename__ = "changesets"

    id = sa.Column(sa.Integer, primary_key=True)
    eid = sa.Column(sa.String(22), default=utils.uuid, nullable=False, unique=True)
    status = sa.Column(sa.Unicode(16), nullable=False, default=STATUS_OPEN)
    order_index = sa.Column(sa.Integer, nullable=False)

    description = sa.Column(sa.UnicodeText())
    created_date = sa.Column(sa.DateTime, nullable=False, default=date.now)

    user = relationship("User", backref=backref("changesets", cascade="all"))
    user_id = sa.Column(sa.Integer, sa.ForeignKey('users.id'), nullable=False, index=True)

    project = relationship("Project", backref=backref("changesets", cascade="all"))
    project_id = sa.Column(sa.Integer, sa.ForeignKey('projects.id'), nullable=False, index=True)

    @property
    def is_open(self):
        """
        Checks whether it's still possible to add new changes to this set.
        """
        return self.status == STATUS_OPEN

    def get_change(self, filepath):
        """
        Retrieve all the changes to this Changeset related to a specific file.
        """
        path, name = os.path.split(filepath)

        q = Session.query(Change)
        q = q.filter_by(changeset=self)
        q = q.join((File, sa.and_(File.name==name, File.path==path)))
        return q.first()
    
    def add_change(self, filepath, temp_contents_filepath, description):
        """
        Check that file exists, if it does add a Change directly.
        If it doesn't exist, create the File and then add the change.
        """
        if not self.is_open:
            raise exceptions.ClientException("You can't modify completed changeset %s."  % (self.eid,), exceptions.FORBIDDEN)        

        path, name = os.path.split(filepath)
        
        file_object = self.project.get_file(filepath)

        if file_object is None:
            mimetype, _ = mimetypes.guess_type(filepath)
            file_object = File(path=path,
                               name=name,
                               mimetype=mimetype,
                               project=self.project)
            Session.add(file_object)

        return file_object.add_change(self, temp_contents_filepath, description)
        
    def complete(self):
        """
        Finalize a changeset by disallowing any more changes
        """
        self.status = STATUS_COMPLETED
        self.project.update_activity()

class Entity(Base):
    """
    An Entity contained in a project
    """
    __tablename__ = "entities"
    
    id = sa.Column(sa.Integer, primary_key=True)
    eid = sa.Column(sa.String(22), default=utils.uuid, nullable=False, unique=True)

    type = sa.Column(sa.String(1), nullable=False)
    path = sa.Column(sa.UnicodeText(), nullable=False)
    name = sa.Column(sa.UnicodeText(), nullable=False)
    mimetype = sa.Column(sa.Unicode(128))
    
    description = sa.Column(sa.UnicodeText())

    project = relationship("Project", backref=backref("entities", cascade="all"))
    project_id = sa.Column(sa.Integer, sa.ForeignKey('projects.id'), nullable=False, index=True)

    __table_args__ = (sa.UniqueConstraint('path', 'name', 'project_id'), {})
    __mapper_args__ = {'polymorphic_on': type}

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

    def __init__(self, *args, **kwargs):
        super(self, File).__init__(*args, **kwargs)
        self._create_parent_directory()

    @property
    def mime_headers(self):
        """
        Return a dictionary containing the mime type headers for HTTP requests.
        """
        
    def _create_parent_directory(self):
        """
        Check if the parent directory exists and if it doesn't create it.
        """
        path, name = os.path.split(self.path)
        q = Session.query(Directory)
        q = q.filter_by(path=path)
        q = q.filter_by(name=name)
        directory = q.first()
        if directory:
            return

        directory = Directory(path=path, name=name, project=self.project)
        Session.add(directory)
        
    def remove(self):
        """
        Remove the file from the repository

        XXX: Super HARD
        """
        change = self.add_change()
        change.status = STATUS_REMOVED
        self.project.update_activity()

    def get_change(self):
        """
        Fetch change for this file.
        """
        
    def add_change(self, changeset, temp_contents_filepath, description):
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
                        changeset=changeset)
        Session.add(change)
        Session.flush()
        change.set_contents(temp_contents_filepath)
        self.project.update_activity()
        return change

class Change(Base):
    """
    Every single change to a File through a changeset is also added to this table
    to query them later when the user needs to see the history of changes to a
    specific file.
    """
    __tablename__ = "changes"
    
    id = sa.Column(sa.Integer, primary_key=True)
    eid = sa.Column(sa.String(22), default=utils.uuid, nullable=False, unique=True)
    status = sa.Column(sa.String(16), nullable=False, default=STATUS_EXISTS)

    description = sa.Column(sa.UnicodeText())
    created_date = sa.Column(sa.DateTime, nullable=False, default=date.now)
    size = sa.Column(sa.Integer(), nullable=False, default=0)
    diff_size = sa.Column(sa.Integer(), nullable=False, default=0)

    entity = relationship("File", backref=backref("changes", cascade="all"))
    entity_id = sa.Column(sa.Integer, sa.ForeignKey('entities.id'), nullable=False, index=True)

    changeset = relationship("Changeset", backref=backref("changes", cascade="all"))
    changeset_id = sa.Column(sa.Integer, sa.ForeignKey('changesets.id'), nullable=False, index=True)

    # You can't change the same file multiple times in the same changeset... doesn't make sense
    __table_args__ = (sa.UniqueConstraint('changeset_id', 'entity_id'), {})

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
        scheme = urlparse.urlsplit(files_storage).scheme
        return self._uploaders[scheme](files_storage)
    
    def _get_base_url_path(self):
        """
        Base url for diff and change payloads. Files are organized in a tree like this:

        files/  ORGANIZATION_EID   /   PROJECT_EID   /   FILE_EID   /
        """
        return "/".join("files",
                        self.entity.project.organization.eid,
                        self.entity.project.eid,
                        self.entity.eid)

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
        ext = os.path.splitext(self.entity.name)
        return "/".join(path, self.eid) + ext

    @property
    def diff_url(self):
        """
        Use name mangling to get binary diff from last revision
        """
        path = self._get_base_url_path()
        return "/".join(path, self.eid) + ".diff"

    @property
    def thumbnail_url(self):
        """
        Use name mangling to get the thumbnail url
        """
        path = self._get_base_url_path()
        ext = os.path.splitext(self.entity.name)
        return "/".join(path, "thumbnail-" + self.eid) + ext
    
    def add_comment(self, body, x=None, y=None, width=None, height=None):
        """
        Add a new comment to this change.
        """

    def set_contents(self, tmp_contents_filepath):
        """
        Upload the changed file to its location, generate a diff if it's not.
        """
        self.uploader.set_contents(tmp_contents_filepath, self.url)
        
class ChangeExtract(Base):
    """
    Every file can have extra data attached to them, for example a .png
    could be exploded to multiple files. One specific page is identified
    via Change.eid + FileExtra.order_index inside the original file.
    """
    __tablename__ = "change_extracts"
    
    id = sa.Column(sa.Integer, primary_key=True)

    order_index = sa.Column(sa.Integer, nullable=False)
    description = sa.Column(sa.UnicodeText())
    
    change = relationship("Change", backref=backref("change_extracts", cascade="all"))
    change_id = sa.Column(sa.Integer, sa.ForeignKey('changes.id'), nullable=False, index=True)

    def add_comment(self, body, x=None, y=None, width=None, height=None):
        """
        Add a new comment to this extract
        """

class Comment(Base):
    __tablename__ = "comments"
    
    id = sa.Column(sa.Integer, primary_key=True)
    eid = sa.Column(sa.String(22), default=utils.uuid, nullable=False, unique=True)

    x = sa.Column(sa.Integer)
    y = sa.Column(sa.Integer)
    width = sa.Column(sa.Integer)
    height = sa.Column(sa.Integer)
    
    body = sa.Column(sa.UnicodeText())
    created_date = sa.Column(sa.DateTime, nullable=False, default=date.now)
    edit_date = sa.Column(sa.DateTime, nullable=False, default=date.now, onupdate=date.now)
    
    user = relationship("User", backref=backref("comments", cascade="all"))
    user_id = sa.Column(sa.Integer, sa.ForeignKey('users.id'), nullable=False, index=True)

    change = relationship("Change", backref=backref("comments", cascade="all"))
    change_id = sa.Column(sa.Integer, sa.ForeignKey('changes.id'), nullable=False, index=True)

    change_exctract = relationship("ChangeExtract", backref=backref("comments", cascade="all"))
    change_exctract_id = sa.Column(sa.Integer, sa.ForeignKey('change_extracts.id'), nullable=False, index=True)