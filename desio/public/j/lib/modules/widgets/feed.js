
/***
 * stuff related to the feed widget
 */

;(function($){

Q.FeedCollection = Q.AppendCollection.extend({
    model: Q.Model,
    
    init: function(m, options){
        this.urls.read = $.extendUrl(this.urls.read, _.extract(options, ['organization', 'project', 'entity', 'u']))
    },
    
    urls: {
        read: API_URL('/activity/get')
    }
});

Q.ActivityView = Q.View.extend({
    tagName: "div",

    template: '#activity-template',
    
    formatters: {
        'human_date': 'relativetime'
    },

    init: function(container, settings) {
        this._super(container, settings);
        _.bindAll(this, 'render');
        this.model.view = this;
    },
    
    render: function() {
        var attr = $.extend({}, this.model.attributes);
        attr['raw_date'] = attr['human_date'] = attr['created_date'];
        
        for(var k in attr)
            if(k in this.formatters)
                attr[k] = Q.DataFormatters.get(this.formatters[k], attr[k]);
        
        html = _.template($(this.template).html(), attr);
        this.container.html(html);
        
        return this;
    }
});

Q.FeedView = Q.View.extend('FeedView', {
    events: {
        'click .more a': 'clickMore'
    },
    
    n: {
        feed: '.feed-list'
    },
    
    init: function(container, settings) {
        this._super(container, settings);
        _.bindAll(this, 'render', 'addItem');
        this.model.view = this;
        this.model.bind('add', this.addItem);
        
        this.container.Loader({
            model: this.model,
            location: {position: 'absolute', right: 72, bottom: -32}
        })
    },
    
    clickMore: function(m){
        var items = this.n.feed.find('.item');
        var date = items.eq(items.length-1).attr('data-date');
        this.model.more(date, 5);
        return false;
    },
    
    addItem: function(m){
        $.log('add', m, this.n.feed);
        var view = new Q.ActivityView({model: m});
        this.n.feed.append(view.render().el);
    }
});

})(jQuery);