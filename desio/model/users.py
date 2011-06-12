import sqlalchemy as sa
from sqlalchemy.orm import relation, backref

import pytz
from desio.model.meta import Session, Base
from desio.model import activity
import hashlib

from datetime import datetime

from pylons_common.lib import exceptions as ex, date, utils
from desio.model import Roleable, STATUS_APPROVED, STATUS_REJECTED, STATUS_PENDING
from desio.model import APP_ROLES, APP_ROLE_ADMIN, APP_ROLE_WRITE, APP_ROLE_READ

ROLE_USER = u'user'
ROLE_ADMIN = u'admin'
ROLE_ENGINEER = u'engineer'
ROLE_ROBOT = u'robot'

INVITE_TYPE_ORGANIZATION = u'organization'
INVITE_TYPE_PROJECT = u'project'
INVITE_TYPE_ENTITY = u'entity'

INVITE_TYPES = [INVITE_TYPE_ORGANIZATION, INVITE_TYPE_PROJECT, INVITE_TYPE_ENTITY]

now = date.now

def short_uuid():
    return utils.uuid()[0:6]

def hash_password(clear_pass):
    """
    Used to encrypt our passwords with our special salt.
    """
    salt = u"c4tsareninjasMeow".encode('utf-8')
    hash = hashlib.md5( salt + clear_pass.encode("utf-8") ).hexdigest()

    return hash.decode('utf-8')

class OrganizationUser(Base):
    """
    Stores a user's role in an org
    """
    __tablename__ = "organization_users"

    id = sa.Column(sa.Integer, primary_key=True)
    
    role = sa.Column(sa.Unicode(16), nullable=False)
    status = sa.Column(sa.Unicode(16), nullable=False)
    
    user = relation("User", backref=backref("organization_users", cascade="all"))
    user_id = sa.Column(sa.Integer, sa.ForeignKey('users.id'), nullable=False, index=True)
    
    organization = relation("Organization", backref=backref("organization_users", cascade="all"))
    organization_id = sa.Column(sa.Integer, sa.ForeignKey('organizations.id'), nullable=False, index=True)
    
    created_date = sa.Column(sa.DateTime, nullable=False, default=now)
    
    def __repr__(self):
        return u'OrganizationUser(%s, org:%s, u:%s)' % (self.id, self.organization_id, self.user_id)

class Organization(Base, Roleable):
    """
    Stores a user preference
    """
    __tablename__ = "organizations"

    id = sa.Column(sa.Integer, primary_key=True)
    eid = sa.Column(sa.Unicode(22), unique=True, default=utils.uuid)
    
    subdomain = sa.Column(sa.Unicode(64), nullable=False)
    name = sa.Column(sa.Text(), nullable=False)
    url = sa.Column(sa.Text(), nullable=True)
    
    is_active = sa.Column(sa.Boolean(), default=True)
    
    # does everyone in the org have read access to all projects?
    is_read_open = sa.Column(sa.Boolean(), default=True)
    
    #user is the creator
    creator = relation("User", backref=backref("created_organizations"))
    creator_id = sa.Column(sa.Integer, sa.ForeignKey('users.id'), nullable=False)
    
    created_date = sa.Column(sa.DateTime, nullable=False, default=now)
    updated_date = sa.Column(sa.DateTime, nullable=False, onupdate=now, default=now)
    
    connection_class = OrganizationUser
    object_name = 'organization'
    
    def __repr__(self):
        return u'Organization(%s, %s)' % (self.id, self.subdomain)
    
    def get_role(self, user, status=STATUS_APPROVED):
        if user == self.creator: return APP_ROLE_ADMIN
        
        orgu = self.get_user_connection(user, status)
        if orgu:
            return orgu.role
        return None
    
    def remove_user(self, user):
        if user == self.creator:
            raise ex.ClientException('You cannot remove the organization creator.', ex.INVALID)
        
        super(Organization, self).remove_user(user)
    
    def attach_user(self, user, role=APP_ROLE_READ, status=STATUS_PENDING):
        return super(Organization, self).attach_user(user, role=role, status=status)
    
    def get_user_connection(self, user, status=None):
        return super(Organization, self).get_user_connection(user, status=status)
    
    def get_projects(self, user):
        from desio.model import projects
        q = Session.query(projects.Project).filter_by(organization=self, status=STATUS_APPROVED)
        
        # this is kind of hairy. If org.is_read_open, the user can see all projects, otherwise,
        # we get based on connections
        
        #if not self.is_read_open and self.get_role(user) != APP_ROLE_ADMIN:
        #    q = q.join(projects.ProjectUser).filter(sa.and_(projects.ProjectUser.user==user, projects.ProjectUser.status==STATUS_APPROVED))
        
        projects = q.order_by(sa.desc(projects.Project.last_modified_date)).all()
        
        #this will return all the projects the user can see
        return [p for p in projects if p.get_role(user)]
    
    @property
    def interested_users(self):
        cus = self.get_user_connections(status=STATUS_APPROVED)
        return [cu.user for cu in cus if cu.user]
    
    def get_invites(self, status=STATUS_PENDING, has_user=None):
        q = Session.query(Invite).filter_by(object_id=self.id, type=INVITE_TYPE_ORGANIZATION)
        if has_user == False:
            q = q.filter(Invite.invited_user_id==None)
        if has_user == True:
            q = q.filter(Invite.invited_user_id!=None)
        
        q = q.filter(Invite.status.in_([status]))
        q = q.order_by(sa.desc(Invite.created_date))
        
        return q.all()

