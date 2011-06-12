"""
"""

from collections import defaultdict as dd
from pylons_common.lib.utils import itemize
from desio.api import CanReadOrg

class ReqUsers(object):
    def __init__(self, real_user=None, user=None):
        self.real_user = real_user
        self.user = user

DATE_FORMAT = '%Y-%m-%d %H:%M:%SZ'
def fdatetime(dt):
    if dt:
        return dt.strftime(DATE_FORMAT)
    return None

def out_invite(inv):
    out = itemize(inv, 'eid', 'role', 'type', 'invited_email')
    out['object'] = inv.object.eid
    
    return out

def out_activity(act):
    #{{id}}', '{{type}}', '{{raw_date}}', '{{human_date}}', '{{tiny_message}}', '{{message}}
    out = itemize(act, 'id', 'type', 'tiny_message')
    out['message'] = act.get_message()
    out['created_date'] = fdatetime(act.created_date)
    return out

def out_file(real_user, filenchange):
    f, change = filenchange
    out = itemize(f, 'eid', 'name', 'path', 'description', 'full_path')
    out.update(out_change(real_user, change))
    return out

def out_file_with_all_changes(real_user, f, with_extracts=True):
    out = itemize(f, 'eid', 'name', 'path', 'full_path')
    out['changes'] = []
    for change in f.get_changes():
        ochange = out_change(real_user, change, with_extracts)
        ochange['digest'] = change.digest
        out['changes'].append(ochange)
    return out

def out_change_extract(extract):
    edict = itemize(extract, 'id', 'order_index', 'extract_type', 'url', 'description')
    edict['url'] = extract.base_url + edict['url']
    return edict

def out_change(real_user, change, with_extracts=True):
    out = itemize(change, 'created_date', 'size', 'url', 'thumbnail_url', 'version', 'number_comments', 'parse_status')
    out['number_comments_open'] = change.get_number_comments(status=u'open')
    out['change_description'] = change.description
    out['change_eid'] = change.eid
    out['file_eid'] = change.entity.eid
    out['version'] = change.version
    out['created_date'] = fdatetime(out['created_date'])
    out['url'] = change.base_url + out['url']
    out['thumbnail_url'] = change.base_url + out['thumbnail_url']
    out['creator'] = user.get().output(change.creator)
    
    if real_user and real_user.is_robot():
        out.update(itemize(change, 'parse_type'))

    if with_extracts:
        out['extracts'] = []
        for ex in change.change_extracts:
            out['extracts'].append(out_change_extract(ex))
        out['extracts'].sort(key=lambda x: x['order_index'])

    return out

def out_comment_status(cs):
    out = itemize(cs, 'created_date', 'status')
    out['created_date'] = fdatetime(out['created_date'])
    out['user'] = cs.user.human_name
    return out

def out_comment(comment):
    out  = itemize(comment, 'eid', 'body', 'position', 'created_date', 'status')
    out['created_date'] = fdatetime(out['created_date'])
    out['in_reply_to'] = comment.in_reply_to and comment.in_reply_to.eid or None
    out['creator'] = user.get().output(comment.creator)
    out['id'] = out['eid']
    out['change'] = comment.change.eid
    out['change_version'] = comment.change.version
    out['extract'] = comment.change_extract and out_change_extract(comment.change_extract) or None
    out['completion_status'] = out_comment_status(comment.completion_status)
    return out

def out_directory(directory):
    return itemize(directory, 'name', 'path', 'eid', 'description', 'full_path')
    
class error:
    class explode: pass
    class explode_no_auth: pass
    class jserror: pass

class invite:
    class create:
        def output(self, i):
            return out_invite(i)

class activity:
    class get:
        def output(self, act):
            return [out_activity(a) for a in act]

class user:
    class pretend: pass
    class masquerade: pass
    class stop_pretending: pass
    
    class edit:
        def output(self, u):
            return user.get().output(u)

    class get:
        def output(self, u):
            d = itemize(u, 'id', 'email', 'username', 'is_active', 'default_timezone')
            d['name'] = u.human_name
            return d
    class set_pref: pass

