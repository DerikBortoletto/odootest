odoo.define('tracktrace.dashboard', function (require) {
"use strict";

var AbstractAction = require('web.AbstractAction');
var core = require('web.core');
var QWeb = core.qweb;
var ajax = require('web.ajax');
var rpc = require('web.rpc');
var _t = core._t;
var session = require('web.session');
var web_client = require('web.web_client');
var abstractView = require('web.AbstractView');

var TTRxDashboard = AbstractAction.extend({
	template:'ttrx2_connector_spt.TTRxDashboard',

    init: function(parent, context) {
        this._super(parent, context);
        this.dashboards_templates = ['ttrx2_connector_spt.DashboardTracktrace'];
    },

    willStart: function() {
        var self = this;
        return $.when(ajax.loadLibs(this), this._super()).then(function() {
            return self.fetch_data();
        });
    },

    start: function() {
            var self = this;
            this.set("title", 'TTRx Dashboard');
            return this._super().then(function() {
                self.render_dashboards();
            });
        },

    render_dashboards: function(){
        var self = this;
        _.each(this.dashboards_templates, function(template) {
                self.$('.o_ttrx_dashboard').append(QWeb.render(template, {widget: self}));
            });
        self.$(".o_ttrx_showactions").on('click', self, self._onShowActionClicked.bind(self));
    },

    fetch_data: function() {
        var self = this;
        var def1 =  this._rpc({
                model: 'connector.spt',
                method: 'get_data'
    }).then(function(result)
     {
	   self.show_demo = result['values']['show_demo'];
	   self.connector_id = result['values']['connector'];
	   self.values = result['values'];
    });
        return $.when(def1);
    },

    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------

    /**
     * @private
     * @param {MouseEvent}
     */
    _onShowActionClicked: function (e) {
        var self = this;
        e.preventDefault();
        var $action = $(e.currentTarget);
        var name = $action.parent().attr('name');
        var connector_id = self.connector_id;
        var title = $action.attr('title');
        var action_ref = name;
        if (self.show_demo == true) {
			alert('In demo mode');
        } else {
	        if (name.includes("ttrx2_connector_spt.")) {
				this._rpc({
				    model: 'connector.spt',
				    method: 'create_action',
				    args: [action_ref, title, connector_id],
				}).then(function (result) {
				    if (result.action) {
				        self.do_action(result.action, {
				            additional_context: $action.attr('context')
				        });
				    }
				});
			};
		};
    },

});

core.action_registry.add('tracktrace_dashboard', TTRxDashboard);

return TTRxDashboard;

});

