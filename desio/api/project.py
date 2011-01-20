from desio.api import enforce, logger, validate, h, authorize, \
                    AppException, ClientException, CompoundException, \
                    INVALID, NOT_FOUND, FORBIDDEN, abort, FieldEditor, auth, \
                    IsAdmin, MustOwn, IsLoggedIn, CanContributeToOrg
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

@enforce(eid=unicode)
@authorize(CanContributeToOrg())
def get(real_user, user, eid=None):
    if not user and not eid:
        abort(403)

    p = Session.query(projects.Project).filter_by(eid=eid).first()
    if not p:
        abort(403)
    
    return p
