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
    }
})

Q.ProjectGeneralSettingsPage = Q.BaseSettingsPage.extend({
    run: function(){
        var self = this;
        this._super.apply(this, arguments);
        _.bindAll(this, 'success', 'del');
        
        this.projectUserModule = $('#project-user-module').ProjectUserModule(this.settings);
        
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
        
        $('#delete-link').click(this.del);
    },
    del: function(){
        var name = this.settings.name;
        if(confirm('Are you sure you want to delete project ' + name)){
            $.postJSON($('#delete-link')[0].href, {}, function(){
                alert(name + ' has been deleted.');
                $.redirect('/');
            });
        }
        return false;
    },
    success: function(data){
        Q.notify('Settings saved successfully.');
    }
});


})(jQuery);