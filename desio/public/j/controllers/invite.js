
;(function($){


Q.InvitePage = Q.Page.extend({
    run: function(){
        this._super.apply(this, arguments);
        
        this.form = this.$('form').RedirectForm({
            defaultData: {
                default_timezone: -(new Date().getTimezoneOffset())/60,
                mode: $('#mode').val()
            },
            resetInitially: true
        });
        
        $('#name').inputHint();
        
        if(this.form.val('mode') == 'login_user')
            this.form.focusFirst();
    }
});


})(jQuery);