class UserPreference(Base):
    """
    Stores a user preference
    """
    __tablename__ = "user_preferences"

    id = sa.Column(sa.Integer, primary_key=True)
    
    key = sa.Column(sa.Unicode(64), nullable=False, index=True)
    value = sa.Column(sa.Unicode(64))
    
    user = relation("User", backref=backref("preferences", cascade="all"))
    user_id = sa.Column(sa.Integer, sa.ForeignKey('users.id'), nullable=False)
    
    def __repr__(self):
        return u'UserPreference(%s, u: %s, k: %s, v: %s)' % (self.id, self.user_id, self.key, self.value)

class User(Base):

    __tablename__ = "users"

    id = sa.Column(sa.Integer, primary_key=True)

    email = sa.Column(sa.Unicode(256), unique=True, index=True, nullable=False)
    #: Phone number
    phone = sa.Column(sa.Unicode(25), nullable=True)
    #: User entered nickname, required maximum 64 characters
    _username = sa.Column("username", sa.Unicode(64), unique=True, index=True, nullable=False)
    _display_username = sa.Column("display_username", sa.Unicode(64), unique=True, index=True, nullable=False)
    #: The encrypted version of the password
    _password = sa.Column("password", sa.UnicodeText(), nullable=False)
    #: One of [ROLE_ADMIN, ROLE_ENGINEER, ROLE_OPS, ROLE_USER]
    role = sa.Column(sa.Unicode(30), nullable=False, default=u'user', index=True)
    #: Is True unless an Admin has deactivated this user, which prevents them
    #: from using the site.
    is_active = sa.Column(sa.Boolean, nullable=False, default=True)
    #: User entered first name, maximum 64 characters
    first_name = sa.Column(sa.Unicode(100))
    #: User entered last name, maximum 64 characters
    last_name = sa.Column(sa.Unicode(100))
    #: The name of the user's timezone, should be a pytz timezone name
    default_timezone = sa.Column(sa.Unicode(40), nullable=False, default=u'US/Pacific')
    #: Date of last login, UTC
    last_login_date = sa.Column(sa.DateTime)
    created_date = sa.Column(sa.DateTime, nullable=False, default=now)
    updated_date = sa.Column(sa.DateTime, nullable=False, onupdate=now, default=now)
  
    preferences_defaults = {}

    def _ppassword():
        def fset(self, value):
            self._password = hash_password(value)

        def fget(self):
            return self._password
        return locals()
    password = sa.orm.synonym('_password', descriptor=property(**_ppassword()))
    
    def _pusername():
        def fset(self, value):
            self._username = value.lower()
            self.display_username = value

        def fget(self):
            return self._username
        return locals()
    username = sa.orm.synonym('_username', descriptor=property(**_pusername()))

    def _pdisplay_username():
        def fset(self, value):
            self._display_username = value

        def fget(self):
            if self._display_username is None:
                self._display_username = self.username
            return self._display_username
        return locals()
    display_username = sa.orm.synonym('_display_username', descriptor=property(**_pdisplay_username()))

    def __repr__(self):
        return "%s(%r,%r)" % (self.__class__.__name__, self.id, self.username)

    def _load_prefs(self):
        if not hasattr(self, 'preferences_dict') or not self.preferences_dict:
            self.preferences_dict = {}
            for pref in self.preferences:
                self.preferences_dict[pref.key] = pref
    
    def thumbnail_url(self, size=32):
        import urllib, hashlib, pylons
        
        default = pylons.config.get('pylons_url') + '/i/icons/default_user.png'
        
        # construct the url
        gravatar_url = "http://www.gravatar.com/avatar/" + hashlib.md5(self.email.lower()).hexdigest() + "?"
        gravatar_url += urllib.urlencode({'d':default, 's':str(size)})
        
        return gravatar_url

    @property
    def human_name(self):
        if self.first_name and self.last_name:
            return '%s %s' % (self.first_name, self.last_name)
        return self.username
    
    def get_preference(self, key, default=None, ignore_default=False):
        """
        Gets a user's preference.
        
        :param key: A string key to retrieve the value of
        :param ignore_default: Will return None on key not found instead of the
        default.
        """
        self._load_prefs()
        
        if key in self.preferences_dict:
            return self.preferences_dict[key].value
        
        if default != None:
            return default
        
        if not ignore_default:
            if key in self.preferences_defaults:
                return self.preferences_defaults[key]
        
        return None
    
    def set_preference(self, key, val):
        """
        Sets a user's preference 
        """
        self._load_prefs()
        if key in self.preferences_dict:
            self.preferences_dict[key].value = val
            pref = self.preferences_dict[key]
        else:
            pref = UserPreference(key=key, value=val, user=self)
            Session.add(pref)
            self.preferences_dict[key] = pref
        return pref

    def does_password_match(self, password):
        """
        Returns True if the given password matches the stored password.

        :param password: The password to test whether it matches.
        """
        return hash_password(password) == self._password
    
    def is_admin(self):
        return self.role in [ROLE_ADMIN]
    def is_robot(self):
        return self.role in [ROLE_ROBOT]
    
    def deactivate(self):
        """
        """
        self.is_active = False
    
    def set_timezone_int(self, timez):
        timezones = date.get_timezones()
        hours = int(timez)
        # adjust for offsets that are greater than 12 hours (these are repeats of other offsets)
        if hours > 12:
            hours = hours - 24
        # also, -12 is a repeat of +12
        elif hours < -11:
            hours = hours + 24
        self.default_timezone = timezones[hours]
    
    def as_local_time(self, dt=None):
        """
        Returns the given datetime in user's local timezone. If none is given
        it returns the current datetime in the user's timezone.

        :param dt: The datetime in UTC to convert to the user's timezone.
        """
        if dt:
            # we assume we're given a utc time - can't know otherwise at this point
            dt = dt.replace(tzinfo=pytz.utc)
            return dt.astimezone(pytz.timezone(self.default_timezone))

        return dt
    
    def local_offset(self):
        """
        Returns the number of hours offset this user is from UTC.
        """
        aware_now = now().replace(tzinfo=pytz.timezone(self.default_timezone))
        offset = self.as_local_time(now()).hour - aware_now.hour
        if offset > 12:
            offset = offset - 24
        elif offset < -11:
            offset = offset + 24
        return offset
    
    def get_organizations(self, status=STATUS_APPROVED):
        """
        Orgs explicitly attached to.
        """
        orgs = Session.query(Organization).filter_by(creator=self).all()
        return list(set([r.organization for r in self.get_user_connections(status=status)] + orgs))
    
    def get_projects(self, status=STATUS_APPROVED):
        """
        projects explicitly attached to.
        """
        return [r.project for r in self.get_project_users(status=status)]
    
    def get_entities(self, status=STATUS_APPROVED):
        """
        Entities explicitly attached to.
        """
        return [r.entity for r in self.get_entity_users(status=status)]
    
    def get_user_connections(self, status=STATUS_APPROVED):
        q = Session.query(OrganizationUser).filter(OrganizationUser.user_id==self.id)
        if status:
            q = q.filter(OrganizationUser.status==status)
        return q.all()
    
    def get_project_users(self, status=STATUS_APPROVED):
        from desio.model import projects
        q = Session.query(projects.ProjectUser).filter(projects.ProjectUser.user_id==self.id)
        if status:
            q = q.filter(projects.ProjectUser.status==status)
        return q.all()
    
    def get_entity_users(self, status=STATUS_APPROVED):
        from desio.model import projects
        q = Session.query(projects.EntityUser).filter(projects.EntityUser.user_id==self.id)
        if status:
            q = q.filter(projects.EntityUser.status==status)
        return q.all()
    
    def must_own(self, *things):
        if self.is_admin():
            return True
        for thing in things:
            if thing and not self.owns(thing):
                raise ex.ClientException("User must be an admin or else own this %s." % thing.__class__.__name__, ex.FORBIDDEN)
    
    def owns(self, thing):
        """
        Does the user own the given thing, or not.
        """
        if not thing:
            return False
        if hasattr(thing, 'user_id'):
            return self.id == thing.user_id
        if hasattr(thing, 'creator_id'):
            return self.id == thing.creator_id
        elif isinstance(thing, list):
            for item in thing:
                if not self.owns(item):
                    return False
            return True
        return False

