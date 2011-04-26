(function($){Q.File=Q.Model.extend({type:"file"});Q.FileVersion=Q.File.extend({type:"version"});Q.ProcessingFile=Q.File.extend({type:"processingFile"});Q.Files=Q.Collection.extend({model:Q.File});Q.FileVersions=Q.Files.extend({model:Q.FileVersion});Q.Directory=Q.Model.extend({init:function(){var self=this;var dirs=new Q.Directories([]);dirs.parent=this;var children=this.get("children");this.set({children:dirs},{silent:true});if(children)dirs.add(children,{save:false});dirs.bind("change:current",function(m){self.trigger("change:current",
m)})},isRoot:function(currentPath){currentPath=currentPath||"/";return this.get("full_path")==currentPath}});Q.Directories=Q.Collection.extend({model:Q.Directory,findPath:function(path){for(var i=0;i<this.length;i++){if(this.models[i].isRoot(path))return this.models[i];var p=this.models[i].get("children").findPath(path);if(p)return p}return null}});Q.Comment=Q.Model.extend({urls:{"create":"/api/v1/file/add_comment","delete":"/api/v1/file/remove_comment","completion":"/api/v1/file/set_comment_completion_status"},
statusToggle:{open:"completed",completed:"open"},init:function(){var com=new Q.Comments([]);com.parent=this;var replies=this.get("replies");this.set({replies:com},{silent:true});if(replies)com.add(replies,{save:false})},toJSON:function(method){if(method=="delete")return{comment:this.get("eid")};return this._super(method)},parse:function(data){$.log("Parsing comment success",data.results);data.results.id=data.results.eid;return data.results},hasPosition:function(){return this.get("position")?true:
false},toggleCompleteness:function(){var data={comment:this.id,status:this.statusToggle[this.get("completion_status").status]};var self=this;$.postJSON(this.urls.completion,data,function(data){$.log("Completion res",data.results);if(data&&data.results)self.set({completion_status:data.results})})}});Q.SingleSelectionModel=Q.Model.extend({init:function(key){this._super({});this.key=key},get:function(){return this._super(this.key)},set:function(m){var d={};d[this.key]=m;return this._super(d)}});Q.Comments=
Q.Collection.extend({urls:{"read":"/api/v1/file/get_comments"},model:Q.Comment,init:function(models,settings){this._super.apply(this,arguments);_.bindAll(this,"fetchForVersion","onChangeCompletionStatus");this.bind("change:completion_status",this.onChangeCompletionStatus)},setCurrentVersion:function(currentVersion){if(currentVersion)this.version=currentVersion},onChangeCompletionStatus:function(m){var v=this.version;if(!v)return;$.log("change complete",v,m);var numopen=v.get("number_comments_open");
var cs=m.get("completion_status");if(cs.status=="open")numopen++;else numopen--;v.set({number_comments_open:numopen})},_add:function(m,options){var self=this;options=options||{};var model=this._super.call(this,m,options);$.log("Adding comment",model.isNew()?"NEW":"NOT new",m,options);if(model.isNew()){if(this.parent)model.set({in_reply_to:this.parent.get("eid")});if(!model.get("extract")&&!model.get("change")&&this.version)model.set({change:this.version.get("change_eid")});if(options.save!=false&&
options.silent!=true)model.save({},{success:function(data){self.trigger("newcomment",model)}})}},toJSON:function(){return{change:this.version.get("change_eid")}},parse:function(data){if(data&&data.results&&data.results.comments)return data.results.comments;$.warn("Bad data on comment fetch?",data);return[]},fetchForVersion:function(fileVersion){var neweid=fileVersion.get("change_eid");$.log("Attempting to fetch comments for version",fileVersion.get("version"),neweid);this.setCurrentVersion(fileVersion);
this.fetch()},addComment:function(body,extract,position){var self=this;var com={};if(position&&position.length==4)com={x:position[0],y:position[1],width:position[2],height:position[3]};com.body=body;com.extract=extract;$.log("Adding new comment: ",com,position);this.add(com)}});Q.FileUploader=Q.Module.extend("FileUploader",{available_events:["onStart","onStartOne","onProgress","onFinishOne","onFinish","onError"],defs:{onStart:function(id,file){$.log("Start: ",id,file.name,file)},onProgress:function(id,
loaded,total,percentage,event){$.log("Progress: ",id,loaded,total,percentage,event)},onLoad:function(id,event){$.log("Loaded: ",id,event)},onSuccess:function(id,data){$.log("Success!: ",id,data)},onError:function(id,code,event){switch(code){case event.target.error.NOT_FOUND_ERR:Q.error("File not found!");break;case event.target.error.NOT_READABLE_ERR:Q.error("File not readable!");break;case event.target.error.ABORT_ERR:break;default:Q.error("Read error.")}},forcedName:null,method:"POST",url:"",path:"/"},
init:function(container,settings){this._super(container,$.extend({},this.defs,settings));_.bindAll(this,"_drop","_send","onLoadError","onLoadProgress","onLoad","onSuccess","upload");this.container[0].addEventListener("dragover",function(event){event.stopPropagation();event.preventDefault()},true);this.container[0].addEventListener("drop",this._drop,false)},wrap:function(fn,args){var self=this;return function(event){var a=args.slice(0);a.push(event);return fn.apply(self,a)}},_drop:function(event){event.preventDefault();
var dt=event.dataTransfer;var files=dt.files;for(var i=0;i<files.length;i++){var file=files[i];this.upload(file)}},_send:function(id,file,reader,event){var bin=reader?reader.result:null;var self=this;var s=self.wrap(this.onStart,[id,file,reader,bin]);var r=s();$.log("call start",r);if(false===r)return;function beforeSend(xhr,settings){var fupload=xhr.upload;var body=null;fupload.addEventListener("error",self.wrap(self.onLoadError,[id]),false);fupload.addEventListener("load",self.wrap(self.onLoad,
[id]),false);fupload.addEventListener("progress",self.wrap(self.onLoadProgress,[id]),false);xhr.setRequestHeader("X-Up-Filename",self.settings.forcedName||file.name);xhr.setRequestHeader("X-Up-Size",file.size);xhr.setRequestHeader("X-Up-Type",file.type);xhr.setRequestHeader("X-Up-Path",self.settings.path)}var ajaxOptions={beforeSend:beforeSend,contentType:'application/octet-stream; charset="utf-8"',url:$.extendUrl(this.settings.url,{binbody:true}),data:file,processData:false,dataType:"json",success:self.wrap(self.onSuccess,
[id]),type:"POST"};$.ajax(ajaxOptions)},onLoadError:function(id,event){if($.isFunction(this.settings.onError))this.settings.onError.call(this,id,event.target.error.code,event);this.trigger("loaderror",id,event)},onLoad:function(id,event){if($.isFunction(this.settings.onLoad))this.settings.onLoad.call(this,id,event);this.trigger("load",id,event)},onSuccess:function(id,data){if($.isFunction(this.settings.onSuccess))this.settings.onSuccess.call(this,id,data);this.trigger("success",id,data)},onLoadProgress:function(id,
event){var percentage=null;if(event.lengthComputable)percentage=Math.round(event.loaded*100/event.total);if($.isFunction(this.settings.onProgress))this.settings.onProgress.call(this,id,event.loaded,event.total,percentage,event);this.trigger("progress",id,event.loaded,event.total,percentage,event)},onStart:function(id,file,reader,bin){$.log("file type:",file.type);if(!_.contains(Q.UploadModule.acceptableFormats,file.type));if($.isFunction(this.settings.onStart))return this.settings.onStart.call(this,
id,file);this.trigger("start",id,file,reader,bin);return true},upload:function(file){var self=this;if(window.FileReader){reader=new FileReader;if(reader.addEventListener)reader.addEventListener("loadend",this.wrap(this._send,[Q.FileUploader.id,file,reader]),false);else reader.onloadend=this.wrap(this._send,[Q.FileUploader.id,file,reader]);reader.readAsDataURL(file)}else this._send(this.id,file,null);Q.FileUploader.id++}});Q.FileUploader.id=2;Q.UploadModule=Q.FileUploader.extend("UploadModule",{init:function(container,
settings){_.bindAll(this,"handleDrag","onProgress");var defs={files:null,previewImage:"",maxPreviewSize:5242880};settings=$.extend({},defs,settings);settings.onProgress=this.onProgress;this._super(container,settings);var set=this.settings;this.files=this.settings.files},onStart:function(id,file,reader,bin){var ret=this._super(id,file,reader,bin);if(ret==false)return ret;var image=this.settings.previewImage;$.log(file.size,this.settings.maxPreviewSize,file.size<this.settings.maxPreviewSize);if(bin&&
_.contains(Q.UploadModule.previewFormats,file.type)&&file.size<this.settings.maxPreviewSize)image=bin;var m={id:id,name:file.name,type:file.type,size:file.size,src:image,file:file,progress:0,loaded:0};m=new Q.ProcessingFile(m);if(m.type!="processingFile"){$.error("Processing file must have different type",m);throw new Error("Processing file must have type processingFile not "+m.type);}this.files.add(m);return true},onProgress:function(id,loaded,total,percentage,event){$.log("onProgress",percentage);
var m=this.files.get(id);if(m)m.set({progress:percentage,loaded:loaded})},onSuccess:function(id,data){this._super(id,data);if(!data||!data.results){$.log("No data",data);return}data=data.results;$.log("Uploaded!",id,data);data.id=data.eid;data.uploadId=id;var m=this.files.get(data.id);if(m){m.set({uploadId:data.uploadId});m.set(data)}else this.files.add(new Q.File(data))}});Q.UploadModule.acceptableFormats=[];Q.UploadModule.previewFormats=["image/gif","image/png"]})(jQuery);(function($){Q.FileView=Q.View.extend({tagName:"div",className:"file",template:"#file-template",formatters:{"size":"filesize(0)","number_comments":"number","created_date":"relativetime","name":"compressstr(28)"},init:function(container,settings){this._super(container,settings);_.bindAll(this,"render","updateVersion");this.model.view=this;this.model.bind("change:version",this.updateVersion)},updateVersion:function(m){$.log("FileView update version",m);this.render()},render:function(){var attr=$.extend({},
this.model.attributes);attr.user=attr.creator?attr.creator.name:"";$.log(attr);for(var k in attr)if(k in this.formatters)attr[k]=Q.DataFormatters.get(this.formatters[k],attr[k]);html=_.template($(this.template).html(),attr);this.container.html(html);return this}});Q.ProcessingFileView=Q.FileView.extend({className:"processing-file",template:"#upload-template",init:function(container,settings){this._super(container,settings);_.bindAll(this,"updateProgress");this.model.bind("change:progress",this.updateProgress)},
updateVersion:function(m){},_updateProgress:function(prog){var perc=Q.DataFormatters.percent(prog,0);var isup=prog<100;this.uploading[isup?"show":"hide"]();this.processing[isup?"hide":"show"]();this.progress.css({width:perc});(function(t){if(t.progtime)clearTimeout(t.progtime);t.progtime=setTimeout(function(){t._updateProgress(100)},1500)})(this)},updateProgress:function(m){var prog=m.get("progress");this._updateProgress(prog)},render:function(){this._super();$.log(this.model.get("src"));var img=
$("<img/>",{"class":"thumb"});img[0].file=this.model.get("file");img[0].src=this.model.get("src");this.container.find("img.thumb").replaceWith(img);this.progress=this.container.find(".progress");this.processing=this.container.find(".processing");this.uploading=this.container.find(".uploading");return this}});Q.DropTarget=Q.Module.extend("DropTarget",{init:function(c,s){var defs={template:"#droptarget-template",showOn:"elemdrag",targetClass:"target",onTargetEnter:function(){},onTargetLeave:function(){}};
this._super(c,$.extend({},defs,s));_.bindAll(this,"handleDrag","handleTargetEnter","handleTargetLeave","hideTarget");this._createDropTarget()},_createDropTarget:function(){this.target=$($(this.settings.template).html());var pos=this.container.css("position");if(!pos||pos=="static")this.container.css({position:"relative"});this.container.append(this.target);var elem=this.container;elem.bind("dragenter",this.handleDrag);this.target.bind("dragenter",this.handleTargetEnter);this.target.bind("dragleave",
this.handleTargetLeave)},handleDrag:function(event){$.log("handle Drag",event.target,this.target);if(event.type=="dragenter"&&this.target)this.target.show()},hideTarget:function(){this.target.hide()},handleTargetEnter:function(e){$.log("handleTargetEnter",e.target);if(!$(e.target).hasClass(this.settings.targetClass))return;if(this.settings.onTargetEnter.call(this,e)==false)return;this.target.addClass("over")},handleTargetLeave:function(e){$.log("handleTargetLeave",e.target);if(!$(e.target).hasClass(this.settings.targetClass))return;
if(this.settings.onTargetEnter.call(this,e)==false)return;setTimeout(this.hideTarget,200)},hide:function(){this.target.hide()},show:function(){this.target.show()}});Q.DirectoryView=Q.View.extend({tagName:"div",className:"directory",dropTemplate:"#droptarget-template",rootTemplate:"#root-template",dirTemplate:"#dir-template",init:function(container,settings){var defs={showDropTargetOn:"bodydrag"};this._super(container,$.extend({},defs,settings));_.bindAll(this,"render","addFile","updateVersion","handleTargetLeave");
this.model.view=this;this.files=this.model.get("files");this.files.bind("add",this.addFile);this.files.bind("change:version",this.updateVersion)},addFile:function(m){this.target.hide();$.log("adding processig file?",m,this.filesElem);if(m.type=="processingFile"){var view=new Q.ProcessingFileView({model:m});this.filesElem.prepend(view.render().el)}else{var view=new Q.FileView({model:m});var el=view.render().container;var pm=this.files.get(m.get("uploadId"));if(pm){$.log("poo",pm);pm.view.container.replaceWith(el);
pm.view.remove();this.files.remove(pm)}else this.filesElem.append(el)}this.updateFileClasses()},updateVersion:function(m){this.target.hide();var pm=this.files.get(m.attributes.uploadId);$.log("ver poo before",m,m.attributes.uploadId,m.attributes,m.get("uploadId"),this.files);if(pm){$.log("ver poo",pm,this.files);pm.view.container.replaceWith(m.view.container);pm.view.remove();this.files.remove(pm)}this.updateFileClasses()},updateFileClasses:function(){var elems=this.filesElem.children();elems.removeClass("posmod3").removeClass("posmod4");
for(var i=0;i<elems.length;i++){var el=elems.eq(i);if(i%3==0)el.addClass("posmod3");if(i%4==0)el.addClass("posmod4")}},handleTargetLeave:function(){if(this.files.length)return true;this.target.target.removeClass("over");return false},render:function(){var html;if(!this.model.isRoot(this.settings.path))html=_.template($(this.dirTemplate).html(),this.model.attributes);else html=_.template($(this.rootTemplate).html(),this.model.attributes);this.container.html(html);if(this.settings.showDropTargetOn){this.target=
this.container.find(".files-container").DropTarget({showOn:this.settings.showDropTargetOn,onTargetLeave:this.handleTargetLeave});this.filesElem=this.container.find(".files");if(this.files.length==0)this.target.show();else this.target.hide()}return this}});Q.FilesModule=Q.Module.extend("FilesModule",{init:function(container,settings){_.bindAll(this,"addDirectory");var defs={showDropTargetOn:"bodydrag",directories:[],previewImage:"",maxPreviewSize:5242880};settings=$.extend({},this.defs,settings);this._super(container,
settings);var set=this.settings;this.directories=new Q.Directories([]);this.directories.bind("add",this.addDirectory);for(var i=0;i<set.directories.length;i++){var attr=$.extend({},set.directories[i]);$.log(attr);attr.id=attr.eid;this.directories.add(new Q.Directory(attr))}},addDirectory:function(m){if(m.isRoot(this.settings.path)){var set=$.extend({},this.settings);var files=m.get("files");m.set({files:new Q.Files([])});var view=new Q.DirectoryView($.extend({},set,{model:m}));this.container.append(view.render().el);
set.path=$.pathJoin(m.attributes.path,m.attributes.name);set.files=m.get("files");$.log("Setting up upload module","@"+this.settings.role+"@");if(this.settings.role&&this.settings.role!="read")view.target.target.UploadModule(set);for(var j=0;j<files.length;j++){files[j].id=files[j].eid;m.get("files").add(new Q.File(files[j]))}}}})})(jQuery);
