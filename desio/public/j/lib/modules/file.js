
;(function($){

Q.File = Q.Model.extend({
    type: 'file'
});

Q.FileVersion = Q.File.extend({
    type: 'version'
});

Q.ProcessingFile = Q.File.extend({
    type: 'processingFile'
});

Q.Files = Q.Collection.extend({
    model: Q.File
});

Q.FileVersions = Q.Files.extend({
    model: Q.FileVersion
});

Q.Directory = Q.Model.extend({});
Q.Directories = Q.Collection.extend({});

/***
 *
 * Comments. How do they work?
 *
 * Initial load of page: 
 * - Place all comments in Q.Comments with {save: false}
 * - Each root level comment will have a Q.Comment created. 
 * - Each comment can have replies, so the Q.Comment will place its replies in
 *   a Q.Comments object, etc.
 * - View binds to comments collection add event.
 *   - Adds a root level comment on add,
 *   - binds to replies add event
 *   - then cycles through replies and adds them too.
 *
 * Add a reply to a comment
 * - have the reply form pull the parent comment id and put it in a hidden field in the form
 * - on submit, call comments.get(id), get parent comment
 * - call comment.get('replies').add({..new reply..})
 * - parent comment is bound to comment.replies.add event. creates a new reply view when one is
 *   added
 * 
 * Adding a comment
 * - call comments.add({..new reply..}, {save: true}); //the save: true is default
 * - the Q.Comments overrides _add, it will call model.save()
 * - same as initial page load...
 *
 * Removing a comment
 * - find the comment and call destroy() on it
 * - each comment view is bound to the comment model's destroy event. on destroy, remove the elem.
 *
 * Fetching new comments for a version
 * - Something binds to a version change model. When the version changes,
 *   the binding obj gets the change eid from the model and calls
 *   Q.Comments.fetchForVersion(eid)
 **/
Q.Comment = Q.Model.extend({
    urls: {
        'create': '/api/v1/file/add_comment',
        'delete': '/api/v1/file/remove_comment'
    },
    
    init: function(){
        
        var com = new Q.Comments([]);
        com.parent = this;
        var replies = this.get('replies');
        this.set({replies: com}, {silent: true});
        
        if(replies)
            com.add(replies, {save:false});
    },
    
    toJSON: function(method){
        if(method == 'delete'){
            return {
                comment: this.get('eid')
            }
        }
        return this._super(method);
    },
    
    parse: function(data){
        $.log('Parsing comment success', data.results);
        data.results.id = data.results.eid;
        return data.results;
    }
});

Q.Comments = Q.Collection.extend({
    urls: {
        'read': '/api/v1/file/get_comments'
    },
    
    model: Q.Comment,
    
    init: function(models, settings){
        this._super.apply(this, arguments);
        _.bindAll(this, 'fetchForVersion');
    },
    
    setCurrentVersion: function(currentVersion){
        //this is a backbone model
        if(currentVersion){
            this.version = currentVersion;
            this.version.bind('change:change_eid', this.fetchForVersion);
        }
    },
    
    _add: function(m, options){
        options = options || {};
        //$.log('Adding comment', model.isNew() ? 'NEW' : 'NOT new', m, options);
        var model = this._super.call(this, m, options);
        
        $.log('Adding comment', model.isNew() ? 'NEW' : 'NOT new', m, options);
        
        if(model.isNew()){
            //is this a reply?
            if(this.parent)
                model.set({in_reply_to: this.parent.get('eid')});
            
            //is this a new comment on the file itself?
            if(!model.get('extract') && !model.get('change') && this.version)
                model.set({change: this.version.get('change_eid')});
            
            if(options.save != false && options.silent != true)
                model.save();
        }
    },
    
    toJSON: function(){
        return {
            change: this.version.get('change_eid')
        };
    },
    
    parse: function(data){
        if(data && data.results && data.results.comments)
            return data.results.comments;
        $.warn('Bad data on comment fetch?', data);
        return [];
    },
    
    fetchForVersion: function(fileVersion){
        //give me a fileversion model object
        
        var neweid = fileVersion.get('change_eid');
        
        $.log('Attempting to fetch comments for version', fileVersion.get('version'), neweid);
        
        //we could cache the comments, but whatev for now
        //var oldeid = null;
        //if(this.version)
        //    oldeid = this.version.get('change_eid');
        //if(oldeid)
        //    this.versions[oldeid] = _.clone()
        
        //this calls toJSON,
        //then on success calls parse,
        //with the result of parse(), calls reset.
        this.fetch();
    },
    
    /**
     * provide either a change or an extract
     * position is: [x, y, width, height]
     */
    addComment: function(body, extract, position){
        var com = {};
        if(position && position.length == 4) com = {
                x: position[0],
                y: position[1],
                width: position[2],
                height: position[3]
            };
        
        com.body = body;
        com.extract = extract;
        
        $.log('Adding new comment: ', com, position);
        this.add(com);
    }
});

Q.FileUploader = Q.Module.extend('FileUploader', {

    available_events: ['onStart', 'onStartOne', 'onProgress', 'onFinishOne', 'onFinish', 'onError'],
    
    defs: {
        onStart: function(id, file) {
            $.log('Start: ', id, file.name, file);
        },
        onProgress: function(id, loaded, total, percentage, event) {
            $.log('Progress: ', id, loaded, total, percentage, event);
        },
        onLoad: function(id, event) {
            $.log('Loaded: ', id, event);
        },
        onSuccess: function(id, data) {
            $.log('Success!: ', id, data);
        },
        onError: function(id, code, event) {
            switch(code) {
                case event.target.error.NOT_FOUND_ERR:
                    Q.error('File not found!');
                break;
                case event.target.error.NOT_READABLE_ERR:
                    Q.error('File not readable!');
                break;
                case event.target.error.ABORT_ERR:
                break; 
                default:
                    Q.error('Read error.');
            }
        },
        forcedName: null, //if you always want an uploaded file to be a certain name, set this to that name
        method: 'POST',
        url: '',
        path: '/' //the file's path sent up in a header
    },
    
    init: function(container, settings){
        this._super(container, $.extend({}, this.defs, settings));
        _.bindAll(this, '_drop', '_send', 'onLoadError', 'onLoadProgress', 'onLoad', 'onSuccess', 'upload');
        
        // The inclusion of the event listeners (DragOver and drop)
        //this.uploadPlace =  document.getElementById(place);
        this.container[0].addEventListener("dragover", function(event) {
            event.stopPropagation(); 
            event.preventDefault();
        }, true);
        this.container[0].addEventListener("drop", this._drop, false);
    },
    
    wrap: function(fn, args){
        var self = this;
        return function(event){
            var a = args.slice(0);
            a.push(event);
            fn.apply(self, a);
        };
    },
    
    _drop: function(event) {
        event.preventDefault();
        var dt = event.dataTransfer;
        var files = dt.files;
        for (var i = 0; i<files.length; i++) {
            var file = files[i];
            this.upload(file);
        }
    },
    
    // Once the process of reading file
    _send: function(id, file, reader, event) {
        var bin = reader ? reader.result : null;
        var self = this;
        
        var s = self.wrap(this.onStart, [id, file, reader, bin]);
        if(false === s())
            return;
        
        function beforeSend(xhr, settings){
            var fupload = xhr.upload;
            var body = null;
            
            fupload.addEventListener('error', self.wrap(self.onLoadError, [id]), false);
            fupload.addEventListener('load', self.wrap(self.onLoad, [id]), false);
            fupload.addEventListener('progress', self.wrap(self.onLoadProgress, [id]), false);
            
            //we just send this as a binary wad in the request payload.
            xhr.setRequestHeader('X-Up-Filename', self.settings.forcedName || file.name);
            xhr.setRequestHeader('X-Up-Size', file.size);
            xhr.setRequestHeader('X-Up-Type', file.type);
            xhr.setRequestHeader('X-Up-Path', self.settings.path);
        }
        
        
        var ajaxOptions = {
            beforeSend: beforeSend,
            contentType: 'application/octet-stream; charset="utf-8"',
            url: $.extendUrl(this.settings.url, {binbody: true}),
            data: file,
            processData: false,
            dataType: 'json',
            success: self.wrap(self.onSuccess, [id]),
            type: 'POST'
        };
        $.ajax(ajaxOptions);
    },
    
    // Loading errors
    onLoadError: function(id, event) {
        if($.isFunction(this.settings.onError))
            this.settings.onError.call(this, id, event.target.error.code, event);
        this.trigger('loaderror', id, event);
    },
    
    onLoad: function(id, event) {
        if($.isFunction(this.settings.onLoad))
            this.settings.onLoad.call(this, id, event);
        this.trigger('load', id, event);
    },
    
    onSuccess: function(id, data) {
        if($.isFunction(this.settings.onSuccess))
            this.settings.onSuccess.call(this, id, data);
        this.trigger('success', id, data);
    },
    
    // Reading Progress
    onLoadProgress: function(id, event) {
        var percentage = null;
        if (event.lengthComputable) {
            percentage = Math.round((event.loaded * 100) / event.total);
        }
        if($.isFunction(this.settings.onProgress))
            this.settings.onProgress.call(this, id, event.loaded, event.total, percentage, event);
        this.trigger('progress', id, event.loaded, event.total, percentage, event);
    },
    
    onStart: function(id, file, reader, bin){
        if($.isFunction(this.settings.onStart))
            return this.settings.onStart.call(this, id, file);
        this.trigger('start', id, file, reader, bin);
        return true;
    },
    
    // Upload image files
	upload: function(file) {
        
        var self = this;
		// Firefox 3.6, Chrome 6, WebKit
		if(window.FileReader) {
            
            reader = new FileReader();
            
            // Firefox 3.6, WebKit
            if(reader.addEventListener) { 
                reader.addEventListener('loadend', this.wrap(this._send, [Q.FileUploader.id, file, reader]), false);
            // Chrome 7
            } else { 
                reader.onloadend = this.wrap(this._send, [Q.FileUploader.id, file, reader]);
            }
            
            // The function that starts reading the file as a binary string
            reader.readAsDataURL(file);
		
		}
        
        // Safari 5 does not support FileReader
        else {
			this._send(this.id, file, null);
		}
        
        Q.FileUploader.id++;
	}
});
Q.FileUploader.id = 2;

Q.UploadModule = Q.FileUploader.extend('UploadModule', {
    
    init: function(container, settings){
        /**
         * settings:
         * files
         */
        _.bindAll(this, 'handleDrag', 'onProgress');
        
        var defs = {
            files: null, //a Q.Files obj
            previewImage: '',
            maxPreviewSize: 5242880 //5MB
        };
        settings = $.extend({}, defs, settings);
        settings.onProgress = this.onProgress;
        
        this._super(container, settings);
        
        var set = this.settings;
        
        this.files = this.settings.files;
    },
    
    onStart: function(id, file, reader, bin){
        var ret = this._super(id, file, reader, bin);
        if(ret == false) return ret;
        
        //if not do some kind of error, and no upload of that file...
        if(!_.contains(Q.UploadModule.acceptableFormats, file.type));
        
        //figure out what the contents of the file are. our view will blindly jam it
        //into an image elem.
        var image = this.settings.previewImage;
        $.log(file.size, this.settings.maxPreviewSize, file.size < this.settings.maxPreviewSize);
        if(bin && _.contains(Q.UploadModule.previewFormats, file.type) && file.size < this.settings.maxPreviewSize)
            image = bin;
        
        //there is a problem here: we should look for an existing file potentially
        //If they are uploading a change to an existing file, we wont know about it
        
        //create a fake model, put it in the model container
        var m = {
            id: id,
            name: file.name,
            type: file.type,
            size: file.size,
            src: image,
            file: file,
            progress: 0,
            loaded: 0
        };
        m = new Q.ProcessingFile(m);
        if(m.type != 'processingFile'){
            $.error('Processing file must have different type', m);
            throw new Error('Processing file must have type processingFile not '+ m.type);
        }
        this.files.add(m);
        
        return true;
    },
    
    onProgress: function(id, loaded, total, percentage, event){
        $.log('onProgress', percentage);
        var m = this.files.get(id);
        if(m)
            m.set({
                progress: percentage,
                loaded: loaded
            });
    },
    
    onSuccess: function(id, data) {
        this._super(id, data);
        if(!data || !data.results){
            $.log('No data', data);
            return;
        }
        
        data = data.results;
        $.log('Uploaded!', id, data);
        
        data.id = data.eid;
        data.uploadId = id;
        var m = this.files.get(data.id);
        
        if(m){
            //this must be updated first!
            m.set({uploadId: data.uploadId});
            
            m.set(data);
        }
        else
            this.files.add(new Q.File(data));
    }
});

Q.UploadModule.acceptableFormats = [];
Q.UploadModule.previewFormats = ['image/gif', 'image/png'];

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
        if(this.model.get('full_path') != this.settings.path)
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

/**
 * We have
 * Q.ProcessingFile model - holds a currently being uploaded file.
 * Q.File model - holds a single uploaded file
 * Q.Files collection - holds some of the above
 *
 * Q.ProcessingFileView - view for a processing file
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
});

})(jQuery);