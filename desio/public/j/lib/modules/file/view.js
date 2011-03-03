
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
        //'size': 'filesize'
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
    
    updateProgress: function(m){
        var perc = Q.DataFormatters.percent(m.get('progress'), 0);
        
        this.progress.css({width: perc});
        this.progressText.text(perc);
    },
    
    render: function() {
        this._super();
        
        $.log(this.model.get('src'));
        var img = document.createElement("img");
        img.file = this.model.get('file');   
        img.src = this.model.get('src');
        
        this.container.find('img').replaceWith($(img));
        this.progress = this.container.find('.progress');
        this.progressText = this.container.find('.progress-text');
        
        return this;
    }
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
        _.bindAll(this, "render", 'handleDrag', 'addFile', 'updateVersion', 'handleTargetEnter', 'handleTargetLeave', 'hideTarget');
        
        this.model.view = this;
        
        this.files = this.model.get('files');
        this.files.bind('add', this.addFile);
        this.files.bind('change:progress', this.updateProgress);
        this.files.bind('change:version', this.updateVersion);
        
    },
    
    addFile: function(m){
        this.target.hide();
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
    },
    
    handleDrag: function(event){
        var self = this;
        if(event.type == "dragenter" && this.target)
            this.target.show();
    },
    
    hideTarget: function(){
        this.target.hide();
    },
    
    handleTargetEnter: function(){
        this.target.addClass('over');
    },
    handleTargetLeave: function(){
        if(this.files.length)
            setTimeout(this.hideTarget, 200);
        else
            this.target.removeClass('over');
    },
    
    _createDropTarget: function(){
        this.target = $($(this.dropTemplate).html());
        var pos = this.container.css('position');
        if(!pos || pos == 'static')
            this.container.css({position: 'relative'});
        
        return this.target;
    },
    
    render: function() {
        $.log(this.settings);
        var html;
        
        //check whether we should show the header or not.
        if(!this.model.isRoot(this.settings.path))
            html = _.template($(this.dirTemplate).html(), this.model.attributes);
        else
            html = _.template($(this.rootTemplate).html(), this.model.attributes);
        
        this.container.html(html);
        
        if(this.settings.showDropTargetOn){
            target = this._createDropTarget();
            
            this.filesElem = this.container.find('.files');
            this.container.find('.files-container').append(target);
            
            if(this.files.length == 0) this.target.show();
            else this.target.hide();
            
            var elem = this.target;
            if(this.settings.showDropTargetOn == 'bodydrag') elem = $(document);
            
            this.container.bind("dragenter",this.handleDrag);
            this.target.bind("dragenter",this.handleTargetEnter);
            this.target.bind("dragleave",this.handleTargetLeave);
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
            $.log(attr);
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
            view.target.UploadModule(set);
            
            for(var j = 0; j < files.length; j++){
                files[j].id = files[j].eid;
                m.get('files').add(new Q.File(files[j]));
            }
            
        }
    }
});

})(jQuery);