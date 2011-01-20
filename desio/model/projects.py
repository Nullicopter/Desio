import sqlalchemy as sa
from sqlalchemy.orm import relationship, backref

from desio.model.meta import Session, Base
import hashlib

from pylons_common.lib import exceptions, date, utils
from desio.model import users, STATUS_OPEN, STATUS_COMPLETED, STATUS_INACTIVE

class Project(Base):
    """
    A Project represents a revisioned tree of files
    """
    __tablename__ = "projects"
    
    id = sa.Column(sa.Integer, primary_key=True)
    eid = sa.Column(sa.String(22), default=utils.uuid, nullable=False)

    status = sa.Column(sa.Unicode(16), nullable=False, default=STATUS_OPEN)
    name = sa.Column(sa.UnicodeText(), nullable=False)
    description = sa.Column(sa.UnicodeText())
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

    def get_changesets(self, limit=None):
        """
        Returns changesets from most recent to least recent.
        """
        q = Session.query(Changeset)
        q = q.order_by(sa.desc(Changeset.order_index), sa.desc(Changeset.order_index))
        if limit:
            q = q.limit(limit)
        return q

class Changeset(Base):
    """
    A Changeset puts together all the changes to a project that happened
    at the same time and by the same user.
    
    Changesets are ordered by order_index and by creation_date to enable
    the ability to resolve conflicts.
    """
    __tablename__ = "changesets"

    id = sa.Column(sa.Integer, primary_key=True)
    eid = sa.Column(sa.String(22), default=utils.uuid, nullable=False)
    status = sa.Column(sa.Unicode(16), nullable=False, default=STATUS_OPEN)
    order_index = sa.Column(sa.Integer, nullable=False)

    description = sa.Column(sa.UnicodeText())
    created_date = sa.Column(sa.DateTime, nullable=False, default=date.now)

    user = relationship("User", backref=backref("changesets", cascade="all"))
    user_id = sa.Column(sa.Integer, sa.ForeignKey('users.id'), nullable=False, index=True)

    project = relationship("Project", backref=backref("changesets", cascade="all"))
    project_id = sa.Column(sa.Integer, sa.ForeignKey('projects.id'), nullable=False, index=True)

    def add_change(self, filepath, temp_contents_filepath, description):
        """
        Check that file exists, if it does add a Change directly and generate a binary diff.
        
        If it doesn't exist, create the File and then add the change.
        """
        pass
        

class File(Base):
    """
    A File entity contained in a project
    """
    __tablename__ = "files"
    
    id = sa.Column(sa.Integer, primary_key=True)
    eid = sa.Column(sa.String(22), default=utils.uuid, nullable=False)
    
    path = sa.Column(sa.UnicodeText(), nullable=False, default=u"/")
    name = sa.Column(sa.UnicodeText(), nullable=False)
    mimetype = sa.Column(sa.Unicode(128), nullable=False)
    size = sa.Column(sa.Integer(), nullable=False, default=0)
    
    description = sa.Column(sa.UnicodeText())

    project = relationship("Project", backref=backref("files", cascade="all"))
    project_id = sa.Column(sa.Integer, sa.ForeignKey('projects.id'), nullable=False, index=True)

    __table_args__ = (sa.UniqueConstraint('path', 'name', 'project_id'), {})

class Change(Base):
    """
    Every single change to a File through a changeset is also added to this table
    to query them later when the user needs to see the history of changes to a
    specific file.
    """
    __tablename__ = "changes"
    
    id = sa.Column(sa.Integer, primary_key=True)
    eid = sa.Column(sa.String(22), default=utils.uuid, nullable=False)

    description = sa.Column(sa.UnicodeText())
    created_date = sa.Column(sa.DateTime, nullable=False, default=date.now)

    file = relationship("File", backref=backref("changes", cascade="all"))
    file_id = sa.Column(sa.Integer, sa.ForeignKey('files.id'), nullable=False, index=True)

    changeset = relationship("Changeset", backref=backref("changes", cascade="all"))
    changeset_id = sa.Column(sa.Integer, sa.ForeignKey('changesets.id'), nullable=False, index=True)

    @property
    def binary_diff_prev(self):
        "use name mangling to get binary diff from last revision"

    @property
    def binary_diff_next(self):
        "use name mangling to get binary diff to next revision"


class FileExtract(Base):
    """
    Every file can have extra data attached to them, for example a .png
    could be exploded to multiple files. One specific page is identified
    via Change.eid + FileExtra.order_index inside the original file.
    """
    __tablename__ = "file_extracts"
    
    id = sa.Column(sa.Integer, primary_key=True)

    order_index = sa.Column(sa.Integer, nullable=False)
    description = sa.Column(sa.UnicodeText())
    
    change = relationship("Change", backref=backref("file_extracts", cascade="all"))
    change_id = sa.Column(sa.Integer, sa.ForeignKey('changes.id'), nullable=False, index=True)

class Comment(Base):
    __tablename__ = "comments"
    
    id = sa.Column(sa.Integer, primary_key=True)
    eid = sa.Column(sa.String(22), default=utils.uuid, nullable=False)

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

    file_exctract = relationship("FileExtract", backref=backref("comments", cascade="all"))
    file_exctract_id = sa.Column(sa.Integer, sa.ForeignKey('file_extracts.id'), nullable=False, index=True)
