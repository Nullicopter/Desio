
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
        
        if(this.currentVersion && this.currentVersion in this.views){
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
            
            //if we didnt find any proper extracts, use the real file url
            for(var i = 0; i < extr.length; i++)
                if(extr[i].extract_type != "thumbnail")
                    images.push(new Q.ImageView({
                        model: new Backbone.Model(extr[i]),
                        comments: this.settings.comments,
                        boxWidth: this.settings.boxWidth,
                        selectedComment: this.settings.selectedComment
                    }).render());
            
            
            if(images.length == 0){
                images.push(new Q.ImageView({
                    model: new Backbone.Model(model.attributes)
                }).render());
            }
            
            this.views[ver] = images;
        }
        
        for(var i = 0; i < images.length; i++){
            $.log(images[i].model);
            this.n.images.append(images[i].container);
        }
        
        this.currentVersion = ver;
    }
});

Q.ImageView = Q.View.extend({
    template: '#image-template',
    className: 'image',
    
    init: function(){
        //model is a generic backbone model with a file extract in it
        _.bindAll(this, 'onChange', 'onSelect', 'onRelease', 'setCropper', 'onStart', 'changeComment');
        this._super.apply(this, arguments);
        
        $.log('ImageView settings', this.settings, this.model);
        
        this.settings.selectedComment.bind('change:comment', this.changeComment);
    },
    
    onChange: function(c){
        if(this.newCommentView)
            this.newCommentView.hide();
        
        //$.log('onChange', c.x, c.y, c.x2, c.y2, c.w, c.h, c);
    },
    changeComment: function(m){
        m = m.get();
        
        if(m && this.model.get('id') == m.get('extract_id') && m.hasPosition()){
            this.hidePopups();
            var pos = m.get('position');
            this.cropper.animateTo([pos[0], pos[1], pos[2]+pos[0], pos[3]+pos[1]]);
        }
    },
    
    hidePopups: function(){
        if(this.newCommentView)
            this.newCommentView.hide();
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
    },
    
    onStart: function(){
        this.settings.selectedComment.set(null);
    },
    
    setCropper: function(cropperApi){
        this.cropper = cropperApi;
        this.newCommentView.setCropper(cropperApi);
    },
    
    release: function(){
        if(this.cropper)
            this.cropper.release();
    },
    
    render: function(){
        $.log('render', this.settings.boxWidth);
        if(this.cropper)
            this.cropper.destory();
        
        this._super();
        
        this.newCommentView = new Q.ImageNewCommentView({
            model: this.model.clone(),
            comments: this.settings.comments
        });
        
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
            boxWidth: this.settings.boxWidth
        });
        
        this.newCommentView.render();
        this.newCommentView.hide();
        
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
        
        this.cropper.release();
        
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
    
    init: function(container, settings){
        /**
         * Will get in settings:
         * model: Q.Comment()
         * selectedComment: 
         */
        $.log(settings);
        this._super(container, settings);
        _.bindAll(this, 'onAddReply', 'onSelectComment');
        
        if(this.model.get('position')){
            this.container.addClass('position');
            this.container.mousedown(function(e){
                e.stopPropagation();
            });
        }
        
        this.model.bind('add', this.onAddReply);
        this.settings.selectedComment.bind('change:comment', this.onSelectComment)
    },
    
    onSelectComment: function(m){
        m = m.get();
        if(m && m.get('eid') == this.model.get('eid'))
            this.container.addClass('selected');
        else
            this.container.removeClass('selected');
    },
    
    onAddReply: function(m){
        if(this.replies){
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
            body: this.model.get('body')
        };
        this.renderTemplate(d);
        
        this.replies = this.$('.replies').hide();
        var repl = this.model.get('replies');
        
        for(var i = 0; i < repl.length; i++){
            $.log('Adding reply in render', repl.models[i]);
            this.onAddReply(repl.models[i]);
        }
        
        return this;
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
        if(!targ.is('.comment')) targ = targ.parents('.comment');
        var id = targ[0].id;
        
        var m = this.model.get(id);
        
        if(m && m.hasPosition())
            this.settings.selectedComment.set(m);
    },
    onNewComment: function(m){
        this.onAddComment(m);
        this.settings.selectedComment.set(m);
    },
    
    onAddComment: function(m){
        if(!m.isNew()){
            var view = new Q.CommentView({
                model: m,
                selectedComment: this.settings.selectedComment
            });
            this.container.append(view.render().el);
        }
    },
    
    onRemoveComment: function(m){
    }
});

