/**
 * JS for viewing/editing the project's settings
 */

;(function($){

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