;/*******************************************************************************
 *
 ******************************************************************************/

(function($){


//Overrides
Q.Loader.defaults.image = '/i/loaders/16x16_arrows.gif';
Q.AsyncForm.defaults.autoGenValidationOptions = true;

//Mustache-like delimiters!
_.templateSettings = {
  interpolate : /\{\{(.+?)\}\}/g
};

//TODO: put this in quaid
Q.View.prototype.renderTemplate = function(attributes){
    this.container.html(_.template($(this.template).html(), attributes));
    return this;
};
Q.View.prototype.render = function(){
    return this.renderTemplate(this.model.attributes);
}

// using call as a hack so the resulting objects are of type Backbone.Collection
// making it so isinstance still works.
var _Collection = Class.extend.call(Backbone.Collection, Backbone.Collection.prototype);
Q.Collection = _Collection.extend({
    _ctor: function(models, settings){
        
        this.settings = settings;
        
        //call backbone's constructor
        Backbone.Collection.call(this, models, settings);
        
        // call the quaid constructor
        if ( $.isFunction(this.init) )
            this.init.call(this, models, settings);
    },
    init: function(){},
    
    removeAll: function(){
        var models = _.clone(this.models);
        for(var i = 0; i < models.length; i++)
            this.remove(models[i]);
    },
    
    /**
     * Called by Backbone.sync. grabs a url from this.settings.urls based on the method
     */
    url: function(method) {
        if(!this.urls || !this.urls[method])
            $.error("Place a url map in the settings of your model! " + this + " needs a url for " + method);
        else{
            var url = this.urls[method];
            return $.isFunction(url) ? url() : url;
        }
        throw new Error('Place a url map in the settings of your model!');
    }
});

// using call as a hack so the resulting objects are of type Backbone.Model
// making it so isinstance still works.
var _Model = Class.extend.call(Backbone.Model, Backbone.Model.prototype);
Q.Model = _Model.extend({
    
    _ctor: function(attributes, settings){
        
        this.settings = $.extend({}, Q.Model.defaults, settings);
        
        //call backbone's constructor
        Backbone.Model.call(this, attributes, this.settings);
        
        // call the quaid constructor
        if ( $.isFunction(this.init) )
            this.init.call(this, attributes, this.settings);
    },
    
    init: function(){},
    
    /**
     * Upon create, update, read, this is called with the server's response.
     * You are supposed to return an object that will be passed to this
     * model's set function.
     *
     * Default it sets nothing returning an empty object.
     */
    parse: function(data){
        data = data.results || data;
        if(data.eid)
            return {id: data.eid, eid: data.eid};
        
        return {};
    },
    
    /**
     * Called by Backbone.sync. Default behaviour is to reuturn all the attributes.
     */
    toJSON: function(){
        return $.extend({}, this.attributes);
    },
    
    /**
     * Called by Backbone.sync. grabs a url from this.settings.urls based on the method
     */
    url: function(method) {
        if(!this.urls || !this.urls[method])
            $.error("Place a url map in the settings of your model! " + this + " needs a url for " + method);
        else{
            var url = this.urls[method];
            return $.isFunction(url) ? url() : url;
        }
        throw new Error('Place a url map in the settings of your model!');
    },
    
    /**
     * returns GET/POST, etc based on a CRUD word from Backbone.sync
     */
    httpMethod: function(method){
        return this.settings.methods[method];
    }
});

Q.Model.methods = {
    create: 'POST',
    read: 'GET',
    update: 'POST',
    'delete': 'POST'
};

//end stuff to put in quaid

//backbone sync override
Backbone.sync = function(method, model, success, error) {
    var modelJSON = model.toJSON(method);
    
    // Default JSON-request options.
    var params = {
        url: model.url(method),
        type: Q.Model.methods[method],
        data: modelJSON,
        dataType: 'json',
        success: success,
        error: error
    };
    
    // Make the request.
    $.ajax(params);
};


Q.defaultValidationOptions = {
    errorPlacement: function(error, element) {
        var errc = $('<div class="error-container"></div>');
        
        errc.append(error);
        
        element.parent().append(errc);
    },
    success: function(element){
    }
};

Q.Page = Q.Module.extend({
    init: function(settings){
        var defs = {
            pageSelector: '#page'
        };
        this.args = arguments;
        this.settings = $.extend({}, defs, settings);
        window.PAGE = this;
    },
    
    readyrun: function(){
        var self = this;
        var args = arguments;
        $(document).ready(function(){
            self.run.apply(self, args);
        });
    },
    
    run: function(){
        this.container = $(this.settings.pageSelector);
        this.delegateEvents();
        this.cacheNodes();
    }
});

Q.RedirectForm = Q.AsyncForm.extend('RedirectForm', {
    _onSuccess: function(data){
        this._super.apply(this, arguments);
        
        if(data && data.results && data.results.url)
            $.redirect(data.results.url);
    }
});

Q.ReloadForm = Q.AsyncForm.extend('ReloadForm', {
    _onSuccess: function(data){
        this._super.apply(this, arguments);
        $.reload();
    }
});

$.fn.reloadLink = function(){
    this.click(function(){
        $.post(this.href, {}, function(){
            $.reload();
        });
        return false;
    });
};

$.postJSON = function( url, data, callback, opts) {
    if ( $.isFunction( data ) ) {
        callback = data;
        data = {};
    }
    opts = opts || {};
    
    if(opts.loader)
        opts.loader.startLoading();
    
    function makecb(cb){
        return function(){
            if($.isFunction(cb))
                cb.apply(this, arguments);
            if(opts.loader)
                opts.loader.stopLoading();
        }
    }
    
    return $.ajax({
        type: "POST",
        url: url,
        data: data,
        success: makecb(callback),
        applicationError: makecb(opts.error),
        dataType: 'json'
    });
};

$(document).ready(function(){
    $('.reload-link').reloadLink();
});

})(jQuery);


