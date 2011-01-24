from desio.api import enforce, logger, validate, h, authorize, \
                    AppException, ClientException, CompoundException, \
                    INVALID, NOT_FOUND, FORBIDDEN, abort, FieldEditor, auth, \
                    IsAdmin, MustOwn, IsLoggedIn

from desio.model import users, Session
import sqlalchemy as sa

import formencode
import formencode.validators as fv

ID_PARAM = 'u'

ROLES = [users.ROLE_USER, users.ROLE_ADMIN, users.ROLE_ENGINEER]
EDIT_FIELDS = ['password', 'first_name', 'last_name', 'default_timezone']
ADMIN_EDIT_FIELDS = ['role', 'is_active', 'username']

class UniqueEmail(fv.FancyValidator):
    def __init__(self, user=None):
        self.user = user
    
    def _to_python(self, value, state):
        # we don't support multiple values, so we run a quick check here (we got a webapp where this was a problem)
        if type(value) != type(u""):
            raise fv.Invalid('You must supply a valid email.', value, state)
        
        user = Session.query(users.User).filter(sa.func.lower(users.User.email)==value.lower()).first()
        # if this user is the same as the logged in one then don't throw the error - allows keeping old email address when editing contact info
        if user and user != self.user:
            raise fv.Invalid('That user already exists. Please choose another.', value, state)
        return value

class RegisterForm(formencode.Schema):
    
    password = fv.UnicodeString(not_empty=True, min=5)
    confirm_password = fv.UnicodeString(not_empty=True, min=5)
    email = formencode.All(fv.Email(not_empty=True), fv.MaxLength(256), UniqueEmail())
    default_timezone = fv.Int(not_empty=True)
    username = fv.UnicodeString(not_empty=False, min=4, max=64)
    first_name = fv.UnicodeString(not_empty=False, max=64)
    last_name = fv.UnicodeString(not_empty=False, max=64)
    name = fv.UnicodeString(not_empty=False, max=128)
    
    chained_validators = [fv.FieldsMatch('password', 'confirm_password')]

@enforce(default_timezone=int)
def create(**params):
    """
    Creates a user.
    
    DO NOT EXPOSE THIS to the web api. Please.
    """
    numusers = len(Session.query(users.User).all())

    scrubbed = validate(RegisterForm, **params)

    user = users.User()
    Session.add(user)
    
    user.email = scrubbed.email
    user.username = 'username' in scrubbed and scrubbed.username or scrubbed.email
    user.password = scrubbed.password
    user.set_timezone_int(scrubbed.default_timezone)
    
    if scrubbed.get('name'):
        name = scrubbed.get('name').split(' ', 1)
        user.first_name = name[0].strip()
        user.last_name = len(name) == 2 and name[1].strip() or u''
    else:
        user.first_name = scrubbed.get('first_name')
        user.last_name = scrubbed.get('last_name')
    
    #first user is an admin. 
    if numusers == 0:
        user.role = users.ROLE_ADMIN
    
    return user

@enforce(key=unicode, value=unicode, use_real_user=bool)
def set_pref(real_user, user, key, value, use_real_user=True):
    
    class Pref(formencode.Schema):
        key     = fv.MaxLength(64, not_empty=True)
        value   = fv.MaxLength(64, not_empty=False)
    scrubbed = validate(Pref, key=key, value=value)
    
    u = user
    if use_real_user:
        u = real_user
    u.set_preference(scrubbed.key, scrubbed.value or '')

def generate_password():
    return utils.uuid()[:8]

@enforce(u=users.User, username=unicode)
#@authorize(IsAdmin())
def get(u=None, username=None):
    if not u and not username:
        abort(403)
    elif u: return u
    
    u = Session.query(users.User).filter_by(username=username).first()
    if not u:
        abort(403)
    
    return u

@enforce(u=users.User)
@authorize(IsAdmin())
def masquerade(real_user, user, u):
    if not u:
        return False
    auth.login(u, redirect_after=False)
    return True

@enforce(u=users.User)
@authorize(IsAdmin())
def pretend(real_user, user, u):
    if not u:
        return False
    auth.pretend(u, url=None)
    return True

@enforce()
@authorize(IsAdmin())
def stop_pretending(real_user, user):
    auth.stop_pretending(url=None)
    return True
    

@enforce(u=users.User, is_active=bool, default_timezone=int)
@authorize(IsLoggedIn())
def edit(real_user, user, u, **kwargs):
    """
    Editing of the campaigns. Supports editing one param at a time. Uses the FieldEditor
    paradigm.
    """
    if not u or not(real_user.is_admin() or real_user.id == u.id):
        raise ClientException('User not found', code=NOT_FOUND, field='u')
    
    editor = Editor()
    editor.edit(real_user, user, u, **kwargs)
    return u

class EditForm(formencode.Schema):
    role = formencode.All(fv.UnicodeString(not_empty=False), fv.OneOf(ROLES))
    password = formencode.All(fv.UnicodeString(not_empty=False))
    first_name = formencode.All(fv.UnicodeString(not_empty=False), fv.MaxLength(64))
    last_name = formencode.All(fv.UnicodeString(not_empty=False), fv.MaxLength(64))
    default_timezone = fv.Int(not_empty=False)
    is_active = fv.Bool(not_empty=False)

class Editor(FieldEditor):
    def __init__(self):
        super(Editor, self).__init__(EDIT_FIELDS, ADMIN_EDIT_FIELDS, EditForm)

    def edit_role(self, real_user, user, u, key, param):
        self._edit_generic('Role', u, key, param)
    
    def edit_password(self, real_user, user, u, key, param):
        self._edit_generic('Password', u, key, param)
    
    def edit_username(self, real_user, user, u, key, param):
        self._edit_generic('Username', u, key, param)
    
    def edit_first_name(self, real_user, user, u, key, param):
        self._edit_generic('First Name', u, key, param)
    
    def edit_last_name(self, real_user, user, u, key, param):
        self._edit_generic('Last Name', u, key, param)
    
    def edit_default_timezone(self, real_user, user, u, key, param):
        old = u.default_timezone
        u.set_timezone_int(param)
        self.log('Timezone', key, old, u.default_timezone)
    
    def edit_is_active(self, real_user, user, u, key, param):
        self._edit_generic('IsActive', u, key, param)