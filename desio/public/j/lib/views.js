;/*******************************************************************************
 *
 ******************************************************************************/

(function($){

Q.PopupView = Q.View.extend({
    
    init: function(container, settings){
        /**
         * Expecting some things in settings:
         *
         * model: some data;
         * referenceElem: this can be an element you want to show the popup next to; leave as null
         *
         * Also expecting this will be subclassed. So create a this.
         *
         * template: jquery object or something
         */
        var defs = {
            referenceElem: null
        };
        this._super(container, $.extend({}, defs, settings));
        
        this.template = $.getjQueryObject(this.template);
        
        if(this.settings.referenceElem)
            this.settings.referenceElem = $.getjQueryObject(this.settings.referenceElem);
        
        this.hidden = false;
    },
    viewport: function(elem) {
        
		return {
			x: elem.scrollLeft(),
			y: elem.scrollTop(),
			cx: elem.width(),
			cy: elem.height()
		};
	},
    
    show: function(referenceElem){
        //referenceElem is another jquery object that this will be next to.
        //will use the one in settings if not defined
        referenceElem = referenceElem ? $.getjQueryObject(referenceElem) : this.settings.referenceElem;
        
        refPos = referenceElem.position();
        
        $.log('thing position', refPos, referenceElem);
        
        this.container.insertAfter(referenceElem);
        this.container.show();
        
        this.container.css({
            left: refPos.left + referenceElem.width() + 10,
            top: refPos.top
        });
        
        this.hidden = false;
    },
    
    hide: function(){
        if(!this.hidden){
            this.container.hide();
            this.hidden = true;
        }
    }
});

})(jQuery);


