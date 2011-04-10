
;(function($){


Q.InvitePage = Q.Page.extend({
    run: function(){
        this._super.apply(this, arguments);
        
        this.form = this.$('form').RedirectForm({
            defaultData: { default_timezone: -(new Date().getTimezoneOffset())/60 },
            resetInitially: true
        });
        
        $('#name').inputHint();
    }
});


})(jQuery);