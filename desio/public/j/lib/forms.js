;/*******************************************************************************
 *
 ******************************************************************************/

(function($){

Q.Editable = Class.extend('Editable',{
    init: function(c, s){
        var defs = {
            url: null,
            id: 'key',
            name: 'value',
            submit: 'save',
            tooltip: 'Click to edit...',
            ajaxoptions: {dataType: 'json'},
            onfinished: function(){}
        };
        
        function nop(){}
        this.cb = {
            callback: nop,
            onerror: nop,
            onreset: nop,
            onedit: nop
        };
        
        for(var k in this.cb)
            if(k in s) this.cb[k] = s[k];
        
        this._super(c, $.extend({}, defs, s));
        
        var self = this;
        function bind(fn){
            var o = self[fn];
            self[fn] = function(){
                var arr = [this].concat(Array.prototype.slice.call(arguments));
                return o.apply(self, arr);
            }
        }
        
        var fns = {
            'onSuccess': 'callback',
            'onError': 'onerror',
            'onEdit': 'onedit',
            'onReset': 'onreset'
        };
        
        for(var k in fns){
            bind(k);
            this.settings[fns[k]] = this[k];
        }
        
        this.container.editable(this.settings.url, this.settings);
    },
    
    _callCb: function(name, args){
        return this.cb[name].apply(this, args);
    },
    
    onFinished: function(){
        if($.isFunction(this.settings.onfinished))
            return this.settings.onfinished.apply(this, arguments);
        return null;
    },
    
    onSuccess: function(editable, data, settings){
        this.onFinished.apply(this, arguments);
        
        return this._callCb('callback', arguments);
    },
    
    onReset: function(editable, data, settings){
        this.onFinished(editable, data, settings);
        return this._callCb('onreset', arguments);
    },
    
    onError: function(editable, data, settings){
        this.onFinished(editable, data, settings);
        return this._callCb('onerror', arguments);
    },
    
    onEdit: function(editable, data, settings){
        return this._callCb('onedit', arguments);
    }
});

})(jQuery);


