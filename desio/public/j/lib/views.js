;/*******************************************************************************
 *
 ******************************************************************************/

(function($){

Q.PopupView = Q.View.extend({
    
    //this is where the popup will go. Make sure it has a position that isnt static
    referenceContainer: '#page-inner',
    id: 'popup-view',
    
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
        this.referenceContainer = $.getjQueryObject(this.referenceContainer);
        
        if(this.settings.referenceElem)
            this.settings.referenceElem = $.getjQueryObject(this.settings.referenceElem);
        
        this.hidden = false;
    },
    
    viewport: function() {
        
        var elem = $(window);
		return {
			x: elem.scrollLeft(),
			y: elem.scrollTop(),
			w: elem.width(),
			h: elem.height()
		};
	},
    
    render: function(){
        this._super();
        
        
        this.referenceContainer.append(this.el);
        this.el.id = this.id + '-' + Q.PopupView.id++;
        this.container.addClass('popup-view');
        
        this.container.mousedown(function(e){
            e.stopPropagation();
        });
    },
    
    show: function(referenceElem){
        //referenceElem is another jquery object that this will be next to.
        //will use the one in settings if not defined
        referenceElem = referenceElem ? $.getjQueryObject(referenceElem) : this.settings.referenceElem;
        
        refPos = referenceElem.offset();
        containerPos = this.referenceContainer.offset();
        
        refPos.w = referenceElem.width();
        refPos.h = referenceElem.height();
        
        var viewport = this.viewport();
        
        this.container.show();
        
        var size = {
            w: this.container.width(),
            h: this.container.height()
        };
        
        var pos = {
            left: refPos.left + refPos.w + 10,
            top: refPos.top
        };
        
        if(viewport.x+viewport.w < pos.left+size.w)
            pos.left = refPos.left - size.w - 10;
        
        if(viewport.y+viewport.h < pos.top+size.h)
            pos.top = viewport.y+viewport.h - size.h - 10;
        
        pos.top = pos.top - containerPos.top;
        pos.left = pos.left - containerPos.left;
        this.container.css(pos);
        
        this.hidden = false;
    },
    
    hide: function(){
        if(!this.hidden){
            this.container.hide();
            this.hidden = true;
        }
    }
});
Q.PopupView.id = 0;

})(jQuery);


