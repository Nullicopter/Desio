;/*******************************************************************************
 *
 ******************************************************************************/

(function($){

Q.ProjectUsers = Backbone.Collection.extend({
    initialize: function(models, settings){
        this.settings = settings;
    },
    
    sync: function(projectEid){
        //calls attach_users on the project after the project as been created.
        var p = {
            users: [],
            roles: [],
            project: projectEid
        };
        
        for(var i = 0; i < this.models.length; i++){
            p.users.push(this.models[i].get('user').id);
            p.roles.push(this.models[i].get('role'));
        }
        
        var self = this;
        function trig(){
            self.trigger('synced', arguments);
        }
        
        if(p.users.length > 0){
            p.users = p.users.join(',');
            p.roles = p.roles.join(',');
            $.postJSON(this.settings.syncUrl, p, trig, trig);
        }
        else
            trig({});
    }
});

Q.ProjectUser = Backbone.Model.extend({
});

Q.ProjectUserView = Q.View.extend({
    tagName: 'div',
    className: 'user',
    template: '#project-user-template',
    inviteTemplate: '#project-invite-template',
    events: {
        'change .role select': 'roleChange',
        'click .remove': 'remove'
    },
    
    init: function(container, settings){
        this._super(container, settings);
    },
    
    render: function() {
        var ma = this.model.attributes;
        
        if(ma.invite){
            var attr = {
                name: ma.user.name
            };
            $(this.el).html(_.template($(this.inviteTemplate).html(), attr));
        }
        else{
            var attr = {
                uid: ma.user.id,
                username: ma.user.username,
                email: ma.user.email,
                name: ma.user.name,
                role: ma.role
            };
            $(this.el).html(_.template($(this.template).html(), attr));
            $(this.el).find('select').val(attr.role);
        }
        return this;
    },
    
    remove: function(e){
        $.log(this.model.collection, this.settings);
        this.model.collection.remove(this.model);
        this.container.remove();
        
        if(this.settings.sync)
            $.postJSON(e.target.href);
        
        return false;
    },
    
    roleChange: function(e){
        this.model.set({role: $(e.target).val()});
    }
});

Q.ProjectUserAddForm = Q.AsyncForm.extend('ProjectUserAddForm', {
    init: function(container, settings){
        settings.defaultData = {u: '', role: 'read'};
        this._super(container, settings);
        
        this.getElement('u').inputHint();
    },
    
    _onSubmit: function(){
        if(this.settings.sync)
            this._super.apply(this, arguments);
        
        var data = this.val();
        $.log('submit', data, this.settings.sync);
        if(data.u && data.u in this.settings.userMap){ //this is the email!
            var m = {user: this.settings.userMap[data.u], role: data.role};
            this.user = m;
            this.val('u', m.user.id);
            this.settings.model.add(new Q.ProjectUser(m));
        }
        else if(this.settings.inviteUrl && this.settings.sync){
            var c = confirm(data.u + ' is not a member of your organization yet.\n\nDo you want to invite them to this project?');
            
            if(c){
                var m = {user: {name: data.u}, invite: true};
                this.settings.model.add(new Q.ProjectUser(m));
                
                $.postJSON(this.settings.inviteUrl, {email: data.u, role: data.role}, function(data){
                    Q.notify(data.results.invited_email+' has been successfully invited to this project.');
                });
                return false;
            }
        }
        else if(!this.settings.sync && data.u){
            alert(data.u + " is not a member of your organization yet.\n\nAfter you create the project, you can invite other people who arent already members of your organization from the project's settings pages.");
        }
        
        return this.settings.sync;
    },
    
    _validSubmit: function(){
        if(this.settings.sync && this.user)
            this._super.apply(this, arguments);
        else{
            this._submittersEnable(true);
            this.loader.stopLoading();
        }
        
        this.user = null;
        this.reset();
    }
});

Q.ProjectUserModule = Q.Module.extend('ProjectUserModule', {
    n: {
        email: '#user-email',
        addForm: '#add-project-user',
        users: '#project-users form'
    },
    
    init: function(container, settings){
        _.bindAll(this, 'addUser', 'removeUser', 'roleChange', 'synced');
        /**
         * settings:
         * projectUsers: [{user: {id: 2, username: 'blah', name: 'jim bob'}, role: 'admin'}]
         * userMap
         * roleUrl: '',
         * syncUrl: ''
         * sync: false //tells this thing to make async calls or not.
         */
        this._super(container, settings);
        
        this.model = new Q.ProjectUsers([], settings);
        
        settings.model = this.model;
        this.model.bind('add', this.addUser);
        this.model.bind('remove', this.removeUser);
        this.model.bind('change:role', this.roleChange);
        this.model.bind('synced', this.synced);
        
        this.n.addForm.ProjectUserAddForm(settings);
        
        this.n.email.autocomplete({source: settings.emails});
        
        for(var i = 0; i < settings.projectUsers.length; i++)
            this.model.add(new Q.ProjectUser(settings.projectUsers[i]));
    },
    
    roleChange: function(m){
        var p = {
            u: m.get('user').id,
            role: m.get('role')
        };
        if(this.settings.sync)
            $.postJSON(this.settings.roleUrl, p, null, {loader: this.loader});
        $.log('change role:', p);
    },
    
    removeUser: function(m){
        var u = m.get('user');
        this.settings.emails.push(u.email);
    },
    
    addUser: function(m){
        var u = m.get('user');
        this.settings.emails = _.without(this.settings.emails, u.email);
        this.n.email.autocomplete('option', {source: this.settings.emails});
        this.n.users.prepend(new Q.ProjectUserView({model: m, sync: this.settings.sync}).render().el);
    },
    
    sync: function(projectEid){this.model.sync(projectEid);},
    
    synced: function(){
        this.trigger('synced', arguments);
    }
});

})(jQuery);


