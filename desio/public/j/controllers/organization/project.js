
;(function($){


Q.ProjectCreatePage = Q.Page.extend({
    init: function(settings){
        this._super(settings);
    },
    
    run: function(){
        this._super.apply(this, arguments);
        
        this.form = this.$('form').RedirectForm({
            validationOptions: {
                rules:{
                    name: 'required',
                    description: {required: false}
                }
            }
        });
        this.form.focusFirst();
    }
});


})(jQuery);