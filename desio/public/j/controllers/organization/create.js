
;(function($){

Q.TextGhost = Q.Module.extend('TextGhost', {
    singleKeys:{
        8: true,
        9: true,
        45: true,
        95: true
    },
    init: function(c, s){
        _.bindAll(this, 'change', 'showHint');
        var defs = {
            ghost: null
        };
        this._super(c, $.extend({}, defs, s));
        
        this.settings.ghost = $.getjQueryObject(this.settings.ghost);
        
        this.original = this.settings.ghost.text();
        
        this.container.keydown(this.change);
        this.container.focus(this.change);
        this.container.blur(this.showHint);
    },
    
    showHint: function(){
        if(!this.container.val())
            this.settings.ghost.text(this.original);
    },
    
    change: function(e){
        
        //8, 9, 48-57, 65-90, 45, 95, 97-122
        if(e.keyCode && !(e.keyCode in this.singleKeys) &&
           (e.keyCode < 48 || e.keyCode > 57) && (e.keyCode < 65 || e.keyCode > 90) && (e.keyCode < 97 || e.keyCode > 122)){
            e.stopPropagation();
            return false;
        }
        
        var self = this;
        setTimeout(function(){
            self.settings.ghost.text(self.container.val());
        }, 10);
    }
});

Q.ValidChecker = Q.Module.extend('ValidChecker', {
    init: function(c, s){
        _.bindAll(this, 'change', 'handleSuccess', 'handleError');
        var defs = {
            validElement: null,
            url: '/api/v1/organization/is_unique'
        };
        this._super(c, $.extend({}, defs, s));
        
        this.settings.validElement = $.getjQueryObject(this.settings.validElement);
        
        this.container.keyup(this.change);
        this.form = this.container.parents('form');
    },
    
    handleSuccess: function(data){
        this.settings.validElement.removeClass('subdomain-error').show();
    },
    handleError: function(data){
        this.settings.validElement.addClass('subdomain-error').show();
    },
    
    change: function(e){
        if(e.keyCode != 8 && e.keyCode < 32) return;
        
        var self = this;
        $.ajax({
            url: this.settings.url,
            data: {subdomain: this.container.val()},
            success: this.handleSuccess,
            error: this.handleError,
            dataType: 'json',
            form: this.form
        });
    }
});

Q.CreatePage = Q.Page.extend({
    
    run: function(){
        this._super.apply(this, arguments);
        
        $('#create-box :text').inputHint();
        
        $('#subdomain').TextGhost({ghost: '#subdomain-ghost span'});
        $('#subdomain').ValidChecker({validElement: '#subdomain-feedback'});
        
        this.form = this.$('form').RedirectForm({
            validationOptions: {
                rules:{
                    company_name: {asyncError:true},
                    subdomain: {asyncError:true},
                    name: {asyncError:true},
                    email: {asyncError:true},
                    password: {asyncError:true},
                    confirm_password: {asyncError:true}
                }
            },
            defaultData: { default_timezone: -(new Date().getTimezoneOffset())/60 },
            resetInitially: true
        });
        this.form.focusFirst();
    }
});


})(jQuery);