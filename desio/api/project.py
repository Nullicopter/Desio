from desio.api import enforce, logger, validate, h, authorize, \
                    AppException, ClientException, CompoundException, \
                    abort, FieldEditor, auth, \
                    IsAdmin, MustOwn, IsLoggedIn, CanWriteProject,CanAdminProject, CanReadProject, \
                    CanContributeToOrg, CanReadOrg
from desio.model import users, Session, projects, STATUS_APPROVED, STATUS_PENDING, STATUS_REJECTED
import sqlalchemy as sa

import formencode
import formencode.validators as fv

from pylons_common.lib.exceptions import *

ID_PARAM = 'project'

EDIT_FIELDS = ['name', 'description']
ADMIN_EDIT_FIELDS = ['status']

ROLES = [projects.PROJECT_ROLE_READ, projects.PROJECT_ROLE_WRITE, projects.PROJECT_ROLE_ADMIN]
ROLE_STATUSES = [STATUS_APPROVED, STATUS_PENDING, STATUS_REJECTED]

class RoleStatusForm(formencode.Schema):
    role = fv.OneOf(ROLES, not_empty=True)
    status = fv.OneOf(ROLE_STATUSES, not_empty=True)

class UniqueName(fv.FancyValidator):
    def __init__(self, organization, project=None):
        self.organization = organization
        self.project = project
    
    def _to_python(self, value, state):
        # we don't support multiple values, so we run a quick check here (we got a webapp where this was a problem)
        if not isinstance(value, unicode):
            raise fv.Invalid('You must supply a valid string.', value, state)

        project = Session.query(projects.Project
                ).filter(projects.Project.organization==self.organization
                ).filter(projects.Project.name==value
                )
        
        if self.project:
            project = project.filter(projects.Project.id != self.project.id)
        
        project = project.first()

        if project:
            raise fv.Invalid('A project with this name already exists. Please choose another.', value, state)
        return value

@enforce(name=unicode, description=unicode)
@authorize(CanContributeToOrg())
def create(real_user, user, organization, **params):
    """
    Creates a project.
    """
    class ProjectForm(formencode.Schema):
        name = formencode.All(fv.UnicodeString(not_empty=True), UniqueName(organization))
        description = fv.UnicodeString(not_empty=False)
    
    scrubbed = validate(ProjectForm, **params)

    project = projects.Project(name=scrubbed.name,
                               creator=user,
                               description=scrubbed.description,
                               organization=organization)
    Session.add(project)
    Session.flush()
    
    return project

@enforce()
@authorize(CanAdminProject())
def edit(real_user, user, project, **kwargs):
    """
    Editing of the campaigns. Supports editing one param at a time. Uses the FieldEditor
    paradigm.
    """
    editor = Editor(project)
    editor.edit(real_user, user, project, **kwargs)
    Session.flush()
    Session.refresh(project)
    return project

class Editor(FieldEditor):
    def __init__(self, project):
        
        class EditForm(formencode.Schema):
            name = formencode.All(fv.UnicodeString(not_empty=False), UniqueName(project.organization, project))
            description = fv.UnicodeString(not_empty=False)
        
        super(Editor, self).__init__(EDIT_FIELDS, ADMIN_EDIT_FIELDS, EditForm)

    def edit_name(self, real_user, user, u, key, param):
        self._edit_generic('Name', u, key, param)
    
    def edit_description(self, real_user, user, u, key, param):
        self._edit_generic('Description', u, key, param)
    
    def edit_status(self, real_user, user, u, key, param):
        self._edit_generic('Status', u, key, param)

@enforce(project=unicode)
@authorize(CanReadOrg())
def get(real_user, user, organization, project=None):
    if not user and not project:
        abort(403)
    
    if project:
        q = Session.query(projects.Project).filter_by(organization=organization)
        p = q.filter(sa.or_(projects.Project.eid==project, projects.Project.slug==project)).first()
        CanReadProject().check(real_user, user, project=p)
        return p
    
    return organization.get_projects(user)

##
### User connection stuff

@enforce(u=users.User, role=unicode, status=unicode)
@authorize(CanAdminProject())
def attach_user(real_user, user, project, u, role=users.ORGANIZATION_ROLE_USER):#, status=STATUS_APPROVED): #maybe later

    params = validate(RoleStatusForm, role=role, status=STATUS_APPROVED)
    
    if not project:
        raise ClientException('Project not found', NOT_FOUND, field='project')
    if not u:
        raise ClientException('User not found', NOT_FOUND, field='u')
    
    pu = project.get_project_user(u, status=None)
    if pu:
        raise ClientException('User already attached', INVALID)
    
    orgu = project.attach_user(u, role=params.role, status=params.status)
    
    return orgu

@enforce(users=[users.User], roles=[unicode])
@authorize(CanAdminProject())
def attach_users(real_user, user, project, users, roles):
    if len(users) != len(roles):
        raise ClientException('users and roles much match in size!', field='users')
    
    org_users = []
    for i, u in enumerate(users):
        org_users.append(attach_user(real_user, user, project, u, role=roles[i]))
    
    return org_users

@enforce(u=users.User)
@authorize(CanAdminProject())
def remove_user(real_user, user, project, u):
    return project.remove_user(u)

@enforce(u=users.User, role=unicode)
@authorize(CanAdminProject())
def set_user_role(real_user, user, project, u, role):
    if role not in ROLES:
        raise ClientException('Role must be one of %s' % ROLES, field='role')
    if not u:
        raise ClientException('Need a user!', field='u', code=INVALID)
    
    return project.set_role(u, role)

@enforce(status=[unicode])
@authorize(CanReadProject())
def get_users(real_user, user, project, status=STATUS_APPROVED):
    
    return project.get_project_users(status=status)