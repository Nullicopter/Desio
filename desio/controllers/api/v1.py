"""
"""

from collections import defaultdict as dd
from pylons_common.lib.utils import itemize
from desio.api import CanReadOrg

DATE_FORMAT = '%Y-%m-%d %H:%M:%SZ'
def fdatetime(dt):
    return dt.strftime(DATE_FORMAT)

def out_change_extract(extract):
    edict = itemize(extract, 'order_index', 'extract_type', 'url', 'description')
    edict['url'] = '/' + edict['url']
    return edict

def out_change(change, with_extracts=True):
    out = itemize(change, 'created_date', 'size', 'url', 'thumbnail_url', 'version')              
    out['change_description'] = change.description
    out['change_eid'] = change.eid
    out['version'] = change.version
    out['created_date'] = fdatetime(out['created_date'])            
    out['url'] = '/'+out['url']
    out['thumbnail_url'] = '/'+out['thumbnail_url']

    if with_extracts:
        out['extracts'] = []
        for ex in change.change_extracts:
            out['extracts'].append(out_change_extract(ex))

    return out

def out_comment(comment):
    out  = itemize(comment, 'id', 'eid', 'body', 'position', 'created_date')
    out['created_date'] = fdatetime(out['created_date'])
    out['in_reply_to'] = comment.in_reply_to and comment.in_reply_to.eid or None
    out['creator'] = user.get().output(comment.creator)
    return out

def out_directory(directory):
    return itemize(directory, 'name', 'path', 'eid', 'description', 'full_path')

class error:
    class explode: pass
    class explode_no_auth: pass
    class jserror: pass

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
    
    class edit:
        def output(self, o):
            return organization.get().output(o)
    
    class get:
        def output(self, org):
            return itemize(org, 'subdomain', 'name')
    
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
    
    class get_directory:
        
        def output(self, d):
            d, files = d
            dir = out_directory(d)
            dir['files'] = [file.get().output(f) for f in files]
            return dir

    class get_directories:
        def output(self, d):
            p, directories = d
            tree = build_tree(directories)
            out = project().get().output(p)
            out['directories'] = tree
            return out
        
    class add_directory:
        def output(self, d):
            return project.get_directory().output(d)
    
    class get_structure:
        
        def output(self, struc):
            res = []
            for d, files in struc:
                res.append(project.get_directory().output((d, files)))
            return res

class file:

    class upload:
        def output(self, f):
            return file.get().output(f)
    
    class get:
        def get_file(self, filenchange):
            f, change = filenchange
            out = itemize(f, 'eid', 'name', 'path', 'description', 'full_path')
            out.update(out_change(change))
            return out
        
        def output(self, files):
            if isinstance(files, list):
                return [self.get_file(f) for f in files]
            return self.get_file(files)
            
            
    class add_comment:
        def output(self, c):
            commentable, comment = c

            foutput = None
            if commentable._comment_attribute == 'change_extract':
                out = out_change_extract(commentable)
            elif commentable._comment_attribute == 'change':
                out = out_change(commentable, with_extracts=False)

            out['comment'] = out_comment(comment)

            return out

    class get_comments:
        def output(self, c):
            commentable, comments = c

            foutput = None
            if commentable._comment_attribute == 'change_extract':
                out = out_change_extract(commentable)
            elif commentable._comment_attribute == 'change':
                out = out_change(commentable, with_extracts=False)
            
            children = dd(lambda: [])
            
            for comment in comments:
                children[comment.in_reply_to_id].append(comment)
            
            def get_comments(parent):
                res = []
                for comment in children[parent]:
                    c = out_comment(comment)
                    c['replies'] = get_comments(comment.id)
                    res.append(c)
                return res
            
            out['comments'] = get_comments(None)
            
            return out
        
def build_tree(directories):
    directories.sort(key=lambda d: d.path)
    # we need a root object to have a single point from which
    # we can retrieve all the children directories.
    root = {'children': []}
    lookup = {u"/": root}
    # these are sorted by path, so everything fits inside the "/"
    # and I'll add then to the quick_path_lookup as I add them
    # to speedup node lookup and make it O(1) at the expense of
    # 2x memory usage, who cares right now...
    for directory in directories:
        outdir = project.get_directory().get_dir(directory)
        outdir['children'] = []
        lookup[directory.path]['children'].append(outdir)
        lookup[directory.full_path] = outdir

    del lookup
    return root['children']
