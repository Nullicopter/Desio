
;(function($){


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