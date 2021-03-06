
/**
 * Views relating to a file:
 *
 * We have
 *
 * Q.ProcessingFileView - view for a file in processing (being uploaded)
 * Q.FileView - view for an uploaded file
 * 
 * Q.DirectoryView
 *   - this handles the view logic for a collection of files
 *   - pass it a model: Q.Files
 *   - creates individual file views
 *
 * Q.FileUploader - the dnd uploader
 * Q.UploadModule
 *   - handles logic of uploading multiple files and adding them
 *     to it's Q.Files collection
 *   - pass it a model: Q.Files 
 *
 * Q.FilesModule
 *   - aggregates all this stuff into a single module.
 *   - pass it:
 *   directories: [{
 *      name: '', //root
 *      eid: '',
 *      path: '/',
 *      files: [
 *          {filedata...},{...}
 *      ]
 *   }, ...]
 */

;(function($){

Q.FileView = Q.View.extend({
    tagName: "div",

    className: "file",
    template: '#file-template',
    
    formatters: {
        'size': 'filesize(0)',
        'number_comments': 'number',
        'created_date': 'relativetime',
        'name': 'compressstr(28)'
    },

    init: function(container, settings) {
        this._super(container, settings);
        _.bindAll(this, 'render', 'updateVersion');
        this.model.view = this;
        this.model.bind('change:version', this.updateVersion);
    },
    
    updateVersion: function(m){
        $.log('FileView update version', m);
        this.render();
    },
    
    render: function() {
        var attr = $.extend({}, this.model.attributes);
        attr.user = attr.creator ? attr.creator.name : '';
        $.log(attr);
        
        for(var k in attr)
            if(k in this.formatters)
                attr[k] = Q.DataFormatters.get(this.formatters[k], attr[k]);
        
        html = _.template($(this.template).html(), attr);
        this.container.html(html);
        
        return this;
    }
});

Q.ProcessingFileView = Q.FileView.extend({

    className: "processing-file",
    template: '#upload-template',

    init: function(container, settings) {
        this._super(container, settings);
        _.bindAll(this, 'updateProgress');
        this.model.bind('change:progress', this.updateProgress);
    },
    updateVersion: function(m){},
    
    _updateProgress: function(prog){
        var perc = Q.DataFormatters.percent(prog, 0);
        
        var isup = prog < 100;
        this.uploading[isup ? 'show' : 'hide']();
        this.processing[isup ? 'hide' : 'show']();
        
        this.progress.css({width: perc});
        
        (function(t){
            if(t.progtime) clearTimeout(t.progtime);
            t.progtime = setTimeout(function(){
                t._updateProgress(100);
            }, 1500);
        })(this);
    },
    
    updateProgress: function(m){
        var prog = m.get('progress');
        this._updateProgress(prog);
    },
    
    render: function() {
        this._super();
        
        $.log(this.model.get('src'));
        var img = $("<img/>", {'class': 'thumb'});
        img[0].file = this.model.get('file');   
        img[0].src = this.model.get('src');
        
        this.container.find('img.thumb').replaceWith(img);
        this.progress = this.container.find('.progress');
        this.processing = this.container.find('.processing');
        this.uploading = this.container.find('.uploading');
        
        return this;
    }
});

/*
    Knows nothing about the actual uploading. Just deals with hiding/showing the target box.
*/
Q.DropTarget = Q.Module.extend('DropTarget', {
    
    init: function(c, s){
        var defs = {
            template: '#droptarget-template',
            showOn: 'elemdrag',
            targetClass: 'target',
            onTargetEnter: function(){},
            onTargetLeave: function(){}
        };
        this._super(c, $.extend({}, defs, s));
        _.bindAll(this, 'handleDrag', 'handleTargetEnter', 'handleTargetLeave', 'hideTarget');
        
        this._createDropTarget();
    },
    
    _createDropTarget: function(){
        this.target = $($(this.settings.template).html());
        var pos = this.container.css('position');
        if(!pos || pos == 'static')
            this.container.css({position: 'relative'});
        
        this.container.append(this.target);
        
        var elem = this.container;
        
        elem.bind("dragenter",this.handleDrag);
        this.target.bind("dragenter",this.handleTargetEnter);
        this.target.bind("dragleave",this.handleTargetLeave);
        this.target.bind("drop",this.handleTargetLeave);
    },
    
    handleDrag: function(event){
        $.log('handle Drag', event.target, this.target);
        if(event.type == "dragenter" && this.target)
            this.target.show();
    },
    
    hideTarget: function(){
        this.target.hide();
    },
    
    handleTargetEnter: function(e){
        $.log('handleTargetEnter', e.target);
        if(!$(e.target).hasClass(this.settings.targetClass)) return;
        
        if(this.settings.onTargetEnter.call(this, e) == false) return;
        
        this.target.addClass('over');
    },
    handleTargetLeave: function(e){
        $.log('handleTargetLeave', e.target);
        if(!$(e.target).hasClass(this.settings.targetClass)) return;
        
        if(this.settings.onTargetEnter.call(this, e) == false) return;
        
        setTimeout(this.hideTarget, 200);
    },
    
    hide: function(){ this.target.hide(); },
    show: function(){ this.target.show(); }
});

Q.DirectoryView = Q.View.extend({
    tagName: "div",

    className: "directory",
    dropTemplate: '#droptarget-template',
    rootTemplate: '#root-template',
    dirTemplate: '#dir-template',

    init: function(container, settings) {
        /***
         * Pass in {model: Q.Directory collection}
         */
        var defs = {
            showDropTargetOn: 'bodydrag' //or elemdrag
        };
        this._super(container, $.extend({}, defs, settings));
        _.bindAll(this, "render", 'addFile', 'updateVersion', 'handleTargetLeave');
        
        this.model.view = this;
        
        this.files = this.model.get('files');
        this.files.bind('add', this.addFile);
        this.files.bind('change:version', this.updateVersion);
        
    },
    
    addFile: function(m){
        this.target.hide();
        $.log('adding processig file?', m, this.filesElem);
        //we need to check the type. It may be a processing file, and it
        //may be a regular file.
        //It may be a regular file that was just uploaded so it connected to
        //a ProcessingFile model also in the model collection.
        if(m.type == 'processingFile'){
            var view = new Q.ProcessingFileView({model: m});
            this.filesElem.prepend(view.render().el);
        }
        else{
            var view = new Q.FileView({model: m});
            var el = view.render().container;
            var pm = this.files.get(m.get('uploadId'));
            if(pm){
                $.log('poo', pm);
                //replace the processing file's element with the real files elem
                pm.view.container.replaceWith(el);
                pm.view.remove();
                this.files.remove(pm);
            }
            else
                this.filesElem.append(el);
        }
        this.updateFileClasses();
    },
    
    updateVersion: function(m){
        this.target.hide();
        //This is more than likely a freshly uploaded file. We need to remove the
        //corresponding processing file and replace its elem with the updated file's
        var pm = this.files.get(m.attributes.uploadId);
        $.log('ver poo before', m, m.attributes.uploadId, m.attributes, m.get('uploadId'), this.files);
        if(pm){
            $.log('ver poo', pm, this.files);
            pm.view.container.replaceWith(m.view.container);
            pm.view.remove();
            this.files.remove(pm);
        }
        this.updateFileClasses();
    },
    
    updateFileClasses: function(){
        var elems = this.filesElem.children();
        elems.removeClass('posmod3').removeClass('posmod4');
        for(var i = 0; i < elems.length; i++){
            var el = elems.eq(i);
            if(i % 3 == 0) el.addClass('posmod3');
            if(i % 4 == 0) el.addClass('posmod4');
        }
    },
    
    
    handleTargetLeave: function(){
        if(this.files.length) return true;
        
        this.target.target.removeClass('over');
        return false;
    },
    
    render: function() {
        var html;
        
        //check whether we should show the header or not.
        if(!this.model.isRoot(this.settings.path))
            html = _.template($(this.dirTemplate).html(), this.model.attributes);
        else
            html = _.template($(this.rootTemplate).html(), this.model.attributes);
        
        this.container.html(html);
        
        if(this.settings.showDropTargetOn){
            this.target = this.container.find('.files-container').DropTarget({
                showOn: this.settings.showDropTargetOn,
                onTargetLeave: this.handleTargetLeave
            });
            
            this.filesElem = this.container.find('.files');
            
            if(this.files.length == 0) this.target.show();
            else this.target.hide();
        }
        
        return this;
    }

});

Q.FilesModule = Q.Module.extend('FilesModule', {
    
    init: function(container, settings){
        /**
         */
        _.bindAll(this, 'addDirectory');
        
        var defs = {
            showDropTargetOn: 'bodydrag', //or elemdrag
            directories: [],
            previewImage: '',
            maxPreviewSize: 5242880 //5MB
        };
        settings = $.extend({}, this.defs, settings);
        
        this._super(container, settings);
        
        var set = this.settings;
        
        this.directories = new Q.Directories([]);
        this.directories.bind('add', this.addDirectory);
        
        for(var i = 0; i < set.directories.length; i++){
            var attr = $.extend({}, set.directories[i]);
            $.log('dir', attr);
            attr.id = attr.eid;
            this.directories.add(new Q.Directory(attr));
        }
    },
    
    addDirectory: function(m){
        if(m.isRoot(this.settings.path)){
            
            var set = $.extend({}, this.settings);
            var files = m.get('files');
            m.set({files: new Q.Files([])});
            
            var view = new Q.DirectoryView($.extend({}, set, {model: m}));
            this.container.append(view.render().el);
            
            set.path = $.pathJoin(m.attributes.path, m.attributes.name);
            set.files = m.get('files');
            $.log('Setting up upload module', '@'+this.settings.userRole+'@')
            if(this.settings.userRole && this.settings.userRole != 'read')
                view.target.target.UploadModule(set);
            
            for(var j = 0; j < files.length; j++){
                files[j].id = files[j].eid;
                m.get('files').add(new Q.File(files[j]));
            }
            
        }
    }
});

})(jQuery);