Q.ViewFilePage = Q.Page.extend({
    n: {
        tabs: '#tabs',
        pageImageViewer: '#inpage-image-viewer',
        comments: '#comments',
        commentForm: '#add-comment form',
        addComment: '#add-comment'
    },
    events:{
        'click #add-comment-link': 'addCommentClick',
        'click #add-comment .cancel': 'addCommentCancel'
    },
    run: function(){
        
        /**
         * If you want to upload on this page, use the Q.FileUploader
         * and use the forcedName param
         */
        var self = this;
        this._super.apply(this, arguments);
        _.bindAll(this, 'viewVersion', 'addVersion', 'onSubmitCommentForm');
        
        this.n.addComment.hide();
        this.commentForm = this.n.commentForm.CommentForm({
            validationOptions:{
                submitHandler: this.onSubmitCommentForm
            }
        });
        
        this.versions = new Q.FileVersions([]);
        this.selectedVersion = new Backbone.Model({});
        this.selectedComment = new Q.SingleSelectionModel('comment');
        
        this.comments = new Q.Comments([]);
        
        this.commentsView = this.n.comments.CommentsView({
            model: this.comments,
            selectedComment: this.selectedComment
        });
        
        //do setup and binding here
        this.selectedVersion.bind('change:version', this.viewVersion);
        this.versions.bind('add', this.addVersion);
        
        this.pageImageViewer = this.n.pageImageViewer.ImageViewer({
            model: this.versions,
            selectedVersion: this.selectedVersion,
            selectedComment: this.selectedComment,
            comments: this.comments,
            boxWidth: this.settings.boxWidth
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
    
    /// these functions should prolly be in a separate view
    addCommentCancel: function(){
        this.n.addComment.hide();
        this.commentForm.reset();
        return false;
    },
    addCommentClick: function(){
        if(this.n.addComment.is(':visible'))
            this.addCommentCancel();
        else{
            this.n.addComment.show();
            this.commentForm.focusFirst();
        }
        return false;
    },
    onSubmitCommentForm: function(){
        this.comments.addComment(this.commentForm.val('body'));
        this.addCommentCancel();
        return false;
    },
    ////
    
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

Q.ViewProjectPage = Q.Page.extend({
    events:{
        'click #add-directory-link': 'addDirectory'
    },
    run: function(){
        var self = this;
        this._super.apply(this, arguments);
        
        this.filesModule = $(this.settings.module).FilesModule(this.settings);
    },
    
    addDirectory: function(e){
        var l = $(e.target);
        var n = prompt('What do you want to name this directory?');
        
        var dirs = this.filesModule.directories;
        for(var i = 0; i < dirs.length; i++)
            if(dirs.models[i].get('name') == n){
                n = null;
                Q.warn('Directory already exists!');
            }
        
        if(n){
            $.postJSON(l[0].href, {
                path: $.pathJoin(this.settings.path, n)
            }, function(data){
                data = data.results;
                $.log(data);
                dirs.add(data);
            });
        }
        return false;
    }
});

Q.ProjectCreatePage = Q.Page.extend({
    run: function(){
        var self = this;
        this._super.apply(this, arguments);
        _.bindAll(this, 'success', 'synced');
        this.form = this.$('#new-form').AsyncForm({
            validationOptions: {
                rules:{
                    name: 'required',
                    description: {required: false}
                }
            },
            submitters: '#create-project-link',
            onSuccess: function(data){self.success(data);}
        });
        this.form.focusFirst();
        
        this.projectUserModule = $('#project-user-module').ProjectUserModule(this.settings);
        this.projectUserModule.bind('synced', this.synced);
    },
    
    success: function(data){
        $.log(data);
        this.form.loader.startLoading();
        this.project = data.results;
        this.projectUserModule.sync(data.results.eid);
    },
    
    synced: function(){
        $.log('redirecting to /project/'+this.project.slug);
        
        this.form.loader.stopLoading();
        $.redirect('/project/'+this.project.slug);
    }
});

Q.ProjectUserSettingsPage = Q.Page.extend({
    run: function(){
        var self = this;
        this._super.apply(this, arguments);
        
        this.projectUserModule = $('#project-user-module').ProjectUserModule(this.settings);
    }
});

Q.ProjectGeneralSettingsPage = Q.Page.extend({
    run: function(){
        var self = this;
        this._super.apply(this, arguments);
        _.bindAll(this, 'success');
        
        this.form = this.$('#edit-form').AsyncForm({
            validationOptions: {
                rules:{
                    name: 'required',
                    description: {required: false}
                }
            },
            onSuccess: function(data){self.success(data);}
        });
        this.form.focusFirst();
    },
    
    success: function(data){
        Q.notify('Settings saved successfully.');
    }
});


})(jQuery);