from desio.api import enforce, logger, validate, h, authorize, \
                    AppException, ClientException, CompoundException, \
                    INVALID, NOT_FOUND, FORBIDDEN, abort, FieldEditor, auth, \
                    IsAdmin, MustOwn, IsLoggedIn, CanContributeToOrg, CanReadOrg
from desio.model import users, Session, projects
import sqlalchemy as sa
import re

import formencode
import formencode.validators as fv

from pylons_common.lib.utils import uuid

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

def get_unique_slug(organization, name, max=100):
    
    def gen_slug(input, addon=u''):
        return (u'-'.join(re.findall('[a-z0-9]+', input, flags=re.IGNORECASE)))[:max].lower() + addon
    
    for c in range(20):
        slug = gen_slug(name, addon=(c and unicode(c) or u''))
        project = Session.query(projects.Project
                ).filter(projects.Project.organization==organization
                ).filter(projects.Project.slug==slug
                ).first()
        if not project: return slug
    
    return uuid() #they have 20 projects named similarly, now they get eids!


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
                               slug=get_unique_slug(organization, scrubbed.name),
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