class Invite(Base):
    """
    Stores an invite to a user.
    """
    __tablename__ = "invites"

    id = sa.Column(sa.Integer, primary_key=True)
    eid = sa.Column(sa.Unicode(22), unique=True, default=utils.uuid)
    
    role = sa.Column(sa.Unicode(16), nullable=False)
    status = sa.Column(sa.Unicode(16), nullable=False)
    type = sa.Column(sa.Unicode(16), nullable=False, index=True)
    
    user_id = sa.Column(sa.Integer, sa.ForeignKey('users.id'), nullable=False, index=True)
    user = relation("User", primaryjoin=user_id==User.id, backref=backref("sent_invites", cascade="all"))    
    
    invited_user_id = sa.Column(sa.Integer, sa.ForeignKey('users.id'), nullable=True, index=True)
    invited_user = relation("User", primaryjoin=invited_user_id==User.id, backref=backref("received_invites", cascade="all"))
    
    invited_email = sa.Column(sa.Unicode(256), index=True, nullable=False)
    
    #any project, org, or entity id
    object_id = sa.Column(sa.Integer, nullable=False, index=True)
    
    created_date = sa.Column(sa.DateTime, nullable=False, default=now)
    
    def __init__(self, *args, **kw):
        super(Invite, self).__init__(*args, **kw)
        
        self._setup_lookups()
        self._object = None
    
    def __repr__(self):
        return u'Invite(%s, u:%r, invited:%s, to:%s%s)' % (self.id, self.user, self.invited_email, self.type, self.object_id)
    
    @classmethod
    def _setup_lookups(cls):
        from desio.model import projects
        cls.fetch_types = {
            INVITE_TYPE_ORGANIZATION: Organization,
            INVITE_TYPE_PROJECT: projects.Project,
            INVITE_TYPE_ENTITY: projects.Entity
        }
        
        cls.put_types = {
            Organization.__name__: INVITE_TYPE_ORGANIZATION,
            projects.Project.__name__: INVITE_TYPE_PROJECT,
            projects.File.__name__: INVITE_TYPE_ENTITY,
            projects.Directory.__name__: INVITE_TYPE_ENTITY
        }
    
    @classmethod
    def create(cls, user, email, obj, role=APP_ROLE_READ):
        """
        Invites a user to an object.
        
        Params are supposed to be:
            user invites email to obj with role
        
        This will find the user if he already exists.
        """
        cls._setup_lookups()
        
        if role not in APP_ROLES:
            raise ex.AppException('Check your role(%s) param' % (type, role), ex.INVALID)
        
        if not obj or not user or type(obj).__name__ not in cls.put_types:
            raise ex.AppException('Check your user and org params. They must not be None.' % (type, role), ex.INVALID)
        
        type_ = cls.put_types[type(obj).__name__].strip()
        
        invited = Session.query(User).filter_by(email=email).first()
        invites = Session.query(Invite).filter_by(invited_email=email, object_id=obj.id, type=type_)
        invites = invites.filter(Invite.status.in_([STATUS_APPROVED, STATUS_PENDING])).first()
        
        if (invited and obj.get_role(invited)) or invites:
            raise ex.AppException('User has already been added to this %s' % type(obj).__name__, ex.DUPLICATE)
        
        inv = Invite(role=role, type=type_, invited_email=email,
                     user=user, invited_user=invited,
                     object_id=obj.id, status=STATUS_PENDING)
        Session.flush()
        
        Session.add(activity.InviteEvent(user, inv))
        
        return inv
    
    @property
    def object(self):
        if not getattr(self, '_object', None):
            self._setup_lookups()
            self._object = Session.query(self.fetch_types[self.type.strip()]).filter_by(id=self.object_id).first()
        return self._object
    
    def reject(self):
        self.status = STATUS_REJECTED
    
    def accept(self, user=None):
        """
        Accept an invite. Will attach the user to the object with an approved status.
        """
        
        if self.status != STATUS_PENDING:
            raise ex.AppException('Invite %r already accepted' % self, ex.INVALID)
        
        if not self.invited_user:
            
            if not user:
                raise ex.AppException('Specify user to Invite.accept()', ex.INVALID)
            if user.email.lower() != self.invited_email.lower():
                raise ex.AppException("User's email does not match invite's email in Invite.accept()", ex.INVALID)
            
            self.invited_user = user
        
        self.status = STATUS_APPROVED
        
        obj = self.object
        
        obj.attach_user(self.invited_user, self.role, status=STATUS_APPROVED)
        
        Session.add(activity.InviteAccept(self.invited_user, self))


