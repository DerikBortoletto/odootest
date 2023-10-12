odoo.define("middleware_rest_controller.default", function (require) {
    "use strict";

    var core = require("web.core");
    var session = require("web.session");
    var rpc = require("web.rpc");
    var Dialog = require("web.Dialog");
    var FieldManagerMixin = require("web.FieldManagerMixin");
    var FormController = require("web.FormController");
    var _domain = [];

    function handle_rpc (_model, _ctx, _conds, _method, _fields=[]) {
        return new Promise(function (resolve, reject) {
            rpc.query({
                model: _model,
                method: _method,
                fields: _fields,
                domain: _conds,
                context: _ctx
            }).then(function (result) {
                resolve(result);
            });
        });
    }

    function get_order_lines (_except_line_id) {
        return new Promise(function (resolve, reject) {
            var order_lines = [];
            $("table tr td:nth-child(2)").each(function () {
                if ($(this).parent("tr").attr("data-id") && $(this).parent("tr").attr("data-id") !== _except_line_id) {
                    order_lines.push({
                        id: null,
                        name: $(this).text(),
                        _id: $(this).parent("tr").attr("data-id")
                    });
                }
            });
            resolve(order_lines);
        });
    }

    function verify_line_item (_ctx, _order_line) {
        return new Promise(async function (resolve, reject) {
            var _content = ""
            if (_order_line.data && _order_line.data.product_id) {
                var _order_lines = await get_order_lines(_order_line.id);
                var _obj = {};
                _obj.id = _order_line.data.product_id.id;
                _obj.name = _order_line.data.product_id.display_name;
                _obj._id = _order_line.id;
                _order_lines.push(_obj);


                if (_order_lines.length > 0) {
                    var _tmp_names = [];
                    for (var i=0; i < _order_lines.length; i++) {
                        if (_tmp_names.includes(_order_lines[i].name)) {
                            _content = $("<div>");
                            _content.append($("<b>", {text: _order_lines[i].name}));
                            _content.append(core._t(" cannot be added twice!"));
                            break;
                        } else {
                            _tmp_names.push(_order_lines[i].name);
                        }
                    }

                    if (_content.length === 0 && _order_lines[_order_lines.length - 1].id) {
                        _domain = [
                            ["id", "=", _order_lines[_order_lines.length - 1].id]
                        ];
                        var _product = await handle_rpc("product.product", _ctx, _domain, "search_read", []);
                        if (_product) {
                            if (!_product[0].barcode) {
                                _content = $("<div>");
                                _content.append($("<b>", {text: _product[0].name}));
                                _content.append(core._t(" has no valid barcode!"));
                            }
                            if (_content.length === 0 && _product[0].company_id[0] !== session.user_companies.current_company[0]) {
                                _content = $("<div>");
                                _content.append($("<b>", {text: _product[0].name}));
                                _content.append(core._t(" is not linked with the company "));
                                _content.append($("<b>", {text: session.user_companies.current_company[1]}));
                                _content.append(".");
                            }
                        }
                    }
                }
            }
            resolve(_content);
        });
    }

    FormController.include({
        init: function (parent, model, renderer, params) {
            this._super.apply(this, arguments);
            FieldManagerMixin.init.call(this, this.model);
            this.savingDef = Promise.resolve();
            this.pendingChanges = [];
        },
        _applyChanges: async function (dataPointID, changes, event) {
            var _content = "";
            var _action = changes && changes.order_line ? changes.order_line.operation : null;
            var _model = this.modelName;
            if (_model === "purchase.order" || _model === "sale.order") {
                var _ctx = this.context;
                var curr_url = window.location.href;
                var url = curr_url.replace("#", "?");
                var q_str = url.split("?")[1];
                var q_params = q_str.split("&");
                var id = 0;
                for (var i=0; i < q_params.length; i++) {
                    if (q_params[i].split("=")[0] === "id" && q_params[i].split("=")[1]) {
                        id = parseInt(q_params[i].split("=")[1]);
                    }
                }

                if (id > 0) {
                    _domain = [
                        ["id", "=", id]
                    ];
                    var _state = await handle_rpc(_model, _ctx, _domain, "search_read", ["state"]);
                    if (_model === "purchase.order" && _state[0].state === "purchase") {
                        _content = $("<div>");
                        _content.append(core._t("A confirmed purchase order cannot be modified! You can cancel this order and create a new one."));
                    } else if (_model === "sale.order" && _state[0].state === "sale") {
                        _content = $("<div>");
                        _content.append(core._t("A confirmed sales order cannot be modified! You can cancel this order and create a new one."));
                    } else {
                        if (_action === "UPDATE") {
                            _content = await verify_line_item(_ctx, changes.order_line);
                        }
                    }
                } else {
                    if (_action === "UPDATE") {
                        _content = await verify_line_item(_ctx, changes.order_line);
                    }
                }

                if (_content.length > 0) {
                    new Dialog(this, {
                        title: core._t("Middleware: Alert"),
                        size: "medium",
                        $content: _content
                    }).open();
                    return false;
                }
            }
            this.pendingChanges.push({ dataPointID, changes, event });
            var _super = FieldManagerMixin._applyChanges.bind(this);
            return this.mutex.exec(() => {
                this.pendingChanges.shift();
                return _super(dataPointID, changes, event);
            });
        }
    });

    Dialog.include({
        renderElement: function () {
            this._super();
            if (this.$content) {
                this.setElement(this.$content);
            }
            if (this.$el[0].innerText && this.$el[0].innerText.toLowerCase().includes("inventory audit")) {
                this.$modal.find('.modal-title').first().html("Middleware: Access");
            }
            this.$el.addClass('modal-body ' + this.dialogClass);
        },
    });
});