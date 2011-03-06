
/**
 * JS for viewing a single file.
 */

;(function($){

Q.TabView = Q.View.extend({
    
    template: '#tab-template',
    className: 'tab',
    
    init: function(){
        //gets selectedVersion model in the settings.
        _.bindAll(this, 'clickTab', 'changeVersion');
        this._super.apply(this, arguments);
        this.container.click(this.clickTab);
        
        this.settings.selectedVersion.bind('change:version', this.changeVersion)
    },
    
    changeVersion: function(m){
        if(m.get('version') == this.model.get('version'))
            this.container.addClass('selected');
        else
            this.container.removeClass('selected');
    },
    
    clickTab: function(){
        this.settings.selectedVersion.set(_.clone(this.model.attributes));
    }
});

Q.ImageViewer = Q.View.extend('ImageViewer', {
    template: '#image-template',
    className: 'image',
    
    n: {
        title: '.top-bar .text',
        images: '.image-container'
    },
    
    init: function(){
        //gets selectedVersion model in the settings.
        //gets selectedComment in settings
        //gets comments
        //gets pinsMode
        _.bindAll(this, 'changeVersion', 'docClick');
        this._super.apply(this, arguments);
        
        //this will store all the image views. Lazy loaded.
        this.views = {};
        this.currentVersion = null;
        
        this.settings.selectedVersion.bind('change:version', this.changeVersion)
        
        $(document).mousedown(this.docClick);
    },
    
    docClick: function(e){
        $.log('document click', this.currentVersion, this.views);
        
        var targ = $(e.target);
        var docclick = !(targ.is('.not-doc') || targ.parents('.not-doc').length);
        
        if(docclick && this.currentVersion && this.currentVersion in this.views){
            var v = this.views[this.currentVersion];
            for(var i = 0; i < v.length; i++)
                v[i].release(e);
        }
    },
    
    changeVersion: function(m){
        var ver = m.get('version');
        if(ver == this.currentVersion) return;
        
        var model = null;
        for(var i = 0; i < this.model.models.length; i++)
            if(this.model.models[i].get('version') == ver)
                model = this.model.models[i];
        
        if(!model) return;
        
        this.n.images.children().remove();
        
        var images = [];
        if(ver in this.views)
            images = this.views[ver];
        else{
            var extr = model.get('extracts');
            
            for(var i = 0; i < extr.length; i++)
                if(extr[i].extract_type != "thumbnail")
                    images.push(new Q.ImageView(
                        $.extend({}, this.settings, { model: new Backbone.Model(extr[i]) })
                    ));
            
            //if we didnt find any proper extracts, use the real file url
            if(images.length == 0){
                images.push(new Q.ImageView(
                    $.extend({}, this.settings, {
                        model: new Backbone.Model(model.attributes)
                    })
                ));
            }
            
            this.views[ver] = images;
        }
        
        for(var i = 0; i < images.length; i++){
            this.n.images.append(images[i].render().container);
        }
        
        this.currentVersion = ver;
    }
});

Q.PinView = Q.View.extend({
    template: '#pin-template',
    pinsize:{ x: 37, y: 37 },
    className: 'pin',
    
    events: {
        'click': 'setComment'
    },
    
    init: function(){
        //gets:
        // model: is a comment
        // selectedComment
        
        _.bindAll(this, 'updateComment', 'selectComment');
        this._super.apply(this, arguments);
        
        this.model.bind('change:body', this.updateComment);
        //this.settings.selectedComment.bind('change:comment', this.selectComment);
    },
    
    selectComment: function(m){
        m = m.get();
        if(m && m.id == this.model.id)
            this.container.hide();
        else
            this.container.show();
    },
    
    setComment: function(){
        this.settings.selectedComment.set(this.model);
    },
    
    setScale: function(xscale, yscale){
        this.settings.xscale = xscale;
        this.settings.yscale = yscale;
        position();
    },
    
    position: function(){
        var m = this.model;
        var position = m.get('position');
        
        //find the center of the selection
        var pos = {
            left: (position[0] + position[2]/2 - this.pinsize.x/2)/this.settings.xscale,
            top: (position[1] + position[3]/2 - this.pinsize.y/2)/this.settings.yscale
        };
        
        this.pin.css(pos);
    },
    
    render: function(){
        var m = this.model;
        
        var pin = this.pin = this.container.append($(_.template(this.template, {
            title: m.get('creator').name + ': ' + m.get('body')
        })));
        
        this.position();
        
        if(m.get('extract'))
            pin.attr('extract', m.get('extract').id);
        
        return this;
    }
});

Q.ImageView = Q.View.extend({
    template: '#image-template',
    pinTemplate: '#pin-template',
    className: 'image',
    
    init: function(){
        //model is a generic backbone model with a file extract in it
        _.bindAll(this, 'onChange', 'onSelect', 'changeCollapse', 'onRelease', 'setCropper', 'onStart', 'changeComment', 'onAddComment', 'changePinsMode');
        this._super.apply(this, arguments);
        
        this.pinTemplate = $(this.pinTemplate).html();
        
        this.settings.selectedComment.bind('change:comment', this.changeComment);
        this.settings.comments.bind('add', this.onAddComment);
        this.settings.comments.bind('newcomment', this.onAddComment);
        this.settings.pinsMode.bind('change:pins', this.changePinsMode);
        this.settings.collapsable.bind('change:collapse', this.changeCollapse);
    },
    
    onChange: function(c){
        if(this.newCommentView)
            this.newCommentView.hide();
    },
    changeComment: function(m){
        m = m.get();
        
        if(m && this.container.is(':visible') && (!m.get('extract') || this.model.get('order_index') == m.get('extract').order_index) && m.hasPosition()){
            this.hidePopups();
            var pos = m.get('position');
            this.pins.hide();
            this.cropper.setSelect([pos[0], pos[1], pos[2]+pos[0], pos[3]+pos[1]]);
            
            this.popupCommentView.show(this.cropper.trackerElem, m);
        }
    },
    
    changeCollapse: function(isit){
        var width = isit ? this.settings.fullBoxWidth : this.settings.boxWidth;
        $.log('set width: ', width);
        this.settings.collapseInitially = isit;
        this.render();
    },
    
    changePinsMode: function(m){
        m = m.get();
        if(m == 'show'){
            this.pins.show();
            this.cropper.release();
        }
        else
            this.pins.hide();
    },
    
    hidePopups: function(){
        if(this.newCommentView)
            this.newCommentView.hide();
        if(this.popupCommentView)
            this.popupCommentView.hide();
    },
    
    onAddComment: function(m){
        if(m && m.hasPosition() && (!m.get('extract') || m.get('extract').order_index == this.model.get('order_index')) && this.cropper){
            $.log('placing pin?', m);
            var pin = new Q.PinView({
                model: m,
                selectedComment: this.settings.selectedComment,
                xscale: this.cropper.xscale,
                yscale: this.cropper.yscale
            });
            
            pin.template = this.pinTemplate;
            
            this.pins.append(pin.render().el);
        }
    },
    
    onSelect: function(c){
        $.log('onSelect', c, this.settings.boxWidth, 'elem', this.cropper, this.cropper.trackerElem);
        if(c.w && c.h && this.newCommentView){
            this.newCommentView.show(this.cropper.trackerElem);
        }
    },
    
    onRelease: function(){
        this.hidePopups();
        this.settings.selectedComment.set(null);
        if(this.settings.pinsMode.get() == 'show')
            this.pins.show();
    },
    
    onStart: function(){
        this.settings.selectedComment.set(null);
        this.pins.hide();
    },
    
    setCropper: function(cropperApi){
        this.cropper = cropperApi;
        this.newCommentView.setCropper(cropperApi);
        
        this.$('.jcrop-holder').append(this.pins);
        for(var i = 0; i < this.settings.comments.length; i++){
            this.onAddComment(this.settings.comments.models[i]);
        }
    },
    
    release: function(){
        if(this.cropper)
            this.cropper.release();
    },
    
    render: function(){
        if(this.cropper)
            this.cropper.destroy();
        
        this._super();
        
        var width = this.settings.collapseInitially ? this.settings.fullBoxWidth : this.settings.boxWidth;
        $.log('rendering with width', width, this.settings.collapseInitially);
        var img = this.$('img').Jcrop({
            onChange: this.onChange,
            onSelect: this.onSelect,
            onRelease: this.onRelease,
            onLoad: this.setCropper,
            onStart: this.onStart,
            //cornerHandles: false,
            //sideHandles: false,
            allowMove: false,
            keySupport: false,
            allowResize: false,
            boxWidth: width
        });
        
        if(!this.newCommentView){
            this.newCommentView = new Q.ImageNewCommentView({
                model: this.model.clone(),
                comments: this.settings.comments
            });
            this.newCommentView.render();
            this.newCommentView.hide();
        }
        
        if(!this.popupCommentView){
            this.popupCommentView = new Q.PopupCommentView({
                model: this.model,
                replyForm: window.replyForm
            });
            
            this.popupCommentView.render();
            this.popupCommentView.hide();
        }
        
        if(!this.pinObjs)
            this.pinObjs = [];
        
        this.pins = this.$('.pins')[this.settings.pinsMode.get()]();
        
        return this;
    }
});

Q.CommentForm = Q.Form.extend('CommentForm', {
    init: function(con, set){
        var defs = {
            validationOptions:{
                rules: {body: 'required'},
                messages: {body: 'Message please'}
            }
        };
        this._super(con, $.extend(true, {}, defs, set));
        
        _.bindAll(this, 'parseKey');
        
        var b = this.getElement('body');
        b.keypress(this.parseKey);
    },
    
    parseKey: function(e){
        var shift_down = e.shiftKey;
        switch(e.keyCode){
            case 13:
                this.form.submit();
                return false;
        }
        return true;
    }
});

Q.ImageNewCommentView = Q.PopupView.extend({
    template: '#image-comment-template',
    className: 'new-image-comment',
    
    init: function(container, settings){
        //model is a generic backbone model with a file extract in it
        var defs = {
            model: new Q.Model({}),
            comments: null //need the list of comments to add to....
        };
        this._super(container, $.extend({}, defs, settings));
        this.model = this.model || this.settings.model;
        
        _.bindAll(this, 'onSubmit');
    },
    
    setupForm: function(){
        this.form = this.$('form').CommentForm({
            validationOptions:{
                submitHandler: this.onSubmit
            }
        });
    },
    
    onSubmit: function(){
        var pos = this.cropper.tellSelect();
        pos = [pos.x, pos.y, pos.w, pos.h];
        $.log('submit', this.form.val('body'), this.model.id, pos);
        
        this.settings.comments.addComment(this.form.val('body'), this.model.id, pos);
        
        //this.cropper.release();
        
        return false;
    },
    
    setCropper: function(cropperApi){this.cropper = cropperApi;},
    show: function(){
        this._super.apply(this, arguments);
        
        this.form.reset();
        this.form.focusFirst();
    },
    
    render: function(){
        this._super();
        
        this.setupForm();
        
        return this;
    }
    
});

Q.CommentView = Q.View.extend({
    tagName: 'div',
    className: 'comment',
    template: '#comment-template',
    
    events: {
        'click .reply-link': 'onClickReply'
    },
    
    init: function(container, settings){
        /**
         * Will get in settings:
         * model: Q.Comment()
         * selectedComment: 
         */
        this._super(container, settings);
        _.bindAll(this, 'onAddReply', 'onSelectComment');
        
        if(this.model.get('position')){
            this.container.addClass('position');
            this.container.mousedown(function(e){
                e.stopPropagation();
            });
        }
        
        var replies = this.model.get('replies');
        replies.bind('add', this.onAddReply);
        replies.bind('newcomment', this.onAddReply);
        
        if(this.settings.selectedComment)
            this.settings.selectedComment.bind('change:comment', this.onSelectComment)
    },
    
    onSelectComment: function(m){
        m = m.get();
        if(m && m.get('eid') == this.model.get('eid'))
            this.container.addClass('selected');
        else
            this.container.removeClass('selected');
    },
    
    onClickReply: function(){
        var elem = this.$('#'+this.settings.replyForm.container[0].id);
        this.settings.replyForm.model = this.model.get('replies');
        if(elem.length && this.settings.replyForm.container.is(':visible'))
            this.settings.replyForm.hide();
        else{
            this.settings.replyForm.container.insertAfter(this.$('.reply-link'));
            this.settings.replyForm.show();
        }
        return false;
    },
    
    onAddReply: function(m){
        if(this.replies && !m.isNew()){
            this.replies.show();
            $.log('Adding reply in onAddReply', m);
            var com = new Q.CommentView({
                model: m,
                selectedComment: this.settings.selectedComment
            });
            this.replies.append(com.render().el);
        }
        else
            $.log('NOT Adding reply as no replies yet...', m);
    },
    
    render: function(){
        this.container[0].id = this.model.get('eid');
        var d = {
            time: $.relativeDateStr($.parseDate(this.model.get('created_date'))),
            creator: this.model.get('creator').name,
            body: this.model.get('body'),
            version: this.model.get('change_version')
        };
        this.renderTemplate(d);
        
        this.replies = this.$('.replies').hide();
        var repl = this.model.get('replies');
        
        for(var i = 0; i < repl.length; i++){
            $.log('Adding reply in render', repl.models[i]);
            this.onAddReply(repl.models[i]);
        }
        
        if(!this.settings.replyForm)
            this.$('.reply-link').remove();
        return this;
    }
});

Q.PopupCommentView = Q.PopupView.extend({
    template: '#popup-comment-template',
    className: 'popup-comment-view',
    tagName: 'div',
    
    init: function(container, settings){
        //model is a comment
        this._super(container, settings);
        
        //_.bindAll(this, 'onSubmit');
    },
    
    show: function(referenceElem, comment){
        var com = new Q.CommentView({
            model: comment,
            replyForm: this.settings.replyForm
        });
        this.container.find('.comment-container').html(com.render().el);
        
        this._super(referenceElem);
    }
});

Q.CommentsView = Q.View.extend('CommentsView', {
    
    events:{
        'click .comment': 'onClickComment'
    },
    
    init: function(container, settings){
        /**
         * Will get in settings:
         * model: Q.Comments()
         * selectedComment: 
         */
        
        this._super(container, settings);
        _.bindAll(this, 'onAddComment', 'onNewComment', 'onRemoveComment');
        
        var loader = this.loader = this.container.Loader();
        
        this.model.bind('newcomment', this.onNewComment);
        this.model.bind('add', this.onAddComment);
        this.model.bind('remove', this.onRemoveComment);
        
        this.model.bind('request:start', function(){
            $.log('start loading');
            loader.startLoading();
        });
        this.model.bind('request:end', function(){
            $.log('stop loading');
            loader.stopLoading()
        });
    },
    
    render: function(){return this;},
    
    onClickComment: function(e){
        var targ = $(e.target);
        if(targ.is('a')) return true;
        
        if(!targ.is('#comments>.comment')) targ = targ.parents('#comments>.comment');
        var id = targ[0].id;
        
        var m = this.model.get(id);
        
        if(m && m.hasPosition())
            this.settings.selectedComment.set(m);
    },
    onNewComment: function(m){
        this.onAddComment(m);
        if(m && m.hasPosition())
            this.settings.selectedComment.set(m);
    },
    
    onAddComment: function(m){
        if(!m.isNew()){
            var view = new Q.CommentView({
                model: m,
                selectedComment: this.settings.selectedComment,
                replyForm: this.settings.replyForm
            });
            this.container.append(view.render().el);
        }
    },
    
    onRemoveComment: function(m){
    }
});

Q.CommentFormView = Q.View.extend('CommentFormView', {
    n: {
        commentForm: 'form'
    },
    events:{
        'click .cancel': 'addCommentCancel'
    },
    
    init: function(container, settings){
        //model is the comment collection we are adding to.
        
        this._super(container, settings);
        _.bindAll(this, 'onSubmitCommentForm');
        
        this.container.hide();
        this.form = this.n.commentForm.CommentForm({
            validationOptions:{
                submitHandler: this.onSubmitCommentForm
            }
        });
    },
    
    show: function(){
        this._super();
        this.form.focusFirst();
    },
    
    hide: function(){
        this.container.hide();
        this.form.reset();
    },
    
    addCommentCancel: function(){
        this.hide();
        return false;
    },
    
    onSubmitCommentForm: function(){
        var self = this;
        
        $.log(self.model, self.form.val('body'));
        self.model.addComment(self.form.val('body'));
        
        this.addCommentCancel();
        return false;
    }
});

Q.PinButtonView = Q.View.extend('PinButtonView', {
    init: function(c, set){
        this._super(c, set);
        _.bindAll(this, 'setButton', 'pinToggle');
        this.model.bind('change:pins', this.setButton);
        c.click(this.pinToggle);
        
        this.pins = $('.pins');
    },
    
    setButton: function(mode){
        var targ = this.container;
        if(mode.get() == 'hide'){
            targ.removeClass('selected');
            targ.attr('title', 'Click to show annotation pins');
        }
        else{
            targ.addClass('selected');
            targ.attr('title', 'Click to hide annotation pins');
        }
    },
    
    pinToggle: function(e){
        if(this.model.get() == 'show')
            this.model.set('hide');
        else
            this.model.set('show');
        return false;
    }
});

Q.ViewFilePage = Q.Page.extend({
    n: {
        tabs: '#version-tabs',
        pageImageViewer: '#inpage-image-viewer',
        comments: '#comments',
        addComment: '#add-comment',
        replyComment: '#reply-comment',
        pinToggle: '#pin-toggle',
        sidepanel: '#sidepanel'
    },
    events:{
        'click #add-comment-link': 'addCommentClick'
    },
    run: function(){
        
        /**
         * If you want to upload on this page, use the Q.FileUploader
         * and use the forcedName param
         */
        var self = this;
        this._super.apply(this, arguments);
        _.bindAll(this, 'viewVersion', 'addVersion');
        
        var sidepanel = this.n.sidepanel.Sidepanel({
            collapsePreference: this.settings.collapsePreference,
            collapseInitially: this.settings.collapseInitially
        });
        
        this.versions = new Q.FileVersions([]);
        this.selectedVersion = new Backbone.Model({});
        this.selectedComment = new Q.SingleSelectionModel('comment');
        
        //pin junk
        this.pinsMode = new Q.SingleSelectionModel('pins');
        this.n.pinToggle.PinButtonView({model: this.pinsMode})
        this.pinsMode.set('show');
        
        this.comments = new Q.Comments([]);
        
        this.commentForm = this.n.addComment.CommentFormView({
            model: this.comments
        });
        this.replyForm = window.replyForm = this.n.replyComment.CommentFormView({
            model: null
        });
        
        this.commentsView = this.n.comments.CommentsView({
            model: this.comments,
            selectedComment: this.selectedComment,
            replyForm: this.replyForm
        });
        
        //do setup and binding here
        this.selectedVersion.bind('change:version', this.viewVersion);
        this.versions.bind('add', this.addVersion);
        
        this.pageImageViewer = this.n.pageImageViewer.ImageViewer({
            model: this.versions,
            selectedVersion: this.selectedVersion,
            selectedComment: this.selectedComment,
            pinsMode: this.pinsMode,
            comments: this.comments,
            boxWidth: this.settings.boxWidth,
            fullBoxWidth: this.settings.fullBoxWidth,
            collapseInitially: this.settings.collapseInitially,
            collapsable: sidepanel
        });
        
        //add the versions to the model
        for(var i = 0; i < this.settings.versions.length; i++){
            this.versions.add(this.settings.versions[i]);
        }
        this.selectedVersion.set(this.settings.versions[0]);
        
        this.comments.setCurrentVersion(this.selectedVersion);
        this.comments.add(this.settings.comments, {
            save: false,
            urls: this.settings.commentUrls
        });
        
        $.log(this.comments);
    },
    
    addCommentClick: function(){
        if(this.commentForm.container.is(':visible'))
            this.commentForm.addCommentCancel();
        else{
            this.commentForm.show();
            this.commentForm.form.focusFirst();
        }
        return false;
    },
    
    addVersion: function(m){
        $.log('add version', m);
        this.n.tabs.append(new Q.TabView({
            model: m,
            selectedVersion: this.selectedVersion
        }).render().container);
    },
    
    viewVersion: function(m){
        //m.version is a FileVersion model
        var version = m.get('version');
        $.log('View version', version);
    }
});

})(jQuery);