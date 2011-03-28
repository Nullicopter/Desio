from desio.api import enforce, logger, validate, h, authorize, \
                    AppException, ClientException, CompoundException, \
                    abort, FieldEditor, auth, \
                    IsAdmin, MustOwn, IsLoggedIn, CanWriteProject,CanAdminProject, CanReadProject, \
                    CanContributeToOrg, CanReadOrg, Exists, Or
from desio.model import users, Session, projects, STATUS_APPROVED, STATUS_PENDING, STATUS_REJECTED
import sqlalchemy as sa
import os.path

import formencode
import formencode.validators as fv

from pylons_common.lib.exceptions import *
from pylons_common.lib.utils import uuid

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
@authorize(CanAdminProject(), Exists('project', 'u'))
def attach_user(real_user, user, project, u, role=users.ORGANIZATION_ROLE_USER):#, status=STATUS_APPROVED): #maybe later

    params = validate(RoleStatusForm, role=role, status=STATUS_APPROVED)
    
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
@authorize(CanAdminProject(), Exists('u'))
def set_user_role(real_user, user, project, u, role):
    if role not in ROLES:
        raise ClientException('Role must be one of %s' % ROLES, field='role')
    
    return project.set_role(u, role)

@enforce(status=[unicode])
@authorize(CanReadProject())
def get_users(real_user, user, project, status=STATUS_APPROVED):
    
    return project.get_project_users(status=status)

def _get_files_for_dir(project, dirobj):
    if not dir: return None
    
    def get_file_tuple(f):
        return (f, f.get_change())
    
    newpath = os.path.join(dirobj.path, dirobj.name)+'/'
    dirfiles = project.get_entities(filepath=newpath, only_type=projects.File.TYPE)
    d = (dirobj, [])
    for f in dirfiles:
        d[1].append(get_file_tuple(f))
    return d

@enforce(path=unicode)
@authorize(CanWriteProject(), Exists('path'))
def add_directory(real_user, user, project, path):
    
    dir = project.add_directory(user, path)
    print path, dir
    
    return _get_files_for_dir(project, dir)

@enforce(path=unicode)
@authorize(CanWriteProject(), Exists('path'))
def get_directory(real_user, user, project, path):
    """
    returns
    [(Directory(/), [
        (File('bleh.png'), Change('latestversion')),
    ]),
    """
    
    if path[-1] != u'/': path = path + u'/'
    
    dir = project.get_entities(user, path[:-1], only_type=projects.Directory.TYPE)
    
    return _get_files_for_dir(project, dir)
    
@enforce(path=unicode)
@authorize(CanReadProject(), Exists('path'))
def get_structure(real_user, user, project, path=u'/'):
    """
    For a given path will get all the files, directories and files within
    the top level directories.
    
    returns something like this:
    [(Directory(/), [
        (File('bleh.png'), Change('latestversion')),
    ]),
    (Directory(/mydir), [
        (File('bleh2.png'), Change('latestversion')),
    ]),]
    """
    
    if path[-1] != u'/': path = path + u'/'
    
    def get_file_tuple(f):
        return (f, f.get_change())
    
    entities = project.get_entities(filepath=path)
    
    res = []
    cur_dir = None
    cur_dir_files = []
    for entity in entities:
        if entity.type == projects.File.TYPE:
            cur_dir_files.append(get_file_tuple(entity))
        
        #root dir is a special case...
        elif entity.type == projects.Directory.TYPE and not entity.name:
            cur_dir = entity
        
        #is directory
        else:
            res.append(_get_files_for_dir(project, entity))
    
    if not cur_dir:
        if path[:-1]:
            cur_dir = project.get_entities(filepath=path[:-1])
        else:
            #return fake dir for root
            cur_dir = projects.Directory(path=u'/', name=u'', eid=uuid())
    
    res = [(cur_dir, cur_dir_files)] + res
    if not cur_dir_files and not cur_dir: return None
    
    return res

@enforce()
@authorize(CanReadProject())
def get_directories(real_user, user, project):
    """
    Get all directories in the project and returns them.

    The serializer for this call returns the directories in a tree.
    Look at v1 api for more details.
    """
    directories = project.get_entities(only_type=projects.Directory.TYPE)
    return project, directories


@enforce()
@authorize(CanReadProject())
def get_files(real_user, user, project, since=None):
    """
    Get all files in the project and return them, if since is passed
    then only files with changes after since.

    The serializer will append all the changes to each file
    """
    files = project.get_entities(only_type=projects.File.TYPE)
    return project, files
