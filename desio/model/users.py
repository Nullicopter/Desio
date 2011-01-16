import sqlalchemy as sa
from sqlalchemy.orm import relation, backref

import pytz
from desio.model.meta import Session, Base
import hashlib

from datetime import datetime

from pylons_common.lib import exceptions, date
from desio.model import STATUS_APPROVED, STATUS_REJECTED, STATUS_PENDING

ROLE_USER = u'user'
ROLE_ADMIN = u'admin'
ROLE_ENGINEER = u'engineer'

ORGANIZATION_ROLE_ADMIN = ROLE_ADMIN
ORGANIZATION_ROLE_CREATOR = 'creator'
ORGANIZATION_ROLE_USER = ROLE_USER

def now():
    return datetime.utcnow()

def hash_password(clear_pass):
    """
    Used to encrypt our passwords with our special salt.
    """
    salt = u"c4tsareninjasMeow".encode('utf-8')
    hash = hashlib.md5( salt + clear_pass.encode("utf-8") ).hexdigest()

    return hash.decode('utf-8')

class OrganizationUser(Base):
    """
    Stores a user preference
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

class Organization(Base):
    """
    Stores a user preference
    """
    __tablename__ = "organizations"

    id = sa.Column(sa.Integer, primary_key=True)
    
    subdomain = sa.Column(sa.Unicode(64), nullable=False)
    name = sa.Column(sa.Text(), nullable=False)
    url = sa.Column(sa.Text(), nullable=True)
    
    is_active = sa.Column(sa.Boolean(), default=True)
    
    created_date = sa.Column(sa.DateTime, nullable=False, default=now)
    updated_date = sa.Column(sa.DateTime, nullable=False, onupdate=now, default=now)
    
    def __repr__(self):
        return u'Organization(%s, %s)' % (self.id, self.subdomain)
    
    def get_role(self, user, status=STATUS_APPROVED):
        orgu = self.get_organization_user(user, status)
        if orgu:
            return orgu.role
        return None
    
    def get_organization_user(self, user, status=None):
        q = Session.query(OrganizationUser).filter(OrganizationUser.user_id==user.id)
        if status:
            q = q.filter(OrganizationUser.status==status)
        return q.filter(OrganizationUser.organization_id==self.id).first()
    
    def set_user_status(self, user, status):
        # could check pending?
        org_user = self.get_organization_user(user)
        if not org_user:
            return False
        org_user.status = status
        return org_user
    
    def approve_user(self, user):
        self.set_user_status(user, STATUS_APPROVED)
    
    def reject_user(self, user):
        self.set_user_status(user, STATUS_REJECTED)
    
    def attach_user(self, user, role=ORGANIZATION_ROLE_USER, status=STATUS_PENDING):
        org_user = Session.query(OrganizationUser) \
                    .filter(OrganizationUser.organization==self) \
                    .filter(OrganizationUser.user==user).first()
        if org_user:
            org_user.role = role
            org_user.status = status
            return org_user
        
        org_user = OrganizationUser(user=user, organization=self, role=role, status=status)
        Session.add(org_user)
        return org_user
    
    def remove_user(self, user):
        q = Session.query(OrganizationUser).filter(OrganizationUser.organization_id==self.id)
        q = q.filter(OrganizationUser.user_id==user.id)
        orgu = q.first()
        if orgu:
            Session.delete(orgu)
            return True
        return False

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

    email = sa.Column(sa.Unicode(64), unique=True, index=True, nullable=False)
    #: Phone number
    phone = sa.Column(sa.Unicode(25), nullable=True)
    #: User entered nickname, required maximum 64 characters
    _username = sa.Column("username", sa.Unicode(64), unique=True, index=True, nullable=False)
    _display_username = sa.Column("display_username", sa.Unicode(64), unique=True, index=True, nullable=False)
    #: The encrypted version of the password
    _password = sa.Column("password", sa.Unicode(32), nullable=False)
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
    
    def get_preference(self, key, ignore_default=False):
        """
        Gets a user's preference.
        
        :param key: A string key to retrieve the value of
        :param ignore_default: Will return None on key not found instead of the
        default.
        """
        self._load_prefs()
        
        if key in self.preferences_dict:
            return self.preferences_dict[key].value
        
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
        q = Session.query(OrganizationUser).filter(OrganizationUser.user_id==self.id)
        if status:
            q = q.filter(OrganizationUser.status==status)
        return [r.organization for r in q.all()]
    
    def must_own(self, *things):
        if self.is_admin():
            return True
        for thing in things:
            if thing and not self.owns(thing):
                raise exceptions.ClientException("User must be an admin or else own this %s." % thing.__class__.__name__, exceptions.FORBIDDEN)
    
    def owns(self, thing):
        """
        Does the user own the given thing, or not.
        """
        if not thing:
            return False
        if hasattr(thing, 'user_id'):
            return self.id == thing.user_id
        elif isinstance(thing, list):
            for item in thing:
                if not self.owns(item):
                    return False
            return True
        return False