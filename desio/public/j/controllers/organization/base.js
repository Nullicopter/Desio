
;(function($){

Q.Tabs = Q.Module.extend('Tabs', {
    
    events: {
        'click a': 'onTabClick'
    },
    
    init: function(container, settings){
        var defs = {
            panels: null,
            currentClass: 'current',
            tabClass: 'tab'
        };
        this._super(container, $.extend({}, defs, settings));
        
        var cur = this.$('.'+this.settings.currentClass);
        this.select(cur.length ? parseInt(cur.attr('rel')) : 0)
    },
    
    onTabClick: function(e){
        var target = $(e.target);
        this.select(parseInt(target.attr('rel')));
        return false;
    },
    
    select: function(index){
        var tabs = this.$('.'+this.settings.tabClass);
        tabs.removeClass(this.settings.currentClass);
        
        tabs.eq(index).addClass(this.settings.currentClass);
        
        this.settings.panels.hide();
        this.settings.panels.eq(index).show();
    }
});

$(function(){
    $('#sidepanel-tabs').Tabs({
        panels: $('#sidepanels').children()
    });
});


})(jQuery);