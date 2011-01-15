
;(function($){


Q.CreatePage = Q.Page.extend({
    init: function(settings){
        settings.pageSelector = '#small-page';
        this._super(settings);
    },
    
    run: function(){
        this._super.apply(this, arguments);
        
        this.form = this.$('form').RedirectForm({
            validationOptions: {
                rules:{
                    company_name: 'required',
                    subdomain: 'required',
                    name: 'required',
                    email: 'required',
                    password: 'required',
                    confirm_password: 'required'
                }
            },
            defaultData: { default_timezone: -(new Date().getTimezoneOffset())/60 },
            resetInitially: true
        });
        this.form.focusFirst();
        
        $('#create-box :text').inputHint();
    }
});


})(jQuery);