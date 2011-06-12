from desio.api import enforce, logger, validate, h, authorize, \
                    AppException, ClientException, CompoundException, \
                    INVALID, NOT_FOUND, FORBIDDEN, abort, FieldEditor, auth, \
                    IsAdmin, MustOwn, IsLoggedIn, CanReadOrg, CanAdminOrg, \
                    CanWriteOrg, Exists, Or

from desio.model import users, activity, Session, STATUS_APPROVED, STATUS_PENDING, STATUS_REJECTED
import sqlalchemy as sa

import formencode
import formencode.validators as fv

ID_PARAM = 'organization'

ROLES = [users.ROLE_USER, users.ROLE_ADMIN, users.ROLE_ENGINEER]
APP_ROLES = [users.APP_ROLE_READ, users.APP_ROLE_WRITE, users.APP_ROLE_ADMIN]
ROLE_STATUSES = [STATUS_APPROVED, STATUS_PENDING, STATUS_REJECTED]
EDIT_FIELDS = ['name', 'url', 'is_read_open']
ADMIN_EDIT_FIELDS = ['is_active', 'subdomain']

SUBDOMAIN_VALIDATOR = formencode.All(
    fv.UnicodeString(not_empty=True, min=2, max=32, messages={
            'empty': 'Please enter a value',
            'tooShort': 'Subdomains must be at least %(min)i characters.'
    }),
    fv.Regex(regex='^[a-zA-Z][a-zA-Z0-9-]*[a-zA-Z0-9]$',
        messages={
            'invalid': 'Names can only contain letters, numbers, and dashes (-)'
        })
)

SUBDOMAIN_VALIDATOR_EDIT = formencode.All(
    fv.UnicodeString(not_empty=False, min=2, max=32, messages={
            'empty': 'Please enter a value',
            'tooShort': 'Subdomains must be at least %(min)i characters.'
    }),
    fv.Regex(regex='^[a-zA-Z][a-zA-Z0-9-]*[a-zA-Z0-9]$',
        messages={'invalid': 'Names can only contain letters, numbers, and dashes (-)'}
    )
)

class UniqueSubdomain(fv.FancyValidator):
    def _to_python(self, value, state):
        
        if type(value) != type(u""):
            raise fv.Invalid('You must supply a valid subdomain.', value, state)
        
        subd = Session.query(users.Organization).filter(sa.func.lower(users.Organization.subdomain)==value.lower()).first()
        
        if subd:
            raise fv.Invalid('%s is already taken' % value, value, state)
        
        return value.lower()

class RoleStatusForm(formencode.Schema):
    role = fv.OneOf(APP_ROLES, not_empty=True)
    status = fv.OneOf(ROLE_STATUSES, not_empty=True)

class EditForm(formencode.Schema):
    name = fv.UnicodeString(not_empty=False, min=4, max=64)
    url = formencode.All(fv.MaxLength(512, not_empty=False), fv.URL())
    subdomain = formencode.All(SUBDOMAIN_VALIDATOR_EDIT, UniqueSubdomain())
    is_active = fv.Bool(not_empty=False)
    is_read_open = fv.Bool(not_empty=False)

class CreateForm(formencode.Schema):
    subdomain = formencode.All(SUBDOMAIN_VALIDATOR, UniqueSubdomain())
    company_name = fv.UnicodeString(not_empty=True, min=4, max=64)
    url = formencode.All(fv.MaxLength(512, not_empty=False), fv.URL())

class SubdomainTestForm(formencode.Schema):
    subdomain = formencode.All(SUBDOMAIN_VALIDATOR, UniqueSubdomain())
    
@enforce()
@authorize(IsLoggedIn())
def create(real_user, user, **params):
    """
    Creates an organization. Attaches it to User.
    """
    
    scrubbed = validate(CreateForm, **params)
    scrubbed.setdefault('is_active', True)
    
    scrubbed['name'] = scrubbed['company_name']
    del scrubbed['company_name']
    
    #attach the user as a creator.
    org = users.Organization(creator=user, **scrubbed)
    Session.add(org)
    
    #connect user to org as admin of org
    org.attach_user(user, role=users.APP_ROLE_ADMIN, status=STATUS_APPROVED)
    Session.add(activity.NewOrganization(user, org))
    
    Session.flush()
    return org

@enforce()
def get(real_user=None, user=None, organization=None, subdomain=None):
    """
    get a single project, or all the user's projects
    """
    if organization:
        CanReadOrg().check(real_user, user, organization=organization)
        return organization
    
    elif subdomain:
        return Session.query(users.Organization).filter_by(subdomain=subdomain).first()
    
    return user.get_organizations()

@enforce()
@authorize(CanReadOrg())
def get_structure(real_user, user, organization=None):
    """
    get the org and all projects. Serializer does most the work.
    """
    if not organization:
        abort(404)
    
    projects = organization.get_projects(user)
    
    return (organization, projects)

@enforce(is_active=bool)
@authorize(CanAdminOrg())
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
    
    def edit_is_read_open(self, real_user, user, u, key, param):
        self._edit_generic('Is Read Open', u, key, param)
    
    def edit_subdomain(self, real_user, user, u, key, param):
        self._edit_generic('Subdomain', u, key, param)

@enforce(subdomain=unicode)
def is_unique(subdomain):
    validate(SubdomainTestForm, subdomain=subdomain)
    return {'is': True}

@enforce(u=users.User, role=unicode, status=unicode)
@authorize(IsLoggedIn(), Exists('organization', 'u'))
def attach_user(real_user, user, organization, u, role=users.APP_ROLE_READ, status=STATUS_PENDING):

    params = validate(RoleStatusForm, role=role, status=status)
    
    orgu = organization.get_user_connection(u, status=None)
    if orgu:
        raise ClientException('User already attached', INVALID)
    
    role = organization.get_role(user)
    if role == users.APP_ROLE_ADMIN:
        #special. We adhere to role and status vars
        orgu = organization.attach_user(u, role=params.role, status=params.status)
    else:
        # anyone can attempt to attach themselves, but they will be pending approval in
        # read group only
        orgu = organization.attach_user(u, role=users.APP_ROLE_READ, status=STATUS_PENDING)
    
    return orgu

@enforce(u=users.User)
@authorize(CanAdminOrg())
def remove_user(real_user, user, organization, u):
    return organization.remove_user(u)

@enforce(u=users.User, role=unicode)
@authorize(CanAdminOrg(), Exists('u'))
def attachment_approval(real_user, user, organization, u, status=STATUS_APPROVED):
    if status not in [STATUS_APPROVED, STATUS_REJECTED]:
        raise ClientException('Invalid status', field='status', code=INVALID)
    
    #returns false when user/org connection not found
    return bool(organization.set_user_status(u, status))

@enforce(u=users.User, role=unicode)
@authorize(CanAdminOrg(), Exists('u'))
def set_user_role(real_user, user, organization, u, role):
    if role not in users.APP_ROLES:
        raise ClientException('Role must be one of %s' % users.APP_ROLES, field='role')
    
    return organization.set_role(u, role)

@enforce(status=[unicode])
@authorize(CanReadOrg())
def get_users(real_user, user, organization, status=None):
    
    return organization.get_user_connections(status=status)