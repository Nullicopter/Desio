"""
Here we define each front end module. They are in the format:

JS = {
    'module_name': ('path/to/compressed.js', [
        'lib/some/file.js',
        'lib/that/is/part.js',
        'lib/of/the/compressed/module.js'
    ])
}

There is a javascript and a CSS dict. Modules that contain both js and css
should be named the same.

There are multiple consumers of these dicts.

Scriptb uses this for concatenation and compression of the production files.

The templates/require.html module uses them as well:

<%namespace name="r" file="/require.html"/>
${r.require('core', 'test')}

The above would add all css and js includes from both the core and test modules
defined in this file. It will include the proper files depending on whether the
app is in production or dev.
"""
import os

PROJECT_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

STRUCTURE = {
    'JS': {
        'base': os.path.join(PROJECT_PATH, 'public', 'j'),
        'type': 'js'
    },
    
    'CSS': {
        'base': os.path.join(PROJECT_PATH, 'public', 'c'),
        'type': 'css'
    }
}

JS = {
    'core': ('build/core.js', [
        
        'jquery.js',
        'include/jquery.form.js',
        'include/jquery.validate.js',
        'include/jquery.cookie.js',
        'include/jquery.json.js',
        'include/jquery.jeditable.js',
        'include/jquery.input-hint.js',
        'include/jquery.tablesorter.js',
        'include/underscore.js',
        'include/backbone.js',
        
        'quaid/src/core.js',
        'quaid/src/log.js',
        'quaid/src/util.js',
        'quaid/src/widget.js',
        'quaid/src/form.js',
        'quaid/src/validation.js',
        
        'quaid/src/extension/backbone.js',
        'quaid/src/extension/debug.js',
        'quaid/src/extension/notifications.js',
        'quaid/src/extension/editablefield.js',
        
        'lib/base.js',
        'lib/util.js',
        'lib/dialog.js',
        'lib/models.js',
        'lib/forms.js',
        'lib/views.js'
    ]),
    
    'ui': ('build/ui.js', [
        'jqueryui/jquery-ui-1.8.9.custom.min.js'
    ]),
    
    'test': ('build/modules/tests.js',[
        'test/base.js',
        'test/qunit.js',
        'test/test_base.js',
    ]),
    
    'project': ('build/modules/project.js', [
        'lib/modules/project.js'
    ]),
    
    'widgets': ('build/modules/widgets.js', [
        'lib/modules/widgets/feed.js'
    ]),
    
    'file': ('build/modules/file.js', [
        'lib/modules/file/model.js',
        'lib/modules/file/view.js'
    ]),
    
    'image': ('build/modules/image.js', [
        'include/jquery.jcrop.js',
    ]),
    
    'controllers.index': ('build/controllers/index.js', ['controllers/index.js']),
    'controllers.auth': ('build/controllers/auth.js', ['controllers/auth.js']),
    'controllers.invite': ('build/controllers/invite.js', ['controllers/invite.js']),
    
    'controllers.admin': ('build/controllers/admin.js', [
        'controllers/admin/base.js',
        'controllers/admin/report.js'
    ]),
    'controllers.organization': ('build/controllers/organization.js', [
        'controllers/organization/create.js'
    ]),
    'controllers.organization.settings': ('build/controllers/organization.settings.js', [
        'controllers/organization/settings.js',
        'controllers/organization/base.js'
    ]),
    'controllers.organization.project': ('build/controllers/organization.project.js', [
        'controllers/organization/project/project.js',
        'controllers/organization/project/file.js',
        'controllers/organization/project/settings.js',
        'controllers/organization/base.js'
    ])
}

CSS = {
    'core': ('build/core.css', [
        'core/main.css',
        'core/forms.css',
        'core/notifications.css',
        'core/tables.css',
        'core/navigation.css',
        'core/generic.css',
        'core/buttons.css',
        'core/dialog.css',
        'core/widgets.css',
        'widgets/simpleconsole.css',
        'widgets/debugbar.css'
    ]),
    
    'project': ('build/project.css', ['modules/project.css']),
    
    'ui': ('build/ui.css', [
        "jqueryui/jquery.ui.core.css",
        "jqueryui/jquery.ui.resizable.css",
        "jqueryui/jquery.ui.selectable.css",
        "jqueryui/jquery.ui.accordion.css",
        "jqueryui/jquery.ui.autocomplete.css",
        "jqueryui/jquery.ui.button.css",
        "jqueryui/jquery.ui.slider.css",
        "jqueryui/jquery.ui.tabs.css",
        "jqueryui/jquery.ui.datepicker.css",
        "jqueryui/jquery.ui.progressbar.css",
        "jqueryui/jquery.ui.theme.css",
    ]),
    
    'image': ('build/image.css', [
        'modules/image.css',
    ]),
    
    'test': ('build/modules/test.css', [
        'test/qunit.css',
    ]),
    
    'ie': ('build/ie.css', ['core/ie.css']),
    
    'skinny_page': ('build/skinny_page.css', ['modules/skinny_page.css']),
    'medium_page': ('build/medium_page.css', ['modules/medium_page.css']),
    
    'controllers.admin': ('build/controllers.admin.css', [
        'controllers/admin.css'
    ]),
        
    'controllers.organization': ('build/controllers.organization.css', [
        'controllers/organization.css'
    ]),
    
    'controllers.organization.project': ('build/controllers/organization.project.css', [
        'controllers/organization.project/project.css',
        'controllers/organization.project/file.css'
    ])
}