
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
                        boxWidth: this.settings.boxWidth
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
        _.bindAll(this, 'onChange', 'onSelect', 'onRelease', 'setCropper');
        this._super.apply(this, arguments);
        
        $.log('ImageView settings', this.settings, this.model);
    },
    
    onChange: function(c){
        if(this.newCommentView)
            this.newCommentView.hide();
        
        //$.log('onChange', c.x, c.y, c.x2, c.y2, c.w, c.h, c);
    },
    
    onSelect: function(c){
        $.log('onSelect', c, this.settings.boxWidth, 'elem', this.cropper, this.cropper.trackerElem);
        if(c.w && c.h && this.newCommentView){
            this.newCommentView.show(this.cropper.trackerElem);
        }
    },
    
    onRelease: function(){
        if(this.newCommentView)
            this.newCommentView.hide();
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
        
        _.bindAll(this, 'onSubmit', 'parseKey');
    },
    
    setupForm: function(){
        this.form = this.$('form').Form({
            validationOptions:{
                submitHandler: this.onSubmit,
                rules: {body: 'required'},
                messages: {body: 'Message please'}
            }
        });
        
        var b = this.form.getElement('body');
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

Q.ViewFilePage = Q.Page.extend({
    n: {
        tabs: '#tabs',
        pageImageViewer: '#inpage-image-viewer'
    },
    events:{
    },
    run: function(){
        
        /**
         * If you want to upload on this page, use the Q.FileUploader
         * and use the forcedName param
         */
        var self = this;
        this._super.apply(this, arguments);
        _.bindAll(this, 'viewVersion', 'addVersion');
        
        this.versions = new Q.FileVersions([]);
        this.selectedVersion = new Backbone.Model({});
        
        this.comments = new Q.Comments([]);
        
        //do setup and binding here
        this.selectedVersion.bind('change:version', this.viewVersion);
        this.versions.bind('add', this.addVersion);
        
        this.pageImageViewer = this.n.pageImageViewer.ImageViewer({
            model: this.versions,
            selectedVersion: this.selectedVersion,
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