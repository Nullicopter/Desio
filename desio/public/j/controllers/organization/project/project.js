/**
 * JS for viewing or creating a project 
 */

;(function($){

Q.DirectoryTreeView = Q.View.extend('DirectoryTreeView', {
    template: '#dir-tree-template',
    className: 'dir-tree',
    
    init: function(c, set){
        this._super(c, set);
        _.bindAll(this, 'addDirectory', 'changeCurrent');
        
        this.model.get('children').bind('add', this.addDirectory);
        this.model.bind('change:current', this.changeCurrent)
    },
    
    render: function(){
        this.children = this.$('.children');
        
        if(!this.children.length){
            this._super();
            this.children = this.$('.children');
        }
        if(!this.model.isRoot())
            this.children.hide();
        
        var children = this.model.get('children');
        for(var i = 0; i < children.length; i++)
            this.addDirectory(children.models[i]);
        
        return this;
    },
    
    changeCurrent: function(m){
        //if(this.model.get('current')){
            if(!this.$('.current').length) this.container.addClass('current');
            this.children.show();
        //}
    },
    
    addDirectory: function(m){
        var view = new Q.DirectoryTreeView({model: m});
        this.children.append(view.render().el);
        
        if(this.settings.emptyInfo) this.settings.emptyInfo.hide();
    }
});

Q.ViewProjectPage = Q.Page.extend({
    events:{
        'click .add-directory-link': 'addDirectory',
        'click .user-invite': 'popShareDialog'
    },
    n: {
        root: '#root-directory',
        sidepanel: '#sidepanel',
        feed: '.activity-feed',
        emptyInfo: '#no-dir-info',
        shareDialog: '#share-dialog',
        shareEmail: '#email',
        inviteForm: '#invite-form',
        objectName: '.object-name',
        projectName: '.project-name',
        editHideShow: '#project-settings-link, .project-heading .label'
    },
    run: function(){
        var self = this;
        this._super.apply(this, arguments);
        
        this.filesModule = $(this.settings.module).FilesModule(this.settings);
        
        this.n.sidepanel.Sidepanel({
            collapsePreference: this.settings.collapsePreference,
            collapseInitially: this.settings.collapseInitially
        });
        
        var root = new Q.Directory({
            name: '',
            path: '/', full_path: '/',
            children: this.settings.tree.directories
        });
        
        this.rootObject = root;
        this.directories = root.get('children'); //will be a Q.Directories obj
        
        this.root = this.n.root.DirectoryTreeView({
            emptyInfo: this.n.emptyInfo,
            model: root
        });
        this.root.render();
        
        //need to walk the tree to find the current path
        var dir = this.currentDirectory = this.directories.findPath(this.settings.path);
        if(dir) dir.set({current: true});
        else this.currentDirectory = root;
        
        this.feed = new Q.FeedCollection([], {project: this.settings.project});
        this.n.feed.FeedView({model: this.feed});
        
        this.setupInvites();
        
        if(this.settings.userRole == 'admin'){
            this.n.projectName.Editable({
                url: this.settings.editUrl,
                name: 'name',
                tooltip: 'Click to edit the project name...',
                onedit: function(){
                    self.n.editHideShow.hide();
                },
                onfinished: function(){
                    self.n.editHideShow.show();
                },
                callback: function(editable, data, settings){
                    $(editable).text(data.results.name);
                }
            });
            this.n.objectName.Editable({
                url: this.settings.directoryEditUrl,
                name: 'name',
                tooltip: "Click to edit the filder's name...",
                callback: function(editable, data, settings){
                    $(editable).text(data.results.name);
                    $.redirect(data.results.name);
                }
            });
        }
    },
    
    setupInvites: function(){
        //share stuff
        this.n.shareEmail.inputHint();
        this.shareDialog = this.n.shareDialog.Dialog({width: 500});
        
        this.n.inviteForm.AsyncForm({
            onSuccess: function(data){
                Q.notify(data.results.invited_email + ' has been invited!');
                this.val('email', '');
            }
        });
    },
    
    popShareDialog: function(){
        this.shareDialog.open();
        return false;
    },
    
    addDirectory: function(e){
        var l = $(e.target);
        var n = prompt('What do you want to name this folder?');
        
        //this will allow for adding children to the current directory
        //var dirs = this.currentDirectory.get('children');
        var dirs = this.directories;
        var path = this.rootObject.path; //this.settings.path;
        for(var i = 0; i < dirs.length; i++)
            if(dirs.models[i].get('name') == n){
                n = null;
                Q.warn('Directory already exists!');
            }
        
        if(n){
            $.postJSON(l[0].href, {
                path: $.pathJoin(path, n)
            }, function(data){
                data = data.results;
                $.log(data);
                dirs.add(data);
            });
        }
        return false;
    }
});

Q.ProjectCreatePage = Q.Page.extend({
    run: function(){
        var self = this;
        this._super.apply(this, arguments);
        _.bindAll(this, 'success', 'synced');
        this.form = this.$('#new-form').AsyncForm({
            validationOptions: {
                rules:{
                    name: 'required',
                    description: {required: false}
                }
            },
            submitters: '#create-project-link',
            onSuccess: function(data){self.success(data);}
        });
        this.form.getElement('name').focus();
        
        this.projectUserModule = $('#project-user-module').ProjectUserModule(this.settings);
        if(this.projectUserModule)
            this.projectUserModule.bind('synced', this.synced);
    },
    
    success: function(data){
        $.log(data);
        this.form.loader.startLoading();
        this.project = data.results;
        if(this.projectUserModule)
            this.projectUserModule.sync(data.results.eid);
        else
            this.synced();
    },
    
    synced: function(){
        $.log('redirecting to /project/'+this.project.slug);
        
        this.form.loader.stopLoading();
        $.redirect('/project/'+this.project.slug);
    }
});


})(jQuery);