class BetaEmail(Base):
    """
    Stores an invite to a user.
    """
    __tablename__ = "beta_emails"

    id = sa.Column(sa.Integer, primary_key=True)
    eid = sa.Column(sa.Unicode(6), unique=True, default=short_uuid)
    
    #session id
    sid = sa.Column(sa.Unicode(22), unique=True, default='')
    
    creator_id = sa.Column(sa.Integer, sa.ForeignKey('users.id'), nullable=True, index=True)
    creator = relation("User", backref=backref("added_beta_emails", cascade="all"))
    
    email = sa.Column(sa.Unicode(256), index=True, nullable=False)
    
    clicks = sa.Column(sa.Integer, default=0)
    invites = sa.Column(sa.Integer, default=0)
    
    created_date = sa.Column(sa.DateTime, nullable=False, default=now)
    
    @classmethod
    def get(cls, sid=None, email=None):
        if sid and email:
            return Session.query(BetaEmail).filter( sa.or_(BetaEmail.email==(email and email.lower() or ''), BetaEmail.sid==sid) ).first()
        if sid:
            return Session.query(BetaEmail).filter( BetaEmail.sid==sid ).first()
        if email:
            return Session.query(BetaEmail).filter( BetaEmail.email==(email and email.lower() or '') ).first()
        return None
    
    @classmethod
    def create(cls, sid, email, creator=None, send_email=True):
        from desio.utils import email as email_mod
        
        be = cls.get(sid, email)
        
        if be: return be
        
        be = BetaEmail(sid=sid, email=email.lower(), creator=creator)
        Session.add(be)
        
        if send_email:
            email_mod.send(email, 'beta_email.txt', reply_to='ben@binder.io')
        
        return be