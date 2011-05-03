;/*******************************************************************************
 *
 ******************************************************************************/

(function($){

$.extend(_, {
    extract: function(obj, attrs){
        var res = {};
        for(var i in attrs)
            if(attrs[i] in obj)
                res[attrs[i]] = obj[attrs[i]];
        return res;
    }
});
var parseDate = $.parseDate;
$.extend($, {
    pathJoin: function(){
        var delim = '/';
        var s = Array.prototype.join.call(arguments, delim);
        return s.replace(new RegExp(delim+delim, 'gi'), delim);
    },
    
    relativeTimeSpan: function(ms){
        /**
         * give it milliseconds, and it will return a string with the most top level unit:
         *
         * 1000 -> 1 second
         * 3500 -> 3 seconds
         * 70000 -> 1 minute
         * etc.
         **/
        var div = [1000, 60, 60, 24, 7, 52]
        var metrics = ['milli', 'second', 'minute', 'hour', 'day', 'week']
        
        var cur = ms;
        var metric = 'year'
        for(var i = 0; i < div.length; i++){
            
            var tmp = cur/div[i];
            if(tmp < 1){
                metric = metrics[i];
                break;
            }
            else cur = tmp;
        }
        
        return Q.DataFormatters.number(cur) + $.pluralize(cur, ' '+metric+'s', ' '+metric);
    },
    
    relativeDate: function(date, now){
        now = now || new Date();
        
        ret = {};
        ret.mstotal = date - now; //12345678
        ret.ispast = ret.mstotal < 0;
        ret.mstotal = Math.abs(ret.mstotal);
        
        ret.ms = ret.mstotal % 1000; //678 ms
        ret.sectotal = parseInt(ret.mstotal/1000); //12345
        ret.sec = ret.sectotal%60; //45 sec
        ret.mintotal = parseInt(ret.sectotal/60); //205 min
        ret.min = ret.mintotal%60; //25 min
        ret.hourstotal = parseInt(ret.mintotal/60); //3 hours
        ret.hours = ret.hourstotal%24; //3 hours
        ret.daystotal = parseInt(ret.hourstotal/24); //0 days
        
        return ret;
    },
    
    relativeDateStr: function(date, now){
        now = now || new Date();
        
        if(!date) return 'unknown';
        
        data = $.relativeDate(date, now);
        $.log(data);
        
        if(data.sectotal < 10 && data.ispast) return 'Just now';
        
        if(data.daystotal > 7) return $.formatDate(date, "b e, Y");
        
        function modret(str){
            if(data.ispast)
                return str + ' ago';
            return 'in ' + str;
        }
        
        if(data.daystotal == 1 && data.ispast)
            return 'Yesterday'
        if(data.daystotal == 1 && !data.ispast)
            return 'Tomorrow'
        
        if(data.daystotal > 0)
            return modret($.pluralize(data.daystotal, '{0} days', '{0} day'));
        
        if(data.hourstotal)
            return modret($.pluralize(data.hourstotal, '{0} hours', '{0} hour'));
        
        if(data.mintotal)
            return modret($.pluralize(data.mintotal, '{0} minutes', '{0} minute'));
        
        if(data.sectotal)
            return modret($.pluralize(data.sectotal, '{0} seconds', '{0} second'));
        
        if(data.mstotal)
            return modret($.pluralize(data.mstotal, '{0} millis', 'now!'));
        
        return $.formatDate(date, "b e, Y");
    },
    
    fileSize: function(bytes, decimals){
        decimals = (decimals || decimals == 0) ? decimals : 0;
        
        // Bytes is an integer
        var k = 1024;
        
        var labels = [' bytes', 'KB', 'MB', 'GB', 'TB', 'OMFGs', 'WTFOMFGs'];
        var i = 0;
        var cur = bytes;
        
        while(cur >= k){
            cur /= k;
            i++;
        }
        $.log(decimals);
        return Q.DataFormatters.decimal(cur, decimals, false) + '' + labels[i];
    }
});

$.fn.isinview = function(options){
    var place = $(this);
    
    var winheight = $(window).height();
    var wintop = $(window).scrollTop();
    
    var top = place.offset().top;
    var height = place.height();
    
    var inview = top <= (winheight + wintop) && (top + height) >= wintop;
    
    return inview;
};

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
        
        $.debug('scrolling to ', top, place.offset(), winheight, objheight);
        
        $('html, body').animate({
            scrollTop: top
        }, options.speed, options.onFinishedScrolling);
        
    } catch(e) {
        
    }
    
    return this;
};

})(jQuery);


