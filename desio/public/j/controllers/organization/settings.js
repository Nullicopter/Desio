
;(function($){

Q.GeneralSettingsPage = Q.Page.extend({
    n: {
        users: '#users',
        inviteForm: '#invite-form'
    },
    events: {
        'click .actions a': 'userActionClick',
        'change .role select': 'roleChange'
    },
    
    template: '#invited-template',
    
    init: function(settings){
        this._super(settings);
    },
    
    run: function(){
        var self = this;
        this._super.apply(this, arguments);
        
        this.loader = this.n.users.Loader({});
        
        this.n.inviteForm.AsyncForm({
            submitters: '#invite-form a',
            onSuccess: function(data){
                
                Q.notify(data.results.invited_email + ' was successfully invited.');
                
                var h = _.template($(self.template).html(), data.results);
                
                $('.user-list').prepend($(h));
                
                this.val('email', '');
            }
        });
        $('#invite-form input').inputHint();
        
        this.form = $('#edit-form').AsyncForm({
            validationOptions: {
                rules:{
                    name: 'required'
                }
            },
            
            onSuccess: function(){
                Q.notify('Settings successfully updated');
            }
        });
        this.form.focusFirst();
    },
    
    roleChange: function(e){
        var self = this;
        var targ = $(e.target);
        var par = targ.parents('.user');
        var p = {
            u: par.attr('data-user'),
            role: targ.val()
        };
        $.postJSON(this.settings.roleUrl, p, null, {loader: this.loader});
    },
    
    userActionClick: function(e){
        var self = this;
        var targ = $(e.target);
        var par = targ.parents('.user');
        
        $.postJSON(targ[0].href, {}, function(){
            if(targ.hasClass('remove'))
                par.hide();
            else if(targ.hasClass('approve')){
                targ.parents('.actions').hide();
                par.find('.hidden').show();
            }
        }, {loader: this.loader});
        
        return false;
    }
});


})(jQuery);