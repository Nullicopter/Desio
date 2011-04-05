import turbomail, os, re
from turbomail import Message

from datetime import datetime
from collections import defaultdict
import pylons
from mako.lookup import TemplateLookup
from desio.lib.helpers import url_for
from desio.model import users

from pylons_common.lib.log import create_logger
logger = create_logger('desio.utils.email')

EMAIL_TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'templates', 'emails')
EMAIL_TEMPLATE_LOOKUP = TemplateLookup(directories=[EMAIL_TEMPLATES_DIR])

def absolute_url_for(*args, **kwargs):
    subdomain = kwargs.get('subdomain')
    if subdomain:
        url = pylons.config.get('subdomain_url') % (subdomain,)
        del kwargs['subdomain']
    else:
        url = pylons.config.get('pylons_url')
    return str(url) + url_for(*args, **kwargs)

def line_reduce(s):
    # this reduces any number of line breaks of 3 or more to a max of 2
    ws = re.compile("\s{3,}")
    return ws.sub("\n\n", s)

def send(to, template_path, context=None, reply_to='', bcc=None):
    """
    Send message based on a mako template. The recipient is automatically added
    to the context_dict that gets fed to the template.
    """

    t = EMAIL_TEMPLATE_LOOKUP.get_template(template_path)
    
    context = context or {}
    context['url_for'] = absolute_url_for
    
    if isinstance(to, users.User):
        context['user'] = to
        to = to.email

    pc = pylons.config
    
    subject = t.get_def('subject').render_unicode(**context).strip()
    body = line_reduce(t.render_unicode(**context).strip())
    f = (pc['mail.message.author_name'], pc['mail.message.author'])
    
    reroute = pc.get('mail.reroute')
    if reroute:
        old_to = to
        to = reroute
    
    lmsg = 'Sending email from %s to %s.' % (f, to)
    if reroute:
        lmsg += ' Message was rerouted from %s' % old_to
    logger.info(lmsg)
    
    msg = Message(f, to, subject, plain=body)
    msg.plain=body
    msg.bcc = bcc
    msg.send()
    