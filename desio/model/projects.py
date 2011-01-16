import sqlalchemy as sa
from sqlalchemy.orm import relationship, backref

from desio.model.meta import Session, Base
import hashlib

from datetime import datetime

from pylons_common.lib import exceptions, date, utils
from desio.model import users

class Project(Base):
    """
    A Project represents a revisioned tree of files
    """
    __tablename__ = "projects"
    
    id = sa.Column(sa.Integer, primary_key=True)
    eid = sa.Column(sa.String(22), default=utils.uuid, nullable=False)

    status = sa.Column(sa.Unicode(16), nullable=False)
    name = sa.Column(sa.UnicodeText(), nullable=False)
    description = sa.Column(sa.UnicodeText())
    created_date = sa.Column(sa.DateTime, nullable=False, default=date.now)

    organization = relationship("Organization", backref=backref("projects", cascade="all"))
    organization_id = sa.Column(sa.Integer, sa.ForeignKey('organizations.id'), nullable=False, index=True)

class Changeset(Base):
    """
    A Changeset puts together all the changes to a project that happened
    at the same time and by the same user.
    """
    __tablename__ = "changesets"

    id = sa.Column(sa.Integer, primary_key=True)
    eid = sa.Column(sa.String(22), default=utils.uuid, nullable=False)

    description = sa.Column(sa.UnicodeText())
    created_date = sa.Column(sa.DateTime, nullable=False, default=date.now)

    user = relationship("User", backref=backref("changesets", cascade="all"))
    user_id = sa.Column(sa.Integer, sa.ForeignKey('users.id'), nullable=False, index=True)

    project = relationship("Project", backref=backref("changesets", cascade="all"))
    project_id = sa.Column(sa.Integer, sa.ForeignKey('projects.id'), nullable=False, index=True)


class ProjectEntity(Base):
    """
    A project entity is either a directory or a file contained in a project.
    It is later specialized in either of the 2 different entities.
    """
    __tablename__ = "project_entities"
    
    id = sa.Column(sa.Integer, primary_key=True)
    eid = sa.Column(sa.String(22), default=utils.uuid, nullable=False)
    
    path = sa.Column(sa.UnicodeText(), nullable=False, default=u"/")
    name = sa.Column(sa.UnicodeText(), nullable=False)
    type = sa.Column(sa.Unicode(16), nullable=False)
    
    description = sa.Column(sa.UnicodeText())

    project = relationship("Project", backref=backref("project_entities", cascade="all"))
    project_id = sa.Column(sa.Integer, sa.ForeignKey('projects.id'), nullable=False, index=True)

    __table_args__ = (sa.UniqueConstraint('path', 'name', 'type', 'project_id'))
    __mapper_args__ = {'polymorphic_on' : type}

class File(ProjectEntity):
    """
    A File entity contained in a project
    """
    __mapper_args__ = {'polymorphic_identity' : u'file'}

class Directory(ProjectEntity):
    """
    A Directory entity contained in a project
    """
    __mapper_args__ = {'polymorphic_identity' : u'directory'}

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

    changeset = relationship("Changeset", backref=backref("changes", cascade="all"))
    changeset_id = sa.Column(sa.Integer, sa.ForeignKey('changesets.id'), nullable=False, index=True)


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
