
;(function($){


Q.DashPage = Q.Page.extend({
    run: function(){
        this._super.apply(this, arguments);
        
        
    }
});

Q.FrontPage = Q.Page.extend({
    
    run: function(){
        var self = this;
        this._super.apply(this, arguments);
        
        $('#email').inputHint();
        
        this.form = $('#request-invite form').AsyncForm({
            validationOptions: {
                rules: {email: 'required'},
                messages: {email: 'An email address, please.'}
            },
            onSuccess: function(data){
                $('#request-invite').hide();
                $('#has-invite').show();
            }
        });
    }
});


})(jQuery);