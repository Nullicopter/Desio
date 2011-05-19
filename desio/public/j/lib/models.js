
/***
 * Models relating to a file.
 */

;(function($){

Q.AppendCollection = Q.Collection.extend({
    model: Q.Model,
    
    urls: {
        //override this...
    },
    
    url: function(method){
        if(!this.urls[method])
            $.error('No url for', method, this);
        else
            return this.urls[method];
        return null;
    },
    
    toJSON: function(method){
        return this._params;
    },
    
    more: function(offset, limit){
        this._params = {
            offset: offset,
            limit: limit
        };
        
        var self = this;
        Backbone.sync('read', this, function(data){
            for(var i in data.results)
                self.add(data.results[i]);
        });
    }
});

})(jQuery);