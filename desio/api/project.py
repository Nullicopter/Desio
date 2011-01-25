from desio.api import enforce, logger, validate, h, authorize, \
                    AppException, ClientException, CompoundException, \
                    INVALID, NOT_FOUND, FORBIDDEN, abort, FieldEditor, auth, \
                    IsAdmin, MustOwn, IsLoggedIn, CanContributeToOrg, CanReadOrg
from desio.model import users, Session, projects
import sqlalchemy as sa

import formencode
import formencode.validators as fv

ID_PARAM = 'project'

EDIT_FIELDS = ['name', 'description']
ADMIN_EDIT_FIELDS = ['status']

class UniqueName(fv.FancyValidator):
    def __init__(self, organization):
        self.organization = organization
    
    def _to_python(self, value, state):
        # we don't support multiple values, so we run a quick check here (we got a webapp where this was a problem)
        if not isinstance(value, unicode):
            raise fv.Invalid('You must supply a valid string.', value, state)

        project = Session.query(projects.Project
                ).filter(projects.Project.organization==self.organization
                ).filter(projects.Project.name==value
                ).first()

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
                               description=scrubbed.description,
                               organization=organization)
    Session.add(project)
    
    return project

@enforce(project=unicode)
@authorize(CanReadOrg())
def get(real_user, user, organization, project=None):
    if not user and not project:
        abort(403)

    q = Session.query(projects.Project).filter_by(organization=organization)

    if project is None:
        return q.order_by(sa.desc(projects.Project.last_modified_date)).all()
    
    p = q.filter(sa.or_(projects.Project.eid==project, projects.Project.slug==project)).first()

    if not p:
        raise ClientException("Project not found", code=NOT_FOUND)
    
    return p
