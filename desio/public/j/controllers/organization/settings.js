
;(function($){


Q.GeneralSettingsPage = Q.Page.extend({
    init: function(settings){
        this._super(settings);
    },
    
    run: function(){
        this._super.apply(this, arguments);
        
        this.form = this.$('form').AsyncForm({
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
    }
});

Q.UserSettingsPage = Q.Page.extend({
    n: {
        users: '#users'
    },
    events: {
        'click .actions a': 'userActionClick',
        'change .role select': 'roleChange'
    },
    
    init: function(settings){
        this._super(settings);
    },
    
    run: function(){
        this._super.apply(this, arguments);
        
        this.loader = this.n.users.Loader({});
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