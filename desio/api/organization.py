from desio.api import enforce, logger, validate, h, authorize, \
                    AppException, ClientException, CompoundException, \
                    INVALID, NOT_FOUND, FORBIDDEN, abort, FieldEditor, auth, \
                    IsAdmin, MustOwn, IsLoggedIn, CanReadOrg, CanEditOrg, \
                    CanContributeToOrg

from desio.model import users, Session, STATUS_APPROVED, STATUS_PENDING, STATUS_REJECTED
import sqlalchemy as sa

import formencode
import formencode.validators as fv

ID_PARAM = 'organization'

ROLES = [users.ROLE_USER, users.ROLE_ADMIN, users.ROLE_ENGINEER]
ORGANIZATION_ROLES = [users.ORGANIZATION_ROLE_USER, users.ORGANIZATION_ROLE_CREATOR, users.ORGANIZATION_ROLE_ADMIN]
ROLE_STATUSES = [STATUS_APPROVED, STATUS_PENDING, STATUS_REJECTED]
EDIT_FIELDS = ['name', 'url']
ADMIN_EDIT_FIELDS = ['is_active', 'subdomain']

SUBDOMAIN_VALIDATOR = formencode.All(
    fv.UnicodeString(not_empty=True, min=2, max=32),
    fv.Regex(regex='^[a-zA-Z][a-zA-Z0-9-]*[a-zA-Z0-9]$',
    messages={'invalid': 'Names can only contain letters, numbers, and dashes (-)'})
)

SUBDOMAIN_VALIDATOR_EDIT = formencode.All(
    fv.UnicodeString(not_empty=False, min=2, max=32),
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

class RoleStatusForm(formencode.Schema):
    role = fv.OneOf(ORGANIZATION_ROLES, not_empty=True)
    status = fv.OneOf(ROLE_STATUSES, not_empty=True)

class EditForm(formencode.Schema):
    name = fv.UnicodeString(not_empty=False, min=4, max=64)
    url = formencode.All(fv.MaxLength(512, not_empty=False), fv.URL())
    subdomain = formencode.All(SUBDOMAIN_VALIDATOR_EDIT, UniqueSubdomain())
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
    
    #attach the user as a creator.
    org = users.Organization(creator=user, **scrubbed)
    Session.add(org)
    
    #connect user to org as admin of org
    org.attach_user(user, role=users.ORGANIZATION_ROLE_ADMIN, status=STATUS_APPROVED)
    
    Session.flush()
    return org

@enforce(subdomain=unicode)
#@authorize(CanReadOrg()) # dont have to be logged in. Must be careful if we expose this to webservice
def get(organization=None, subdomain=None):
    if not organization and not subdomain:
        abort(404)
    
    if organization: return organization
    
    organization = Session.query(users.Organization).filter(users.Organization.subdomain==subdomain).first()
    
    if not organization:
        raise ClientException('Org not found', code=NOT_FOUND)
    
    return organization

@enforce(is_active=bool)
@authorize(CanEditOrg())
def edit(real_user, user, organization, **kwargs):
    """
    Editing of the campaigns. Supports editing one param at a time. Uses the FieldEditor
    paradigm.
    """
    editor = Editor()
    editor.edit(real_user, user, organization, **kwargs)
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
    
    def edit_subdomain(self, real_user, user, u, key, param):
        self._edit_generic('Subdomain', u, key, param)

@enforce(subdomain=unicode)
def is_unique(subdomain):
    subdomain = SUBDOMAIN_VALIDATOR._to_python(subdomain, None)
    
    usd = UniqueSubdomain()
    try:
        usd._to_python(subdomain, None)
    except fv.Invalid, e:
        return False
    return True

@enforce(u=users.User, role=unicode, status=unicode)
@authorize(IsLoggedIn())
def attach_user(real_user, user, organization, u, role=users.ORGANIZATION_ROLE_USER, status=STATUS_PENDING):

    params = validate(RoleStatusForm, role=role, status=status)
    
    if not organization:
        raise ClientException('Organization not found', NOT_FOUND, field='organization')
    if not u:
        raise ClientException('User not found', NOT_FOUND, field='u')
    
    orgu = organization.get_organization_user(u, status=None)
    if orgu:
        raise ClientException('User already attached', INVALID)
    
    role = organization.get_role(user)
    if role == users.ORGANIZATION_ROLE_ADMIN:
        #special. We adhere to role and status vars
        orgu = organization.attach_user(u, role=params.role, status=params.status)
    else:
        # anyone can attempt to attach themselves, but they will be pending approval in
        # read group only
        orgu = organization.attach_user(u, role=users.ORGANIZATION_ROLE_USER, status=STATUS_PENDING)
    
    return bool(orgu)

@enforce(u=users.User, role=unicode)
@authorize(CanEditOrg())
def attachment_approval(real_user, user, organization, u, status=STATUS_APPROVED):
    if status not in [STATUS_APPROVED, STATUS_REJECTED]:
        raise ClientException('Invalid status', field='status', code=INVALID)
    if not u:
        raise ClientException('Need a user!', field='u', code=INVALID)
    
    #returns false when user/org connection not found
    return bool(organization.set_user_status(u, status))

### stubs

@enforce(status=unicode)
@authorize(CanReadOrg())
def get_users(real_user, user, organization, status=None):
    
    return organization.get_organization_users(status=status)