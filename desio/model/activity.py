import sqlalchemy as sa
from sqlalchemy.orm import relation, backref

import pytz
from desio.model.meta import Session, Base
from desio.model import STATUS_COMPLETED, STATUS_OPEN
from desio.utils import to_unicode

from datetime import datetime

from pylons_common.lib import exceptions as ex, date, utils

now = date.now

def project_url(org, project):
    from desio.lib import helpers as h
    return h.subdomain_url(org.subdomain, controller='organization/project', action='view', slug=project.slug)

def file_url(org, project, entity):
    from desio.lib import helpers as h
    return h.subdomain_url(org.subdomain, controller='organization/file', action='view', project=project.eid, file=entity.eid)

def get_activities(organization=None, project=None, entity=None, user=None, limit=None, order_by='created_date', sort_direction='desc'):
    """
    always use this to query activities
    
    - Will be slow due to multiple queries on get_message() call to each activity
    - can do some kind of caching: run through all the activites, get all the user, project, & entity ids,
      query them, put them in a dict. Then override the user, project, entity properties to
      make use of the dict.
    
    - users prolly will want many of the same events (comments?) over a close time span. Can
      do that here.
    """
    q = Session.query(Activity)
    
    if organization:
        q = q.filter_by(organization_id=organization.id)
    
    if project:
        q = q.filter_by(project_id=project.id)
    
    if entity:
        q = q.filter_by(entity_id=entity.id)
    
    if user:
        q = q.filter_by(user_id=user.id)
    
    if limit:
        q = q.limit(limit)
    
    if order_by and sort_direction:
        d = getattr(sa, sort_direction)
        q = q.order_by(d(getattr(Activity, order_by)))
    
    return q.all()
    
class Activity(Base):
    """
    Stores a user's role in an org
    """
    __tablename__ = "activities"

    id = sa.Column(sa.Integer, primary_key=True)
    
    type = sa.Column(sa.Unicode(32), nullable=False)
    extra = sa.Column(sa.Text(), nullable=True)
    
    user = relation("User", backref=backref("activities", cascade="all"))
    user_id = sa.Column(sa.Integer, sa.ForeignKey('users.id'), nullable=False, index=True)
    
    organization = relation("Organization", backref=backref("activities", cascade="all"))
    organization_id = sa.Column(sa.Integer, sa.ForeignKey('organizations.id'), nullable=False, index=True)
    
    project = relation("Project", backref=backref("activities", cascade="all"))
    project_id = sa.Column(sa.Integer, sa.ForeignKey('projects.id'), nullable=True, index=True)
    
    entity = relation("Entity", backref=backref("activities", cascade="all"))
    entity_id = sa.Column(sa.Integer, sa.ForeignKey('entities.id'), nullable=True, index=True)
    
    object_id = sa.Column(sa.Integer, nullable=True, index=False)
    object_type = sa.Column(sa.Unicode(32), nullable=True) #used to pull the object
    
    created_date = sa.Column(sa.DateTime, nullable=False, default=now, index=True)
    
    __mapper_args__ = {'polymorphic_on': type}
    
    JOINT = u'\a'
    
    def __repr__(self):
        return u'%s(%s, org:%s)' % (self.__class__.__name__, self.id, self.organization_id)
    
    def get_message(user=None):
        return '%r %s, p:%s, entity:%s, extra: %s' % (self.user, self.type, self.project_id, self.entity_id, self.extra)
    
    def get_class_for_obj_type(self):
        
        if not getattr(self, '_object_type_map', None):
            from desio.model import projects, users
            self._object_type_map = {
                'Change': projects.Change,
                'Comment': projects.Comment,
                'Invite': users.Invite
            }
        
        return self._object_type_map.get(self.object_type)
    
    @property
    def object(self):
        cls = self.get_class_for_obj_type()
        if cls:
            return Session.query(cls).filter_by(id=self.object_id).first()
        return None
    
    def get_extra_split(self):
        if self.extra:
            return self.extra.split(self.JOINT)
        return self.extra
    
    def set_extra_split(self, v):
        self.extra = self.JOINT.join([to_unicode(a) for a in v])
    
    extra_split = property(get_extra_split, set_extra_split)

class NewProject(Activity):
    
    TYPE = u'new_project'
    __mapper_args__ = {'polymorphic_identity': TYPE}
    
    def __init__(self, user, project):
        super(self.__class__, self).__init__(user=user, project=project, organization=project.organization)
    
    def get_message(self, user=None):
        url = project_url(self.organization, self.project)
        return '%s created new project <a href="%s">%s</a>' % (self.user.human_name, url, self.project.name)

class NewFile(Activity):
    
    TYPE = u'new_file'
    __mapper_args__ = {'polymorphic_identity': TYPE}
    
    def __init__(self, user, entity):
        super(self.__class__, self).__init__(user=user, entity=entity, project=entity.project, organization=entity.project.organization)
    
    def get_message(self, user=None):
        url = project_url(self.organization, self.project)
        furl = file_url(self.organization, self.project, self.entity)
        return '%s uploaded a new file <a href="%s">%s</a> to project <a href="%s">%s</a>' % (
            self.user.human_name, furl, self.entity.name, url, self.project.name)