class organization:
    
    class attach_user: pass
    class remove_user: pass
    class attachment_approval: pass
    class set_user_role: pass
    class is_unique: pass
    
    class edit:
        def output(self, o):
            return organization.get().output(o)
    
    class get:
        def output(self, org):
            if isinstance(org, list):
                return [itemize(o, 'subdomain', 'name', 'eid') for o in org]
            return itemize(org, 'subdomain', 'name', 'eid')
    
    class get_structure:
        def output(self, orgp):
            from desio.model import projects
            org, projs = orgp
            
            org = organization.get().output(org)
            org['projects'] = []
            
            for p in projs:
                proj = project.get().output(p)
                files = p.get_entities(only_type=projects.File.TYPE)
                proj['files'] = [out_file_with_all_changes(self.real_user, f) for f in files]
                org['projects'].append(proj)
            
            return org
    
    class get_users:
        def output(self, org_users):
            return [{'user': user.get().output(ou.user), 'role': ou.role, 'status': ou.status} for ou in org_users]

class project:
    class remove_user: pass
    class set_user_role: pass
    
    class create:
        def output(self, proj):
            return project.get().output(proj)
    
    class edit:
        def output(self, proj):
            return project.get().output(proj)
    
    class get: 
        def output(self, proj):
            return itemize(proj, 'eid', 'name', 'description', 'slug')
    
    class attach_user:
        def output(self, org_user):
            return {'user': user.get().output(org_user.user), 'role': org_user.role, 'status': org_user.status}
    
    class attach_users:
        def output(self, org_users):
            return project.get_users().output(org_users)
    
    class get_users:
        def output(self, org_users):
            return [project.attach_user().output(ou) for ou in org_users]
    
    class get_directory(ReqUsers):
        
        def output(self, d):
            d, files = d
            dir = out_directory(d)
            dir['files'] = [file.get(self.real_user, self.user).output(f) for f in files]
            return dir

    class get_directories:
        def output(self, d):
            p, directories = d
            tree = build_tree(directories)
            out = project().get().output(p)
            out['directories'] = tree
            return out

    class get_files:
        def output(self, files):
            # XXX: This structure could easily be huge in a big project
            # This clearly needs to change and the client needs to be
            # somewhat smarter about which calls it's making and caching
            # the result of each call if possible.
            p, files = files
            return dict((f.full_path, out_file_with_all_changes(self.real_user, f)) for f in files)
        
    class add_directory:
        def output(self, d):
            return project.get_directory().output(d)
    
    class get_structure(ReqUsers):
        
        def output(self, struc):
            res = []
            for d, files in struc:
                res.append(project.get_directory(self.real_user, self.user).output((d, files)))
            return res

class change:
    class get:
        def output(self, ch):
            if isinstance(ch, (list, tuple)):
                return [out_change(self.real_user, c) for c in ch]
            return out_change(self.real_user, ch)
    
    class edit:
        def output(self, ch):
            return out_change(self.real_user, ch)
    
    class upload_extract: pass

class file:
    
    class remove_comment: pass
    
    class set_comment_completion_status:
        def output(self, cs):
            return out_comment_status(cs)

    class upload(ReqUsers):
        def output(self, f):
            return file.get(self.real_user, self.user).output(f)
    
    class get(ReqUsers):
        
        def output(self, files):
            if isinstance(files, list):
                return [out_file(self.real_user, f) for f in files]
            return out_file(self.real_user, files)
            
            
    class add_comment:
        def output(self, c):
            commentable, comment = c
            
            return out_comment(comment)

    class get_comments(ReqUsers):
        def output(self, c):
            commentable, comments = c

            foutput = None
            if commentable._comment_attribute == 'change_extract':
                out = out_change_extract(commentable)
            elif commentable._comment_attribute == 'change':
                out = out_change(self.real_user, commentable, with_extracts=False)
            elif commentable._comment_attribute == 'file':
                out = out_file(self.real_user, (commentable, commentable.get_change()))
            
            children = dd(lambda: [])
            
            for comment in comments:
                children[comment.in_reply_to_id].append(comment)
            
            def get_comments(parent):
                res = []
                for i, comment in enumerate(children[parent]):
                    c = out_comment(comment)
                    c['replies'] = get_comments(comment.id)
                    c['index'] = i
                    res.append(c)
                return res
            
            out['comments'] = get_comments(None)
            
            return out
        
def build_tree(directories):
    directories.sort(key=lambda d: d.full_path)
    # we need a root object to have a single point from which
    # we can retrieve all the children directories.
    root = {'children': []}
    lookup = {u"/": root}
    # these are sorted by path, so everything fits inside the "/"
    # and I'll add them to the quick_path_lookup as I add them
    # to speedup node lookup and make it O(n) at the expense of
    # 2x memory usage, who cares right now...
    for directory in directories:
        outdir = out_directory(directory)
        outdir['children'] = []
        lookup[directory.path]['children'].append(outdir)
        lookup[directory.full_path] = outdir
    
    del lookup
    return root['children']
