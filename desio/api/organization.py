from desio.api import enforce, logger, validate, h, authorize, \
                    AppException, ClientException, CompoundException, \
                    INVALID, NOT_FOUND, FORBIDDEN, abort, FieldEditor, auth, \
                    IsAdmin, MustOwn, IsLoggedIn

from desio.model import users, Session, STATUS_APPROVED, STATUS_PENDING
import sqlalchemy as sa

import formencode
import formencode.validators as fv

ID_PARAM = 'organization'

ROLES = [users.ROLE_USER, users.ROLE_ADMIN, users.ROLE_ENGINEER]
EDIT_FIELDS = ['name', 'url']
ADMIN_EDIT_FIELDS = ['is_active']

SUBDOMAIN_VALIDATOR = formencode.All(
    fv.UnicodeString(not_empty=True, min=2, max=32),
    fv.Regex(regex='^[a-zA-Z][a-zA-Z0-9-]*[a-zA-Z0-9]$',
    messages={'invalid': 'Names can only contain letters, numbers, and dashes (-)'})
)

class UniqueSubdomain(fv.FancyValidator):
    def _to_python(self, value, state):
        
        if type(value) != type(u""):
            raise fv.Invalid('You must supply a valid subdomain.', value, state)
        
        subd = Session.query(users.Organization).filter(sa.func.lower(users.Organization.subdomain)==value.lower()).first()
        
        if subd:
            raise fv.Invalid('That subdomain already exists :(', value, state)
        
        return value

class EditForm(formencode.Schema):
    name = fv.UnicodeString(not_empty=False, min=4, max=64)
    url = formencode.All(fv.MaxLength(512, not_empty=False), fv.URL())
    is_active = fv.Bool(not_empty=False)

class CreateForm(formencode.Schema):
    subdomain = formencode.All(SUBDOMAIN_VALIDATOR, UniqueSubdomain())
    name = fv.UnicodeString(not_empty=True, min=4, max=64)
    url = formencode.All(fv.MaxLength(512, not_empty=False), fv.URL())

@enforce()
@authorize(IsLoggedIn())
def create(real_user, user, **params):
    """
    Creates an organization. Attaches it to User.
    """
    
    scrubbed = validate(CreateForm, **params)
    scrubbed.setdefault('is_active', True)
    
    org = users.Organization(**scrubbed)
    Session.add(org)
    
    #connect user to org as admin of org
    org.attach_user(user, role=users.ORGANIZATION_ROLE_ADMIN, status=STATUS_APPROVED)
    
    Session.flush()
    return org

@enforce()
@authorize(MustOwn('organization'))
def get(real_user, user, organization):
    if not organization:
        abort(403)
    return organization

@enforce(is_active=bool)
@authorize(MustOwn('organization'))
def edit(real_user, user, organization, **kwargs):
    """
    Editing of the campaigns. Supports editing one param at a time. Uses the FieldEditor
    paradigm.
    """
    editor = Editor()
    editor.edit(real_user, user, u, **kwargs)
    Session.flush()
    Session.refresh(organization)
    return organization

class Editor(FieldEditor):
    def __init__(self):
        super(Editor, self).__init__(EDIT_FIELDS, ADMIN_EDIT_FIELDS, EditForm)

    def edit_name(self, real_user, user, u, key, param):
        self._edit_generic('Name', u, key, param)
    
    def edit_url(self, real_user, user, u, key, param):
        self._edit_generic('Url', u, key, param)
    
    def edit_is_active(self, real_user, user, u, key, param):
        self._edit_generic('IsActive', u, key, param)

@enforce(subdomain=unicode)
def is_unique(subdomain):
    subdomain = SUBDOMAIN_VALIDATOR._to_python(subdomain, None)
    
    usd = UniqueSubdomain()
    try:
        usd._to_python(subdomain, None)
    except fv.Invalid, e:
        return False
    return True

### stubs

@enforce(u=users.User, role=unicode)
@authorize(MustOwn('organization'))
def attach_user(real_user, user, organization, u, role=users.ORGANIZATION_ROLE_USER):
    pass

@enforce(u=users.User, role=unicode)
@authorize(MustOwn('organization'))
def attachment_approval(real_user, user, organization, u, status=STATUS_APPROVED):
    if status not in [STATUS_APPROVED, STATUS_REJECTED]:
        raise ClientException('Invalid status', field='status', code=INVALID)
    if not user:
        raise ClientException('Need a user!', field='u', code=INVALID)
    
    return True

@enforce()
@authorize(MustOwn('organization'))
def get_users(real_user, user, organization):
    pass