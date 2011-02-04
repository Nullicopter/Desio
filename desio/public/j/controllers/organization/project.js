
;(function($){

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
        fieldName: 'file',
        method: 'POST',
        url: '',
        path: '/' //the file's path sent up in a header
    },
    
    init: function(container, settings){
        this._super(container, $.extend({}, this.defs, settings));
        this.id = 0;
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
        
        function beforeSend(xhr, settings){
            var fupload = xhr.upload;
            var body = null;
            
            fupload.addEventListener('error', self.wrap(self.onLoadError, [id]), false);
            fupload.addEventListener('load', self.wrap(self.onLoad, [id]), false);
            fupload.addEventListener('progress', self.wrap(self.onLoadProgress, [id]), false);
            
            //we just send this as a binary wad in the request payload.
            xhr.setRequestHeader('X-Up-Filename', file.name);
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
        
        /*
        //if we want to do multi part stuff, do this. BUt only works in firefox
        xhr.open(this.settings.method, this.settings.url, true);
        
        // Firefox 3.6 provides a feature sendAsBinary ()
        if(bin) {
            var boundary = 'xxxxxxxxx';
            body = '--' + boundary + "\r\n";  
            body += "Content-Disposition: form-data; name="+this.settings.fieldName+"; filename=\"" + file.name + "\"\r\n";  
            body += "Content-Type: application/octet-stream\r\n\r\n";
            body += window.btoa(bin) + "\r\n";
            body += '--' + boundary + '--';      
            xhr.setRequestHeader('content-type', 'multipart/form-data; boundary=' + boundary);
        }
        
        if(xhr.sendAsBinary != null && body){
            xhr.sendAsBinary(bin);
        }
        else if(body){
            xhr.send(body);
        }
        // This is safari!
        else { 
            xhr.open('POST', $.extendUrl(this.settings.url, {garbage: true}), true);
            xhr.setRequestHeader('Content-Type', 'application/octet-stream');
            xhr.setRequestHeader('X-UP-FILENAME', file.name);
            xhr.setRequestHeader('X-UP-SIZE', file.size);
            xhr.setRequestHeader('X-UP-TYPE', file.type);
            xhr.send(file);
        }*/
        
    },
    
    // Loading errors
    onLoadError: function(id, event) {
        if($.isFunction(this.settings.onError))
            this.settings.onError.call(this, id, event.target.error.code, event);
    },
    
    onLoad: function(id, event) {
        if($.isFunction(this.settings.onLoad))
            this.settings.onLoad.call(this, id, event);
    },
    
    onSuccess: function(id, data) {
        if($.isFunction(this.settings.onSuccess))
            this.settings.onSuccess.call(this, id, data);
    },
    
    // Reading Progress
    onLoadProgress: function(id, event) {
        var percentage = null;
        if (event.lengthComputable) {
            percentage = Math.round((event.loaded * 100) / event.total);
        }
        if($.isFunction(this.settings.onProgress))
            this.settings.onProgress.call(this, id, event.loaded, event.total, percentage, event);
    },
    
    // Preview images
    /*previewNow: function(event) {		
        bin = preview.result;
        var img = document.createElement("img"); 
        img.className = 'addedIMG';
        img.file = file;   
        img.src = bin;
        document.getElementById(show).appendChild(img);
    },*/
    
    // Upload image files
	upload: function(file) {
        
        if($.isFunction(this.settings.onStart))
            this.settings.onStart.call(this, this.id, file);
        
        var self = this;
		// Firefox 3.6, Chrome 6, WebKit
		if(window.FileReader) {
            
            reader = new FileReader();
            
            // Firefox 3.6, WebKit
            if(reader.addEventListener) { 
                reader.addEventListener('loadend', this.wrap(this._send, [this.id, file, reader]), false);
            // Chrome 7
            } else { 
                reader.onloadend = this.wrap(this._send, [this.id, file, reader]);
            }
            
            // The function that starts reading the file as a binary string
            reader.readAsBinaryString(file);
            
            //preview
            /*if(this.settings.preview){
                var preview = new FileReader();
                // Firefox 3.6, WebKit
                if(preview.addEventListener) { 
                    preview.addEventListener('loadend', this.previewNow, false);
                // Chrome 7	
                } else { 
                    preview.onloadend = this.previewNow;
                }
                preview.readAsDataURL(file);
            }*/
		
		}
        
        // Safari 5 does not support FileReader
        else {
			this._send(this.id, file, null);
		}
        
        this.id++;
	}
});

Q.ViewProjectPage = Q.Page.extend({
    run: function(){
        var self = this;
        this._super.apply(this, arguments);
        
        $(this.settings.dropzone).FileUploader({
            url: this.settings.url
        });
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