class NewVersion(Activity):
    
    TYPE = u'new_version'
    __mapper_args__ = {'polymorphic_identity': TYPE}
    
    def __init__(self, user, change):
        super(self.__class__, self).__init__(user=user, entity=change.entity, project=change.entity.project, organization=change.entity.project.organization)
        self.object_id = change.id
        self.object_type = change.__class__.__name__
        
        self.extra = unicode(change.version)
    
    def get_message(self, user=None):
        url = project_url(self.organization, self.project)
        furl = file_url(self.organization, self.project, self.entity)
        return '%s uploaded version %s to file <a href="%s">%s</a> in project <a href="%s">%s</a>' % (
            self.user.human_name, self.extra, furl, self.entity.name, url, self.project.name)

class NewComment(Activity):
    
    TYPE = u'new_comment'
    __mapper_args__ = {'polymorphic_identity': TYPE}
    
    def __init__(self, user, entity, comment):
        super(self.__class__, self).__init__(user=user,
                                             entity=entity,
                                             project=entity.project,
                                             organization=entity.project.organization)
        self.object_id = comment.id
        self.object_type = comment.__class__.__name__
    
    def get_message(self, user=None):
        url = project_url(self.organization, self.project)
        furl = file_url(self.organization, self.project, self.entity)
        return '%s posted a note to file <a href="%s">%s</a> in project <a href="%s">%s</a>: <span class="comment-body">%s</span>' % (
            self.user.human_name, furl, self.entity.name, url, self.project.name, self.object.body)

class NewReply(Activity):
    
    TYPE = u'new_reply'
    __mapper_args__ = {'polymorphic_identity': TYPE}
    
    def __init__(self, user, entity, comment):
        super(self.__class__, self).__init__(user=user,
                                             entity=entity,
                                             project=entity.project,
                                             organization=entity.project.organization)
        self.object_id = comment.id
        self.object_type = comment.__class__.__name__
        
        self.extra_split = [
            comment.in_reply_to.id,
            comment.in_reply_to.body
        ]
    
    def get_message(self, user=None):
        url = project_url(self.organization, self.project)
        furl = file_url(self.organization, self.project, self.entity)
        return '%s posted a reply to a note in <a href="%s">%s</a> in project <a href="%s">%s</a>: <span class="comment-body">%s</span>' % (
            self.user.human_name, furl, self.entity.name, url, self.project.name, self.object.body)


class CommentComplete(Activity):
    
    TYPE = u'comment_complete'
    __mapper_args__ = {'polymorphic_identity': TYPE}
    
    STATUS_MAP = {
        STATUS_OPEN: 'uncompleted',
        STATUS_COMPLETED: 'completed'
    }
    
    def __init__(self, comment_status):
        cs = comment_status
        super(self.__class__, self).__init__(user=cs.user,
                                             entity=cs.comment.change.entity,
                                             project=cs.comment.change.entity.project,
                                             organization=cs.comment.change.entity.project.organization)
        self.object_id = cs.comment.id
        self.object_type = cs.comment.__class__.__name__
        
        self.extra_split = [
            cs.status
        ]
    
    def get_message(self, user=None):
        url = project_url(self.organization, self.project)
        furl = file_url(self.organization, self.project, self.entity)
        return '%s %s note "<span class="comment-body">%s</span>" in <a href="%s">%s</a> in project <a href="%s">%s</a>' % (
            self.user.human_name, self.STATUS_MAP[self.extra_split[0]], self.object.body, furl, self.entity.name, url, self.project.name)

class InviteBase(Activity):
    
    def __init__(self, user, invite):
        from desio.model.users import INVITE_TYPE_ORGANIZATION, INVITE_TYPE_PROJECT, INVITE_TYPE_ENTITY
        
        if invite.type == INVITE_TYPE_ORGANIZATION:
            org = invite.object
            proj = entity = None
        elif invite.type == INVITE_TYPE_PROJECT:
            proj = invite.object
            org = proj.organization
            entity = None
        elif invite.type == INVITE_TYPE_ENTITY:
            entity = invite.object
            proj = entity.project
            org = proj.organization
        
        super(InviteBase, self).__init__(user=user,
                                             entity=entity,
                                             project=proj,
                                             organization=org)
        self.object_id = invite.id
        self.object_type = invite.__class__.__name__
        
        self.extra_split = [
            invite.type,
            invite.invited_email,
            invite.role
        ]
    
    @property
    def invite_str(self):
        from desio.model.users import INVITE_TYPE_ORGANIZATION, INVITE_TYPE_PROJECT, INVITE_TYPE_ENTITY
        
        typ = self.extra_split[0]
        if typ == INVITE_TYPE_ORGANIZATION:
            return '%s' % self.organization.name
        elif typ == INVITE_TYPE_PROJECT:
            url = project_url(self.organization, self.project)
            return 'project <a href="%s">%s</a>' % (url, self.project.name)
        elif typ == INVITE_TYPE_ENTITY:
            url = file_url(self.organization, self.project, self.entity)
            return 'file <a href="%s">%s</a>' % (url, self.entity.name)
        
        return None


class Invite(InviteBase):
    
    TYPE = u'invite'
    __mapper_args__ = {'polymorphic_identity': TYPE}
    
    def get_message(self, user=None):
        return u'%s invited %s to %s with' % (
            self.user.human_name, self.extra_split[1], self.invite_str)

class InviteAccept(InviteBase):
    
    TYPE = u'invite_accept'
    __mapper_args__ = {'polymorphic_identity': TYPE}
    
    def get_message(self, user=None):
        return u'%s accepted the invite to %s' % (
            self.user.human_name, self.invite_str)