
;(function($){

Q.Sidepanel = Q.Module.extend('Sidepanel', {
    
    init: function(container, settings){
        var defs = {
            tabs: '#sidepanel-tabs',
            panels: '#sidepanels',
            collapsable: true,
            collapseButton: '#sidepanel-collapse',
            collapsePreference: null,
            collapseInitially: false,
            collapseClass: 'collapsed',
            content: '#content'
        };
        this._super(container, $.extend({}, defs, settings));
        _.bindAll(this, 'toggleCollapse');
        
        this.settings.content = $.getjQueryObject(this.settings.content);
        this.settings.tabs = $.getjQueryObject(this.settings.tabs);
        this.settings.panels = $.getjQueryObject(this.settings.panels);
        this.settings.collapseButton = $.getjQueryObject(this.settings.collapseButton);
        
        this.settings.tabs.Tabs({
            panels: this.settings.panels.children()
        });
        
        if(this.settings.collapsable){
            this.settings.collapseButton.show();
            this.settings.collapseButton.click(this.toggleCollapse);
            this.collapse(this.settings.collapseInitially);
        }
        else
            this.settings.collapseButton.hide();
    },
    setPref: function(val){
        if(this.settings.collapsePreference){
            $.postJSON(window.PREFS_URL, {
                key: this.settings.collapsePreference,
                value: ''+val
            });
        }
    },
    collapse: function(doit, trigger){
        if(doit){
            this.container.addClass(this.settings.collapseClass);
            this.settings.content.addClass(this.settings.collapseClass);
            this.settings.collapseButton.attr('title', 'Expand the sidebar');
            if(trigger) {
                this.setPref(true);
                this.trigger('change:collapse', true);
            }
        }
        else{
            this.container.removeClass(this.settings.collapseClass);
            this.settings.content.removeClass(this.settings.collapseClass);
            this.settings.collapseButton.attr('title', 'Collapse the sidebar');
            if(trigger) {
                this.setPref(false);
                this.trigger('change:collapse', false);
            }
        }
    },
    
    isCollapsed: function(){
        return this.container.hasClass(this.settings.collapseClass);
    },
    
    toggleCollapse: function(){
        this.collapse(!this.container.hasClass(this.settings.collapseClass), true);
        return false;
    }
});

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
        this.tabs = this.$('.'+this.settings.tabClass);
        this.select(cur.length ? parseInt(cur.attr('rel')) : 0);
    },
    
    onTabClick: function(e){
        var target = $(e.target);
        if(!target.is('a')) target = target.parent(); //could be an inner span
        this.select(parseInt(target.attr('rel')));
        return false;
    },
    
    select: function(index){
        var tabs = this.tabs;
        tabs.removeClass(this.settings.currentClass);
        
        tabs.eq(index).addClass(this.settings.currentClass);
        
        this.settings.panels.hide();
        this.settings.panels.eq(index).show();
    }
});

Q.OrgHomePage = Q.Page.extend({
    n: {
        sidepanel: '#sidepanel'
    },
    events:{
    },
    run: function(){
        var self = this;
        this._super.apply(this, arguments);
        //_.bindAll(this, 'viewVersion', 'addVersion');
        
        this.n.sidepanel.Sidepanel({
            collapsable: false
        });
    }
});

})(jQuery);