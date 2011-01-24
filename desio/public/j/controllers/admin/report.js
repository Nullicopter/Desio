
;(function($){


Q.GenericReportPage = Q.Page.extend({
    init: function(settings){
        this._super(settings);
    },
    
    run: function(){
        this._super.apply(this, arguments);
        
        this.table = this.$('.tablesorter').tablesorter();
    }
});


})(jQuery);