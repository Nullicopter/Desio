;/*******************************************************************************
 *
 ******************************************************************************/

(function($){

/**
 * At some point we can make this thing extend the jqui dialog like at AdRoll.
 */
Q.Dialog = Q.Module.extend('Dialog', {
    init: function(container, settings){
        var defs = {
            autoOpen: false,
            draggable: false,
            modal: true,
            resizable: false
        };
        this._super(container, $.extend({}, defs, settings));
        
        this.container.dialog(this.settings);
        
        var p = this.container.parents('.ui-dialog');
        var ch = this.container.parents('.ui-dialog').children();
        
        var node = $('<div/>', {
            'class':'ui-dialog-inner-wrap'
        });
        p.append(node);
        node.append(ch);
    },
    open: function(){
        this.container.dialog('open');
    },
    close: function(){
        this.container.dialog('close');
    }
});


})(jQuery);


