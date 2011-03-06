/**
 * JS for viewing/editing the project's settings
 */

;(function($){

Q.BaseSettingsPage = Q.Page.extend({
    n: {
        root: '#root-directory',
        sidepanel: '#sidepanel'
    },
    
    run: function(){
        this._super.apply(this, arguments);
        this.n.sidepanel.Sidepanel({
            collapsable: false
        });
        
        var root = new Q.Directory({
            name: '',
            path: '/', full_path: '/',
            children: this.settings.tree.directories
        });
        
        this.rootObject = root;
        
        this.root = this.n.root.DirectoryTreeView({model: root});
        this.root.render();
    }
})
Q.ProjectUserSettingsPage = Q.BaseSettingsPage.extend({
    run: function(){
        var self = this;
        this._super.apply(this, arguments);
        
        this.projectUserModule = $('#project-user-module').ProjectUserModule(this.settings);
    }
});

Q.ProjectGeneralSettingsPage = Q.BaseSettingsPage.extend({
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