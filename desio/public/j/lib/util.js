;/*******************************************************************************
 *
 ******************************************************************************/

(function($){

$.fn.scrollshow = function(options){

    try{
        var defs = {
            speed: 200,
            extratop: 0,
            onFinishedScrolling: function(){}
        };
        options = $.extend({}, defs, options);
        
        var place = $(this);
        var winheight = $(window).height();
        var objheight = place.height();
        
        //this should center the elem on the screen
        var top = place.offset().top - options.extratop;
        
        if(objheight < winheight) {
            var diff = winheight/2 - objheight/2;
            top -= diff;
        }
        
        $.debug('scrolling to ', top);
        
        $('html, body').animate({
            scrollTop: top
        }, options.speed, options.onFinishedScrolling);
        
    } catch(e) {
        
    }
    
    return this;
};

})(jQuery);


