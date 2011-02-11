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

var _Collection = Class.extend(Backbone.Collection.prototype);
Q.Collection = _Collection.extend({
    _ctor: function(models, settings){
        
        //call backbone's constructor
        Backbone.Collection.call(this, models, settings);
        
        this.settings = settings;
        
        // call the quaid constructor
        if ( $.isFunction(this.init) )
            this.init.call(this, models, settings);
    }
});

var _Model = Class.extend(Backbone.Model.prototype);
Q.Model = _Model.extend({
    _ctor: function(attributes){
        
        //call backbone's constructor
        Backbone.Model.call(this, attributes);
        
        // call the quaid constructor
        if ( $.isFunction(this.init) )
            this.init.call(this, attributes);
    }
});

//end stuff to put in quaid

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


