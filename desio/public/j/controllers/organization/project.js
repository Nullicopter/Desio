
;(function($){

Q.TabView = Q.View.extend({
    
    template: '#tab-template',
    className: 'tab',
    
    init: function(){
        //gets selectedVersion model in the settings.
        _.bindAll(this, 'clickTab', 'changeVersion');
        this._super.apply(this, arguments);
        this.container.click(this.clickTab);
        
        this.settings.selectedVersion.bind('change:version', this.changeVersion)
    },
    
    changeVersion: function(m){
        if(m.get('version') == this.model.get('version'))
            this.container.addClass('selected');
        else
            this.container.removeClass('selected');
    },
    
    clickTab: function(){
        this.settings.selectedVersion.set({version: this.model.get('version')});
    },
    
    render: function(){
        this.container.html(_.template($(this.template).html(), this.model.attributes));
        return this;
    }
});

Q.ViewFilePage = Q.Page.extend({
    n: {
        tabs: '#tabs'
    },
    events:{
    },
    run: function(){
        
        /**
         * If you want to upload on this page, use the Q.FileUploader
         * and use the forcedName param
         */
        var self = this;
        this._super.apply(this, arguments);
        _.bindAll(this, 'viewVersion', 'addVersion');
        
        this.versions = new Q.FileVersions([]);
        this.selectedVersion = new Backbone.Model({});
        
        //do setup and binding here
        this.selectedVersion.bind('change:version', this.viewVersion);
        this.versions.bind('add', this.addVersion);
        
        
        //add the versions to the model
        for(var i = 0; i < this.settings.versions.length; i++){
            this.versions.add(this.settings.versions[i]);
        }
        this.selectedVersion.set({version: this.settings.versions[0].version});
    },
    
    addVersion: function(m){
        $.log('add version', m);
        this.n.tabs.append(new Q.TabView({
            model: m,
            selectedVersion: this.selectedVersion
        }).render().container);
    },
    
    viewVersion: function(m){
        var version = m.get('version');
        $.log('View version', version);
    }
});

Q.ViewProjectPage = Q.Page.extend({
    events:{
        'click #add-directory-link': 'addDirectory'
    },
    run: function(){
        var self = this;
        this._super.apply(this, arguments);
        
        this.filesModule = $(this.settings.module).FilesModule(this.settings);
    },
    
    addDirectory: function(e){
        var l = $(e.target);
        var n = prompt('What do you want to name this directory?');
        
        var dirs = this.filesModule.directories;
        for(var i = 0; i < dirs.length; i++)
            if(dirs.models[i].get('name') == n){
                n = null;
                Q.warn('Directory already exists!');
            }
        
        if(n){
            $.postJSON(l[0].href, {
                path: $.pathJoin(this.settings.path, n)
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
        this.form.focusFirst();
        
        this.projectUserModule = $('#project-user-module').ProjectUserModule(this.settings);
        this.projectUserModule.bind('synced', this.synced);
    },
    
    success: function(data){
        $.log(data);
        this.form.loader.startLoading();
        this.project = data.results;
        this.projectUserModule.sync(data.results.eid);
    },
    
    synced: function(){
        $.log('redirecting to /project/'+this.project.slug);
        
        this.form.loader.stopLoading();
        $.redirect('/project/'+this.project.slug);
    }
});

Q.ProjectUserSettingsPage = Q.Page.extend({
    run: function(){
        var self = this;
        this._super.apply(this, arguments);
        
        this.projectUserModule = $('#project-user-module').ProjectUserModule(this.settings);
    }
});

Q.ProjectGeneralSettingsPage = Q.Page.extend({
    run: function(){
        var self = this;
        this._super.apply(this, arguments);
        _.bindAll(this, 'success');
        
        this.form = this.$('#edit-form').AsyncForm({
            validationOptions: {
                rules:{
                    name: 'required',
                    description: {required: false}
                }
            },
            onSuccess: function(data){self.success(data);}
        });
        this.form.focusFirst();
    },
    
    success: function(data){
        Q.notify('Settings saved successfully.');
    }
});


})(jQuery);