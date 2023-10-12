# -*- coding: utf-8 -*-
from odoo import http
import json
import ast


class OdooRestController(http.Controller):
    api_ver = "/api/v1/"

    def __init__(self) -> None:
        self.user_id = None
        self.company_id = None
        self.response = None
        pass

    def response_handler(self, res=None):
        if res is not None and isinstance(res, str):
            self.response = {
                "status": "error",
                "message": res,
                "data": ""
            }
        else:
            self.response = {
                "status": "success",
                "message": "Execution successfully completed.",
                "data": "" if res is None else res
            }

    def is_allowed(self, params):
        is_authentic = False
        try:
            http.request.session.authenticate(params["db"], login=params["login"], password=params["password"])
            user = http.request.env["res.users"].sudo().search([("login", "=", params["login"])])
            self.user_id = user[-1].id
            self.company_id = user[-1].company_id[0].id
            is_authentic = True
        except Exception as e:
            print(e.__str__())
            self.response_handler("Access denied!")
        return is_authentic

    @http.route(api_ver + "po-creation", type="json", auth="none", methods=["POST"], csrf=False)
    def po_creation(self, **params):
        if self.is_allowed(params):
            try:
                payload = {
                    "partner_id": int(params["inputs"]["partner_id"]),
                    "name": params["inputs"]["name"],
                    "order_line": [(0, False, product) for product in json.loads(params["inputs"]["order_line"])]
                }
                po = http.request.env["purchase.order"].sudo().create(payload)
                if bool(po):
                    po.button_confirm()
                    res = dict()
                    res["purchase_order_id"] = po[-1].id
                    self.response_handler(res)
                else:
                    self.response_handler("Error! Unable to create the purchase order.")
            except Exception as e:
                self.response_handler(e.__str__())
        return self.response

    @http.route(api_ver + "po-receiving", type="json", auth="none", methods=["POST"], csrf=False)
    def po_receiving(self, **params):
        if self.is_allowed(params):
            try:
                po = http.request.env["purchase.order"].search([("id", "=", params["inputs"]["purchase_order_id"])])
                if bool(po):
                    get_stock_picking = po.action_view_picking()
                    if bool(get_stock_picking) and bool(get_stock_picking["res_id"]):
                        stock_picking = http.request.env["stock.picking"].sudo().search(
                            [("id", "=", get_stock_picking["res_id"])])
                        if bool(stock_picking):
                            if stock_picking[-1].state == "done":
                                self.response_handler("Error! Please check if already received.")
                            else:
                                stock_picking.button_validate()
                                immediate_transfer_line_ids = [[0, False, {
                                    "picking_id": get_stock_picking["res_id"],
                                    "to_immediate": True
                                }]]
                                payload = {
                                    "show_transfers": False,
                                    "pick_ids": [(6, False, [get_stock_picking["res_id"]])],
                                    "immediate_transfer_line_ids": immediate_transfer_line_ids
                                }

                                create_transfer = http.request.env["stock.immediate.transfer"].sudo().create(payload)
                                if bool(create_transfer):
                                    stock_transfer_id = create_transfer[-1].id
                                    transfer = http.request.env["stock.immediate.transfer"].sudo().search(
                                        [("id", "=", stock_transfer_id)])
                                    transfer.with_context(button_validate_picking_ids=transfer.pick_ids.ids).process()

                                    res = dict()
                                    res["stock_transfer_id"] = stock_transfer_id
                                    self.response_handler(res)
                                else:
                                    self.response_handler("Error! Unable to arrange the stock transfer.")
                        else:
                            self.response_handler("Error! Please check if already received.")
                    else:
                        self.response_handler("Error! Unable to receive the order.")
                else:
                    self.response_handler("Error! Purchase order not found.")
            except Exception as e:
                self.response_handler(e.__str__())
        return self.response

    @http.route(api_ver + "so-creation-with-delivery", type="json", auth="none", methods=["POST"], csrf=False)
    def so_creation_with_delivery(self, **params):
        if self.is_allowed(params):
            try:
                payload = {
                    "name": params["inputs"]["name"],
                    "warehouse_id": int(params["inputs"]["warehouse_id"]),
                    "partner_id": int(params["inputs"]["customer_id"]),
                    "order_line": [(0, False, product) for product in json.loads(params["inputs"]["order_line"])]
                }
                so = http.request.env["sale.order"].sudo().create(payload)
                if bool(so):
                    so.action_confirm()
                    sales_order_id = so[-1].id
                    get_stock_picking = so.action_view_delivery()
                    if bool(get_stock_picking) and bool(get_stock_picking["res_id"]):
                        stock_picking = http.request.env["stock.picking"].sudo().search(
                            [("id", "=", get_stock_picking["res_id"])])
                        if bool(stock_picking):
                            stock_picking.button_validate()

                            immediate_transfer_line_ids = [[0, False, {
                                'picking_id': get_stock_picking["res_id"],
                                'to_immediate': True
                            }]]
                            payload = {
                                'show_transfers': False,
                                'pick_ids': [(4, get_stock_picking["res_id"])],
                                'immediate_transfer_line_ids': immediate_transfer_line_ids
                            }

                            create_transfer = http.request.env["stock.immediate.transfer"].sudo().create(payload)
                            if bool(create_transfer):
                                stock_transfer_id = create_transfer[-1].id
                                transfer = http.request.env["stock.immediate.transfer"].sudo().search(
                                    [("id", "=", stock_transfer_id)])
                                transfer.with_context(button_validate_picking_ids=transfer.pick_ids.ids).process()

                                res = dict()
                                res["sales_order_id"] = sales_order_id
                                self.response_handler(res)
                            else:
                                self.response_handler("Error! Unable to arrange the stock transfer.")
                        else:
                            self.response_handler("Error! Unable to create the sales order.")
                    else:
                        self.response_handler("Error! Unable to pick stock.")
                else:
                    self.response_handler("Error! Unable to create the sales order.")
            except Exception as e:
                self.response_handler(e.__str__())
        return self.response

    @http.route(api_ver + "so-creation", type="json", auth="none", methods=["POST"], csrf=False)
    def so_creation(self, **params):
        if self.is_allowed(params):
            try:
                payload = {
                    "name": params["inputs"]["name"],
                    "warehouse_id": int(params["inputs"]["warehouse_id"]),
                    "partner_id": int(params["inputs"]["customer_id"]),
                    "order_line": [(0, False, product) for product in json.loads(params["inputs"]["order_line"])]
                }
                so = http.request.env["sale.order"].sudo().create(payload)
                if bool(so):
                    so.action_confirm()
                    res = dict()
                    res["sales_order_id"] = so[-1].id
                    self.response_handler(res)
                else:
                    self.response_handler("Error! Unable to create the sales order.")
            except Exception as e:
                self.response_handler(e.__str__())
        return self.response

    @http.route(api_ver + "sale-order-delivery", type="json", auth="none", methods=["POST"], csrf=False)
    def sale_order_delivery(self, **params):
        if self.is_allowed(params):
            try:
                so = http.request.env["sale.order"].search([("id", "=", params["inputs"]["sales_order_id"])])
                if bool(so):
                    get_stock_picking = so.action_view_delivery()
                    if bool(get_stock_picking) and bool(get_stock_picking["res_id"]):
                        stock_picking = http.request.env["stock.picking"].sudo().search(
                            [("id", "=", get_stock_picking["res_id"])])
                        if bool(stock_picking):
                            if stock_picking[-1].state == "done":
                                self.response_handler("Error! Please check if already delivered.")
                            else:
                                stock_picking.button_validate()
                                immediate_transfer_line_ids = [[0, False, {
                                    "picking_id": get_stock_picking["res_id"],
                                    "to_immediate": True
                                }]]
                                payload = {
                                    "show_transfers": False,
                                    "pick_ids": [(6, False, [get_stock_picking["res_id"]])],
                                    "immediate_transfer_line_ids": immediate_transfer_line_ids
                                }

                                create_transfer = http.request.env["stock.immediate.transfer"].sudo().create(payload)
                                if bool(create_transfer):
                                    stock_transfer_id = create_transfer[-1].id
                                    transfer = http.request.env["stock.immediate.transfer"].sudo().search(
                                        [("id", "=", stock_transfer_id)])
                                    transfer.with_context(button_validate_picking_ids=transfer.pick_ids.ids).process()

                                    res = dict()
                                    res["stock_transfer_id"] = stock_transfer_id
                                    self.response_handler(res)
                                else:
                                    self.response_handler("Error! Unable to arrange the stock transfer.")
                        else:
                            self.response_handler("Error! Please check if already delivered.")
                    else:
                        self.response_handler("Error! Unable to deliver the order.")
                else:
                    self.response_handler("Error! Sales order not found.")
            except Exception as e:
                self.response_handler(e.__str__())
        return self.response

    @http.route(api_ver + "create-warehouse", type="json", auth="none", methods=["POST"], csrf=False)
    def create_warehouse(self, **params):
        if self.is_allowed(params):
            try:
                payload = {
                    "name": params["inputs"]["name"],
                    "code": params["inputs"]["short_name"],
                    "partner_id": int(params["inputs"]["partner_id"])
                }
                wh_created = http.request.env["stock.warehouse"].sudo().create(payload)
                if bool(wh_created):
                    res = dict()
                    res["warehouse_id"] = wh_created[-1].id
                    res["warehouse_location_id"] = wh_created[-1].view_location_id[0].id
                    res["warehouse_code"] = payload["code"]
                    self.response_handler(res)
                else:
                    self.response_handler("Error! Unable to create the warehouse.")
            except Exception as e:
                self.response_handler(e.__str__())
        return self.response

    @http.route(api_ver + "create-location", type="json", auth="none", methods=["POST"], csrf=False)
    def create_location(self, **params):
        if self.is_allowed(params):
            try:
                payload = {
                    "name": params["inputs"]["name"],
                    "location_id": int(params["inputs"]["parent"]),
                    "active": params["inputs"]["status"]
                }
                loc_created = http.request.env["stock.location"].sudo().create(payload)
                if bool(loc_created):
                    res = dict()
                    res["location_id"] = loc_created[-1].id
                    self.response_handler(res)
                else:
                    self.response_handler("Error! Unable to create the location.")
            except Exception as e:
                self.response_handler(e.__str__())
        return self.response

    @http.route(api_ver + "get-country-state-ids", type="json", auth="none", methods=["POST"], csrf=False)
    def get_country_state_ids(self, **params):
        if self.is_allowed(params):
            try:
                country_id = None
                state_id = None

                country_name = params["inputs"]["country_name"]
                state_name = params["inputs"]["state_name"]
                countries = http.request.env["res.country"].sudo().search([])
                for each in countries:
                    if country_name.lower() == "united states of america" and each.name.lower() == "united states":
                        country_id = int(each.id)
                    elif country_name.lower() in each.name.lower() and each.name.lower().endswith(country_name.lower()):
                        country_id = int(each.id)

                if country_id is not None:
                    states = http.request.env["res.country.state"].sudo().search([("country_id", "=?", country_id)])
                    for each in states:
                        if state_name.lower() in each.name.lower() and each.name.lower().startswith(state_name.lower()):
                            state_id = int(each.id)

                res = dict()
                res["country_id"] = country_id
                res["state_id"] = state_id
                self.response_handler(res)
            except Exception as e:
                self.response_handler(e.__str__())
        return self.response

    @http.route(api_ver + "create-partner", type="json", auth="none", methods=["POST"], csrf=False)
    def create_partner(self, **params):
        if self.is_allowed(params):
            try:
                payload = {
                    "name": params["inputs"]["name"],
                    "is_company": params["inputs"]["is_company"],
                    "active": params["inputs"]["active"],
                    "email": params["inputs"]["email"],
                    "mobile": params["inputs"]["mobile"],
                    "phone": params["inputs"]["phone"],
                    "street": params["inputs"]["street"],
                    # "street2": params["inputs"]["street2"],
                    "city": params["inputs"]["city"],
                    "state_id": int(params["inputs"]["state_id"]),
                    "zip": params["inputs"]["zip"],
                    "country_id": int(params["inputs"]["country_id"])
                }
                if "supplier_rank" in params["inputs"]:
                    payload["supplier_rank"] = int(params["inputs"]["supplier_rank"])
                if "customer_rank" in params["inputs"]:
                    payload["customer_rank"] = int(params["inputs"]["customer_rank"])

                supplier_created = http.request.env["res.partner"].sudo().create(payload)
                if bool(supplier_created):
                    res = dict()
                    res["partner_id"] = supplier_created[-1].id
                    self.response_handler(res)
                else:
                    self.response_handler("Error! Unable to create the partner.")
            except Exception as e:
                self.response_handler(e.__str__())
        return self.response

    @http.route(api_ver + "create-product", type="json", auth="none", methods=["POST"], csrf=False)
    def create_product(self, **params):
        if self.is_allowed(params):
            try:
                is_ready = True
                payload = dict()
                for key, val in params["inputs"].items():
                    if key not in ["attributes", "suppliers"]:
                        payload[key] = val

                if "attributes" in params["inputs"] and bool(params["inputs"]["attributes"]):
                    attribute_line_ids = list()
                    for each in params["inputs"]["attributes"]:
                        attribute_temp = dict()
                        for key, val in each.items():
                            attribute_exists = http.request.env["product.attribute"].sudo().search(
                                [("name", "ilike", key)])
                            if bool(attribute_exists):
                                attribute_id = attribute_exists[-1].id
                                attribute_temp["attribute_id"] = attribute_id
                                attribute_value_ids = list()
                                for _v in val:
                                    attribute_value_exists = http.request.env["product.attribute.value"].sudo().search(
                                        [("attribute_id", "=", attribute_id), ("name", "ilike", _v)])
                                    if bool(attribute_value_exists):
                                        attribute_value_id = attribute_value_exists[-1].id
                                        attribute_value_ids.append(attribute_value_id)
                                if bool(attribute_value_ids):
                                    attribute_temp["value_ids"] = [(6, False, attribute_value_ids)]
                                else:
                                    self.response_handler("Error! Attribute value does not exist.")
                                    is_ready = False
                            else:
                                self.response_handler("Error! Attribute does not exist.")
                                is_ready = False
                        if bool(attribute_temp):
                            attribute_line_ids.append((0, 0, attribute_temp))
                    if bool(attribute_line_ids):
                        payload["attribute_line_ids"] = attribute_line_ids

                if "suppliers" in params["inputs"] and bool(params["inputs"]["suppliers"]):
                    payload["seller_ids"] = [(0, False, supplier) for supplier in params["inputs"]["suppliers"]]

                if is_ready:
                    product_created = http.request.env["product.template"].sudo().create(payload)
                    if bool(product_created):
                        read_product = http.request.env["product.product"].sudo().search(
                            [("product_tmpl_id", "=", int(product_created[-1].id))])
                        res = dict()
                        res["product_id"] = read_product[-1].id
                        res["product_tracking"] = read_product[-1].tracking
                        res["product_code"] = read_product[-1].barcode
                        self.response_handler(res)
                    else:
                        self.response_handler("Error! Unable to create the product.")
            except Exception as e:
                self.response_handler(e.__str__())
        return self.response

    @http.route(api_ver + "link-suppliers-to-product", type="json", auth="none", methods=["POST"], csrf=False)
    def link_suppliers_to_product(self, **params):
        if self.is_allowed(params):
            try:
                product_id = int(params["inputs"]["product_id"])
                product = http.request.env["product.product"].sudo().search([("id", "=", product_id)])
                if bool(product):
                    pass
                else:
                    self.response_handler("Product not found!")
            except Exception as e:
                self.response_handler(e.__str__())
        return self.response

    @staticmethod
    def get_order_name(rec):
        _tmp = str(rec.date_order)
        _tmp = _tmp.replace("-", "")
        _tmp = _tmp.replace(" ", "")
        _tmp = _tmp.replace(":", "")
        return rec.name + "-" + _tmp

    @staticmethod
    def get_location_by_purchase_order(po_id):
        location = None
        po = http.request.env["purchase.order"].sudo().search([("id", "=", int(po_id))])
        if bool(po):
            location = po[-1].picking_type_id[0].warehouse_id[0].name
            location = location.split(":")[0]
        return location

    @http.route(api_ver + "list-purchase-orders", type="json", auth="none", methods=["POST"], csrf=False)
    def list_purchase_orders(self, **params):
        if self.is_allowed(params):
            try:
                purchase_orders = list()
                is_fetch_all = True if "is_all_users" in params["inputs"] and bool(
                    params["inputs"]["is_all_users"]) else False
                conditions = list()
                conditions.append(("state", "in", ["purchase", "done"]))
                conditions.append(("company_id", "=", int(self.company_id)))
                if not is_fetch_all:
                    conditions.append(("user_id", "=", int(self.user_id)))
                _limit = 10
                _offset = 0
                if "page" in params["inputs"]:
                    _offset = (int(params["inputs"]["page"]) - 1) * _limit
                p_orders_data = http.request.env["purchase.order"].sudo().search(conditions, order="id desc", offset=_offset, limit=_limit)
                for _po in p_orders_data:
                    temp = dict()
                    temp["id"] = _po.id
                    temp["name"] = self.get_order_name(_po)
                    temp["vendor"] = _po.partner_id[0].name
                    temp["location"] = self.get_location_by_purchase_order(_po.id)
                    temp["created_on"] = _po.date_order
                    purchase_orders.append(temp)
                self.response_handler(purchase_orders)
            except Exception as e:
                self.response_handler(e.__str__())
        return self.response

    @staticmethod
    def get_location_by_sale_order(so_id):
        location = None
        so = http.request.env["sale.order"].sudo().search([("id", "=", int(so_id))])
        if bool(so):
            location = so[-1].warehouse_id[0].name
            location = location.split(":")[0]
        return location

    @http.route(api_ver + "list-sale-orders", type="json", auth="none", methods=["POST"], csrf=False)
    def list_sale_orders(self, **params):
        if self.is_allowed(params):
            try:
                sale_orders = list()
                is_fetch_all = True if "is_all_users" in params["inputs"] and bool(
                    params["inputs"]["is_all_users"]) else False
                conditions = list()
                conditions.append(("state", "not in", ["draft", "sent", "cancel"]))
                conditions.append(("company_id", "=", int(self.company_id)))
                if not is_fetch_all:
                    conditions.append(("user_id", "=", int(self.user_id)))
                _limit = 10
                _offset = 0
                if "page" in params["inputs"]:
                    _offset = (int(params["inputs"]["page"]) - 1) * _limit
                s_orders_data = http.request.env["sale.order"].sudo().search(conditions, order="id desc", offset=_offset, limit=_limit)
                for _so in s_orders_data:
                    temp = dict()
                    temp["id"] = _so.id
                    temp["name"] = self.get_order_name(_so)
                    temp["customer"] = _so.partner_id[0].name
                    temp["location"] = self.get_location_by_sale_order(_so.id)
                    temp["created_on"] = _so.date_order
                    sale_orders.append(temp)

                self.response_handler(sale_orders)
            except Exception as e:
                self.response_handler(e.__str__())
        return self.response

    @http.route(api_ver + "list-line-items-by-purchase-order", type="json", auth="none", methods=["POST"], csrf=False)
    def list_line_items_by_purchase_order(self, **params):
        if self.is_allowed(params):
            try:
                po = http.request.env["purchase.order"].sudo().search([("id", "=", int(params["inputs"]["po_id"]))])
                if bool(po):
                    order_line = po[-1].order_line
                    line_item_ids = list()
                    for line in order_line:
                        line_item_ids.append(line[0].id)
                    if bool(line_item_ids):
                        list_line_items = list()
                        for li_id in line_item_ids:
                            line_item = http.request.env["purchase.order.line"].sudo().search([("id", "=", int(li_id))])
                            product = line_item[-1].product_id
                            temp = dict()
                            temp["transaction_type"] = "purchase"
                            temp["product_id"] = product[0].id
                            temp["product_code"] = product[0].barcode if bool(product[0].barcode) else ""
                            temp["product_name"] = product[0].name
                            product_variant = http.request.env["product.product"].sudo().search(
                                [("id", "=", int(product[0].id))])
                            product_template = http.request.env["product.template"].sudo().search(
                                [("id", "=", int(product_variant[-1].product_tmpl_id))])
                            # temp["product_uom_id"] = product_template[-1].uom_id[0].id
                            temp["product_tracking"] = product_template[-1].tracking
                            temp["product_demand_quantity"] = line_item[-1].product_qty
                            temp["product_received_quantity"] = line_item[-1].qty_received
                            temp["product_qty_to_receive"] = line_item[-1].product_qty - line_item[-1].qty_received
                            list_line_items.append(temp)
                        self.response_handler(list_line_items)
                    else:
                        self.response_handler("Error! Line items not found for the given purchase order.")
                else:
                    self.response_handler("Error! Given purchase order does not exist.")
            except Exception as e:
                self.response_handler(e.__str__())
        return self.response

    @http.route(api_ver + "receiving-by-purchase-order", type="json", auth="none", methods=["POST"], csrf=False)
    def receiving_by_purchase_order(self, **params):
        if self.is_allowed(params):
            try:
                is_backorder = False
                po = http.request.env["purchase.order"].sudo().search([("id", "=", int(params["inputs"]["po_id"]))])
                if bool(po):
                    order_line = po[-1].order_line
                    line_item_ids = list()
                    for line in order_line:
                        line_item_ids.append(line[0].id)
                    if bool(line_item_ids):
                        products_id = list()
                        products_qty_to_receive = list()
                        products_product_uom_id = list()
                        for li_id in line_item_ids:
                            line_item = http.request.env["purchase.order.line"].sudo().search([("id", "=", int(li_id))])
                            product = line_item[-1].product_id
                            products_id.append(int(product[0].id))

                            product_variant = http.request.env["product.product"].sudo().search(
                                [("id", "=", int(product[0].id))])
                            product_template = http.request.env["product.template"].sudo().search(
                                [("id", "=", int(product_variant[-1].product_tmpl_id))])
                            products_product_uom_id.append(
                                {"product_id": str(product[0].id), "uom_id": product_template[-1].uom_id[0].id})
                            products_qty_to_receive.append({"product_id": str(product[0].id),
                                                            "qty_to_receive": line_item[-1].product_qty - line_item[
                                                                -1].qty_received})

                        go = True
                        products_to_this_receiving = list()
                        invalid_product_details = False
                        lot_name_exist = None
                        serial_name_exist = None
                        for l_item in params["inputs"]["line_items"]:
                            for key, val in l_item.items():
                                if key == "serials":
                                    for _l_i in val:
                                        if go:
                                            if "product_id" in _l_i and int(_l_i["product_id"]) in products_id:
                                                if int(_l_i["product_id"]) not in products_to_this_receiving:
                                                    products_to_this_receiving.append(int(_l_i["product_id"]))
                                                _check_ls_name = None
                                                if "serial_name" in _l_i and bool(_l_i["serial_name"]):
                                                    _check_ls_name = _l_i["serial_name"]
                                                if bool(_check_ls_name):
                                                    lot_serial = http.request.env["stock.production.lot"].sudo().search(
                                                        [("name", "=", _check_ls_name)])
                                                    if bool(lot_serial):
                                                        serial_name_exist = _check_ls_name
                                                        go = False
                                            else:
                                                invalid_product_details = True
                                                go = False
                                elif key == "lots":
                                    for _l_i in val:
                                        if go:
                                            if "product_id" in _l_i and int(_l_i["product_id"]) in products_id:
                                                if int(_l_i["product_id"]) not in products_to_this_receiving:
                                                    products_to_this_receiving.append(int(_l_i["product_id"]))
                                                _check_ls_name = None
                                                if "lot_name" in _l_i and bool(_l_i["lot_name"]):
                                                    _check_ls_name = _l_i["lot_name"]
                                                if bool(_check_ls_name):
                                                    lot_serial = http.request.env["stock.production.lot"].sudo().search(
                                                        [("name", "=", _check_ls_name)])
                                                    if bool(lot_serial):
                                                        lot_name_exist = _check_ls_name
                                                        go = False
                                            else:
                                                invalid_product_details = True
                                                go = False
                                else:
                                    for _l_i in val:
                                        if "product_id" not in _l_i or int(_l_i["product_id"]) not in products_id:
                                            if int(_l_i["product_id"]) not in products_to_this_receiving:
                                                products_to_this_receiving.append(int(_l_i["product_id"]))
                                            invalid_product_details = True
                                            go = False
                        if go:
                            if len(products_id) > len(products_to_this_receiving):
                                is_backorder = True

                            view_stock_picking = po.action_view_picking()
                            if bool(view_stock_picking) and bool(view_stock_picking["res_id"]):
                                stock_picking_id = int(view_stock_picking["res_id"])
                            else:
                                domain = view_stock_picking["domain"]
                                try:
                                    domain = ast.literal_eval(view_stock_picking["domain"])
                                except Exception as e:
                                    e.__str__()
                                    pass
                                stock_picking_id = int(domain[0][2][0])
                            stock_picking = http.request.env["stock.picking"].sudo().search(
                                [("id", "=", stock_picking_id)])

                            revised_line_items = list()
                            for l_item in params["inputs"]["line_items"]:
                                if go:
                                    for key, val in l_item.items():
                                        if key == "serials":
                                            line_item_product_id = None
                                            serials = list()
                                            for _l_i in val:
                                                line_item_product_id = int(_l_i["product_id"])

                                                product_uom_id = None
                                                for each in products_product_uom_id:
                                                    if int(each["product_id"]) == int(_l_i["product_id"]):
                                                        product_uom_id = each["uom_id"]
                                                if not bool(product_uom_id):
                                                    go = False
                                                    self.response_handler("Error! Invalid product uom id detected.")

                                                if go:
                                                    temp = dict()
                                                    temp["product_uom_id"] = int(product_uom_id)
                                                    temp["product_id"] = int(_l_i["product_id"])
                                                    temp["qty_done"] = int(_l_i["qty_done"])
                                                    temp["company_id"] = stock_picking[-1].company_id[0].id
                                                    temp["location_dest_id"] = stock_picking[-1].location_dest_id[0].id
                                                    temp["location_id"] = stock_picking[-1].location_id[0].id
                                                    temp["picking_id"] = stock_picking_id
                                                    temp["lot_name"] = _l_i["serial_name"]
                                                    temp["lot_id"] = False
                                                    temp["move_id"] = False
                                                    temp["owner_id"] = False
                                                    temp["package_id"] = False
                                                    temp["package_level_id"] = False
                                                    serials.append(temp)

                                            if bool(serials):
                                                for each in products_qty_to_receive:
                                                    if int(each["product_id"]) == int(line_item_product_id):
                                                        if int(each["qty_to_receive"]) > len(serials):
                                                            is_backorder = True
                                                        if int(each["qty_to_receive"]) < len(serials):
                                                            go = False
                                                            self.response_handler(
                                                                "Error! Receiving quantity of a serial-based product is bigger than the purchase order quantity.")
                                                revised_line_items.append(serials)
                                        elif key == "lots":
                                            lots = list()
                                            total_done_qty = 0
                                            line_item_product_id = None
                                            for _l_i in val:
                                                line_item_product_id = int(_l_i["product_id"])

                                                product_uom_id = None
                                                for each in products_product_uom_id:
                                                    if int(each["product_id"]) == int(_l_i["product_id"]):
                                                        product_uom_id = each["uom_id"]
                                                if not bool(product_uom_id):
                                                    go = False
                                                    self.response_handler("Error! Invalid product uom id detected.")

                                                if go:
                                                    total_done_qty = total_done_qty + int(_l_i["qty_done"])
                                                    temp = dict()
                                                    temp["product_uom_id"] = int(product_uom_id)
                                                    temp["product_id"] = int(_l_i["product_id"])
                                                    temp["qty_done"] = int(_l_i["qty_done"])
                                                    temp["company_id"] = stock_picking[-1].company_id[0].id
                                                    temp["location_dest_id"] = stock_picking[-1].location_dest_id[0].id
                                                    temp["location_id"] = stock_picking[-1].location_id[0].id
                                                    temp["picking_id"] = stock_picking_id
                                                    temp["lot_name"] = _l_i["lot_name"]
                                                    temp["lot_id"] = False
                                                    temp["move_id"] = False
                                                    temp["owner_id"] = False
                                                    temp["package_id"] = False
                                                    temp["package_level_id"] = False
                                                    lots.append(temp)
                                            if bool(lots):
                                                for each in products_qty_to_receive:
                                                    if int(each["product_id"]) == int(line_item_product_id):
                                                        if int(each["qty_to_receive"]) > total_done_qty:
                                                            is_backorder = True
                                                        if int(each["qty_to_receive"]) < total_done_qty:
                                                            go = False
                                                            self.response_handler(
                                                                "Error! Receiving quantity of a lot-based product is bigger than the purchase order quantity.")
                                                revised_line_items.append(lots)
                                        elif key == "normal":
                                            normal = list()
                                            for _l_i in val:
                                                line_item_product_id = int(_l_i["product_id"])

                                                product_uom_id = None
                                                for each in products_product_uom_id:
                                                    if int(each["product_id"]) == int(_l_i["product_id"]):
                                                        product_uom_id = each["uom_id"]
                                                if not bool(product_uom_id):
                                                    go = False
                                                    self.response_handler("Error! Invalid product uom id detected.")

                                                for each in products_qty_to_receive:
                                                    if int(each["product_id"]) == int(line_item_product_id):
                                                        if int(each["qty_to_receive"]) > int(_l_i["qty_done"]):
                                                            is_backorder = True
                                                        if int(each["qty_to_receive"]) < int(_l_i["qty_done"]):
                                                            go = False
                                                            self.response_handler(
                                                                "Error! Receiving quantity of a product is bigger than the purchase order quantity.")
                                                if go:
                                                    temp = dict()
                                                    temp["product_uom_id"] = int(product_uom_id)
                                                    temp["product_id"] = int(_l_i["product_id"])
                                                    temp["qty_done"] = int(_l_i["qty_done"])
                                                    temp["company_id"] = stock_picking[-1].company_id[0].id
                                                    temp["location_dest_id"] = stock_picking[-1].location_dest_id[0].id
                                                    temp["location_id"] = stock_picking[-1].location_id[0].id
                                                    temp["picking_id"] = stock_picking_id
                                                    temp["lot_name"] = False
                                                    temp["lot_id"] = False
                                                    temp["move_id"] = False
                                                    temp["owner_id"] = False
                                                    temp["package_id"] = False
                                                    temp["package_level_id"] = False
                                                    normal.append(temp)
                                            if bool(normal):
                                                revised_line_items.append(normal)
                            if go:
                                for revised_line in revised_line_items:
                                    if go:
                                        stock_to_be_moved = list()
                                        for i in range(len(stock_picking[-1].move_ids_without_package)):
                                            stock_move = http.request.env["stock.move"].sudo().search(
                                                [("id", "=", stock_picking[-1].move_ids_without_package[i].id)])
                                            if bool(stock_move):
                                                for line in revised_line:
                                                    if int(line["product_id"]) == int(stock_move[-1].product_id[0].id):

                                                        target_product_name = stock_move[-1].product_id[0].name
                                                        qty_to_pick = 0
                                                        for _line in revised_line:
                                                            if int(_line["product_id"]) == int(line["product_id"]):
                                                                qty_to_pick = qty_to_pick + int(_line["qty_done"])
                                                        if qty_to_pick > 0:
                                                            if int(stock_move[-1].product_qty) - int(
                                                                    stock_move[-1].quantity_done) >= qty_to_pick:
                                                                if line["product_id"] not in stock_to_be_moved:
                                                                    stock_to_be_moved.append(line["product_id"])
                                                                    stock_move.sudo().write({
                                                                        "move_line_nosuggest_ids": [
                                                                            (0, False, line) for
                                                                            line in
                                                                            revised_line]})
                                                            else:
                                                                go = False
                                                                self.response_handler(
                                                                    "Error! Unable to receive the requested quantity of " + target_product_name + ".")

                                if go:
                                    try:
                                        stock_picking.button_validate()
                                        if is_backorder:
                                            data = dict()
                                            data["backorder_confirmation_line_ids"] = [
                                                (0, False, {"picking_id": stock_picking_id, "to_backorder": True})]
                                            data["pick_ids"] = [(6, False, [stock_picking_id])]
                                            data["show_transfers"] = False
                                            backorder = http.request.env["stock.backorder.confirmation"].sudo().create(
                                                data)
                                            backorder.with_context(
                                                button_validate_picking_ids=backorder.pick_ids.ids).process()
                                        self.response_handler()
                                    except Exception as e:
                                        self.response_handler(e.__str__())
                        else:
                            if bool(lot_name_exist):
                                self.response_handler("Error! Lot number(" + lot_name_exist + ") already exists.")
                            elif bool(serial_name_exist):
                                self.response_handler("Error! Serial number(" + serial_name_exist + ") already exists.")
                            elif bool(invalid_product_details):
                                self.response_handler("Error! Invalid product details supplied.")
                    else:
                        self.response_handler("Error! Line items not found for the given purchase order.")
                else:
                    self.response_handler("Error! Given purchase order does not exist.")
            except Exception as e:
                self.response_handler(e.__str__())
        return self.response

    @http.route(api_ver + "list-line-items-by-sale-order", type="json", auth="none", methods=["POST"], csrf=False)
    def list_line_items_by_sale_order(self, **params):
        if self.is_allowed(params):
            try:
                po = http.request.env["sale.order"].sudo().search([("id", "=", int(params["inputs"]["so_id"]))])
                if bool(po):
                    order_line = po[-1].order_line
                    line_item_ids = list()
                    for line in order_line:
                        line_item_ids.append(line[0].id)
                    if bool(line_item_ids):
                        list_line_items = list()
                        for li_id in line_item_ids:
                            line_item = http.request.env["sale.order.line"].sudo().search([("id", "=", int(li_id))])
                            product = line_item[-1].product_id
                            temp = dict()
                            temp["transaction_type"] = "sale"
                            temp["product_id"] = product[0].id
                            temp["product_code"] = product[0].barcode if bool(product[0].barcode) else ""
                            temp["product_name"] = product[0].name
                            product_variant = http.request.env["product.product"].sudo().search(
                                [("id", "=", int(product[0].id))])
                            product_template = http.request.env["product.template"].sudo().search(
                                [("id", "=", int(product_variant[-1].product_tmpl_id))])
                            # temp["product_uom_id"] = product_template[-1].uom_id[0].id
                            temp["product_tracking"] = product_template[-1].tracking
                            temp["product_demand_quantity"] = line_item[-1].product_uom_qty
                            temp["product_delivered_quantity"] = line_item[-1].qty_delivered
                            temp["product_qty_to_deliver"] = line_item[-1].product_uom_qty - line_item[-1].qty_delivered
                            list_line_items.append(temp)
                        self.response_handler(list_line_items)
                    else:
                        self.response_handler("Error! Line items not found for the given sale order.")
                else:
                    self.response_handler("Error! Given sale order does not exist.")
            except Exception as e:
                self.response_handler(e.__str__())
        return self.response

    def check_availability(self, ls_id, qty):
        is_available = False
        available = http.request.env["stock.quant"].sudo().search(
            [("lot_id", "=", int(ls_id)), ("company_id", "=", int(self.company_id)), ("quantity", ">", 0)],
            order="create_date desc")
        if bool(available):
            if int(qty) <= available[-1].quantity:
                is_available = True
        return is_available

    @http.route(api_ver + "picking-by-sale-order", type="json", auth="none", methods=["POST"], csrf=False)
    def picking_by_sale_order(self, **params):
        if self.is_allowed(params):
            try:
                is_backorder = False
                so = http.request.env["sale.order"].sudo().search([("id", "=", int(params["inputs"]["so_id"]))])
                if bool(so):
                    order_line = so[-1].order_line
                    line_item_ids = list()
                    for line in order_line:
                        line_item_ids.append(line[0].id)
                    if bool(line_item_ids):
                        products_id = list()
                        products_qty_to_pick = list()
                        products_product_uom_id = list()
                        for li_id in line_item_ids:
                            line_item = http.request.env["sale.order.line"].sudo().search([("id", "=", int(li_id))])
                            product = line_item[-1].product_id
                            products_id.append(int(product[0].id))

                            product_variant = http.request.env["product.product"].sudo().search(
                                [("id", "=", int(product[0].id))])
                            product_template = http.request.env["product.template"].sudo().search(
                                [("id", "=", int(product_variant[-1].product_tmpl_id))])
                            products_product_uom_id.append(
                                {"product_id": str(product[0].id), "uom_id": product_template[-1].uom_id[0].id})
                            products_qty_to_pick.append({"product_id": str(product[0].id),
                                                         "qty_to_pick": line_item[-1].qty_to_deliver})

                        go = True
                        products_to_this_picking = list()
                        invalid_product_details = False
                        lot_name_not_exist = None
                        serial_name_not_exist = None
                        serials_id = list()
                        lots_id = list()
                        for l_item in params["inputs"]["line_items"]:
                            for key, val in l_item.items():
                                if key == "serials":
                                    for _l_i in val:
                                        if go:
                                            if "product_id" in _l_i and int(_l_i["product_id"]) in products_id:
                                                if int(_l_i["product_id"]) not in products_to_this_picking:
                                                    products_to_this_picking.append(int(_l_i["product_id"]))
                                                _check_ls_name = None
                                                if "serial_name" in _l_i and bool(_l_i["serial_name"]):
                                                    _check_ls_name = _l_i["serial_name"]
                                                if bool(_check_ls_name):
                                                    lot_serial = http.request.env["stock.production.lot"].sudo().search(
                                                        [("name", "=", _check_ls_name),
                                                         ("product_id", "=", int(_l_i["product_id"]))])
                                                    if not bool(lot_serial):
                                                        serial_name_not_exist = _check_ls_name
                                                        go = False
                                                    else:
                                                        ls_id = lot_serial[-1].id
                                                        is_available = self.check_availability(ls_id, 1)
                                                        if not bool(is_available):
                                                            go = False
                                                            self.response_handler(
                                                                "Error! Requested quantity for the serial(" + _check_ls_name + ") is currently not available.")
                                                        else:
                                                            serials_id.append({_check_ls_name: ls_id})
                                            else:
                                                invalid_product_details = True
                                                go = False
                                elif key == "lots":
                                    for _l_i in val:
                                        if go:
                                            if "product_id" in _l_i and int(_l_i["product_id"]) in products_id:
                                                if int(_l_i["product_id"]) not in products_to_this_picking:
                                                    products_to_this_picking.append(int(_l_i["product_id"]))
                                                _check_ls_name = None
                                                if "lot_name" in _l_i and bool(_l_i["lot_name"]):
                                                    _check_ls_name = _l_i["lot_name"]
                                                if bool(_check_ls_name):
                                                    lot_serial = http.request.env["stock.production.lot"].sudo().search(
                                                        [("name", "=", _check_ls_name),
                                                         ("product_id", "=", int(_l_i["product_id"]))])
                                                    if not bool(lot_serial):
                                                        lot_name_not_exist = _check_ls_name
                                                        go = False
                                                    else:
                                                        ls_id = lot_serial[-1].id
                                                        is_available = self.check_availability(ls_id, _l_i["qty_done"])
                                                        if not bool(is_available):
                                                            go = False
                                                            self.response_handler(
                                                                "Error! Requested quantity for the lot(" + _check_ls_name + ") is currently not available.")
                                                        else:
                                                            lots_id.append({_check_ls_name: ls_id})
                                            else:
                                                invalid_product_details = True
                                                go = False
                                else:
                                    for _l_i in val:
                                        if "product_id" not in _l_i or int(_l_i["product_id"]) not in products_id:
                                            if int(_l_i["product_id"]) not in products_to_this_picking:
                                                products_to_this_picking.append(int(_l_i["product_id"]))
                                            invalid_product_details = True
                                            go = False

                        if go:
                            if len(products_id) > len(products_to_this_picking):
                                is_backorder = True

                            view_stock_picking = so.action_view_delivery()
                            if bool(view_stock_picking) and bool(view_stock_picking["res_id"]):
                                stock_picking_id = int(view_stock_picking["res_id"])
                            else:
                                domain = view_stock_picking["domain"]
                                try:
                                    domain = ast.literal_eval(view_stock_picking["domain"])
                                except Exception as e:
                                    e.__str__()
                                    pass
                                stock_picking_id = int(domain[0][2][0])
                            stock_picking = http.request.env["stock.picking"].sudo().search(
                                [("id", "=", stock_picking_id)])

                            revised_line_items = list()
                            for l_item in params["inputs"]["line_items"]:
                                if go:
                                    for key, val in l_item.items():
                                        if key == "serials":
                                            line_item_product_id = None
                                            serials = list()
                                            for _l_i in val:
                                                line_item_product_id = int(_l_i["product_id"])

                                                product_uom_id = None
                                                for each in products_product_uom_id:
                                                    if int(each["product_id"]) == int(_l_i["product_id"]):
                                                        product_uom_id = each["uom_id"]
                                                if not bool(product_uom_id):
                                                    go = False
                                                    self.response_handler("Error! Invalid product uom id detected.")

                                                if go:
                                                    temp = dict()
                                                    for each in serials_id:
                                                        for _k, _v in each.items():
                                                            if _k == _l_i["serial_name"]:
                                                                temp["lot_id"] = int(_v)
                                                    temp["product_uom_id"] = int(product_uom_id)
                                                    temp["product_id"] = int(_l_i["product_id"])
                                                    temp["qty_done"] = int(_l_i["qty_done"])
                                                    temp["company_id"] = stock_picking[-1].company_id[0].id
                                                    temp["location_dest_id"] = stock_picking[-1].location_dest_id[0].id
                                                    temp["location_id"] = stock_picking[-1].location_id[0].id
                                                    temp["picking_id"] = stock_picking_id
                                                    temp["lot_name"] = False
                                                    temp["move_id"] = False
                                                    temp["owner_id"] = False
                                                    temp["package_id"] = False
                                                    temp["package_level_id"] = False
                                                    temp["result_package_id"] = False
                                                    serials.append(temp)

                                            if bool(serials):
                                                for each in products_qty_to_pick:
                                                    if int(each["product_id"]) == int(line_item_product_id):
                                                        if int(each["qty_to_pick"]) > len(serials):
                                                            is_backorder = True
                                                        if int(each["qty_to_pick"]) < len(serials):
                                                            go = False
                                                            self.response_handler(
                                                                "Error! Picking quantity of a serial-based product is bigger than the sale order quantity.")
                                                revised_line_items.append(serials)
                                        elif key == "lots":
                                            lots = list()
                                            total_done_qty = 0
                                            line_item_product_id = None
                                            for _l_i in val:
                                                line_item_product_id = int(_l_i["product_id"])

                                                product_uom_id = None
                                                for each in products_product_uom_id:
                                                    if int(each["product_id"]) == int(_l_i["product_id"]):
                                                        product_uom_id = each["uom_id"]
                                                if not bool(product_uom_id):
                                                    go = False
                                                    self.response_handler("Error! Invalid product uom id detected.")

                                                if go:
                                                    total_done_qty = total_done_qty + int(_l_i["qty_done"])
                                                    temp = dict()
                                                    for each in lots_id:
                                                        for _k, _v in each.items():
                                                            if _k == _l_i["lot_name"]:
                                                                temp["lot_id"] = int(_v)
                                                    temp["product_uom_id"] = int(product_uom_id)
                                                    temp["product_id"] = int(_l_i["product_id"])
                                                    temp["qty_done"] = int(_l_i["qty_done"])
                                                    temp["company_id"] = stock_picking[-1].company_id[0].id
                                                    temp["location_dest_id"] = stock_picking[-1].location_dest_id[0].id
                                                    temp["location_id"] = stock_picking[-1].location_id[0].id
                                                    temp["picking_id"] = stock_picking_id
                                                    temp["lot_name"] = False
                                                    temp["move_id"] = False
                                                    temp["owner_id"] = False
                                                    temp["package_id"] = False
                                                    temp["package_level_id"] = False
                                                    temp["result_package_id"] = False
                                                    lots.append(temp)
                                            if bool(lots):
                                                for each in products_qty_to_pick:
                                                    if int(each["product_id"]) == int(line_item_product_id):
                                                        if int(each["qty_to_pick"]) > total_done_qty:
                                                            is_backorder = True
                                                        if int(each["qty_to_pick"]) < total_done_qty:
                                                            go = False
                                                            self.response_handler(
                                                                "Error! Picking quantity of a lot-based product is bigger than the sale order quantity.")

                                                revised_line_items.append(lots)
                                        elif key == "normal":
                                            normal = list()
                                            for _l_i in val:
                                                line_item_product_id = int(_l_i["product_id"])

                                                product_uom_id = None
                                                for each in products_product_uom_id:
                                                    if int(each["product_id"]) == int(_l_i["product_id"]):
                                                        product_uom_id = each["uom_id"]
                                                if not bool(product_uom_id):
                                                    go = False
                                                    self.response_handler("Error! Invalid product uom id detected.")

                                                for each in products_qty_to_pick:
                                                    if int(each["product_id"]) == int(line_item_product_id):
                                                        if int(each["qty_to_pick"]) > int(_l_i["qty_done"]):
                                                            is_backorder = True
                                                        if int(each["qty_to_pick"]) < int(_l_i["qty_done"]):
                                                            go = False
                                                            self.response_handler(
                                                                "Error! Picking quantity of a product is bigger than the sale order quantity.")
                                                if go:
                                                    temp = dict()
                                                    temp["product_uom_id"] = int(product_uom_id)
                                                    temp["product_id"] = int(_l_i["product_id"])
                                                    temp["qty_done"] = int(_l_i["qty_done"])
                                                    temp["company_id"] = stock_picking[-1].company_id[0].id
                                                    temp["location_dest_id"] = stock_picking[-1].location_dest_id[0].id
                                                    temp["location_id"] = stock_picking[-1].location_id[0].id
                                                    temp["picking_id"] = stock_picking_id
                                                    temp["lot_name"] = False
                                                    temp["lot_id"] = False
                                                    temp["move_id"] = False
                                                    temp["owner_id"] = False
                                                    temp["package_id"] = False
                                                    temp["package_level_id"] = False
                                                    temp["result_package_id"] = False
                                                    normal.append(temp)
                                            if bool(normal):
                                                revised_line_items.append(normal)
                            if go:
                                go = False
                                for revised_line in revised_line_items:
                                    stock_to_be_moved = list()
                                    for i in range(len(stock_picking[-1].move_ids_without_package)):
                                        stock_move = http.request.env["stock.move"].sudo().search(
                                            [("id", "=", stock_picking[-1].move_ids_without_package[i].id)])
                                        if bool(stock_move):
                                            for line in revised_line:
                                                if int(line["product_id"]) == int(stock_move[-1].product_id[0].id):
                                                    # target_product_name = stock_move[-1].product_id[0].name
                                                    qty_to_pick = 0
                                                    for _line in revised_line:
                                                        if int(_line["product_id"]) == int(line["product_id"]):
                                                            qty_to_pick = qty_to_pick + int(_line["qty_done"])
                                                    if qty_to_pick > 0:
                                                        if int(stock_move[-1].product_qty) - int(
                                                                stock_move[-1].quantity_done) >= qty_to_pick:
                                                            if line["product_id"] not in stock_to_be_moved:
                                                                stock_to_be_moved.append(line["product_id"])
                                                                stock_move.sudo().write(
                                                                    {"move_line_ids": [(0, False, line) for line in
                                                                                       revised_line]})
                                                                go = True
                                if go:
                                    try:
                                        stock_picking.action_assign()
                                        #
                                        stock_picking.button_validate()
                                        if is_backorder:
                                            data = dict()
                                            data["backorder_confirmation_line_ids"] = [
                                                (0, False, {"picking_id": stock_picking_id, "to_backorder": True})]
                                            data["pick_ids"] = [(6, False, [stock_picking_id])]
                                            data["show_transfers"] = False
                                            backorder = http.request.env["stock.backorder.confirmation"].sudo().create(
                                                data)
                                            backorder.with_context(
                                                button_validate_picking_ids=backorder.pick_ids.ids).process()
                                        self.response_handler()
                                    except Exception as e:
                                        self.response_handler(e.__str__())
                                else:
                                    self.response_handler("An unknown error occurred to pick!")
                        else:
                            if bool(lot_name_not_exist):
                                self.response_handler("Error! Lot number(" + lot_name_not_exist + ") does not exist.")
                            elif bool(serial_name_not_exist):
                                self.response_handler(
                                    "Error! Serial number(" + serial_name_not_exist + ") does not exist.")
                            elif bool(invalid_product_details):
                                self.response_handler("Error! Invalid product details supplied.")
                    else:
                        self.response_handler("Error! Line items not found for the given sale order.")
                else:
                    self.response_handler("Error! Given sale order does not exist.")
            except Exception as e:
                self.response_handler(e.__str__())
        return self.response

    @staticmethod
    def get_country_code(country):
        code = None
        _country = http.request.env["res.country"].sudo().search([("name", "=", country)])
        if bool(_country):
            code = _country[-1].code
        return code

    @http.route(api_ver + "get-purchase-order-location-n-vendor-addresses", type="json", auth="none", methods=["POST"],
                csrf=False)
    def get_purchase_order_location_n_vendor_addresses(self, **params):
        if self.is_allowed(params):
            try:
                po = http.request.env["purchase.order"].sudo().search([("id", "=", int(params["inputs"]["po_id"]))])
                if bool(po):
                    res = dict()
                    location_id = po[-1].picking_type_id[0].warehouse_id[0].id
                    # location_id = po[-1].company_id[0].id
                    warehouse = http.request.env["stock.warehouse"].sudo().search([("id", "=", int(location_id))])
                    temp = dict()
                    temp["partner_id"] = warehouse[-1].partner_id.id
                    temp["partner_name"] = warehouse[-1].partner_id.name
                    temp["testing"] = "okay555!!!"
                    self.response_handler(temp)
                    return self.response

                    location = http.request.env["res.partner"].sudo().search([("id", "=", int(warehouse[-1].partner_id))])
                    temp = dict()
                    temp["name"] = location[-1].name
                    temp["line1"] = location[-1].street
                    temp["line2"] = location[-1].street2
                    temp["line3"] = ""
                    temp["line4"] = ""
                    temp["city"] = location[-1].city
                    temp["state"] = location[-1].state_id[0].name
                    temp["zip"] = location[-1].zip
                    temp["country"] = location[-1].country_id[0].name
                    temp["country_code"] = self.get_country_code(location[-1].country_id[0].name)
                    res["location_address"] = temp
                    res["location_id"] = location_id

                    vendor_id = po[-1].partner_id[0].id
                    vendor = http.request.env["res.partner"].sudo().search([("id", "=", int(vendor_id))])
                    temp = dict()
                    temp["name"] = vendor[-1].name
                    temp["line1"] = vendor[-1].street
                    temp["line2"] = vendor[-1].street2
                    temp["line3"] = ""
                    temp["line4"] = ""
                    temp["city"] = vendor[-1].city
                    temp["state"] = vendor[-1].state_id[0].name
                    temp["zip"] = vendor[-1].zip
                    temp["country"] = vendor[-1].country_id[0].name
                    temp["country_code"] = self.get_country_code(vendor[-1].country_id[0].name)
                    res["vendor_address"] = temp
                    res["vendor_id"] = vendor_id
                    self.response_handler(res)
                else:
                    self.response_handler("Error! Purchase order not found.")
            except Exception as e:
                self.response_handler(e.__str__())
        return self.response

    @http.route(api_ver + "get-sale-order-location-n-customer-addresses", type="json", auth="none", methods=["POST"],
                csrf=False)
    def get_sale_order_location_n_customer_addresses(self, **params):
        if self.is_allowed(params):
            try:
                so = http.request.env["sale.order"].sudo().search([("id", "=", int(params["inputs"]["so_id"]))])
                if bool(so):
                    res = dict()
                    location_id = so[-1].warehouse_id[0].id
                    warehouse = http.request.env["stock.warehouse"].sudo().search([("id", "=", int(location_id))])
                    location = http.request.env["res.partner"].sudo().search(
                        [("id", "=", int(warehouse[-1].partner_id))])
                    temp = dict()
                    temp["name"] = location[-1].name
                    temp["line1"] = location[-1].street
                    temp["city"] = location[-1].city
                    temp["state"] = location[-1].state_id[0].name
                    temp["zip"] = location[-1].zip
                    temp["country"] = location[-1].country_id[0].name
                    temp["country_code"] = self.get_country_code(location[-1].country_id[0].name)
                    res["location_address"] = temp
                    res["location_id"] = location_id

                    customer_id = so[-1].partner_id[0].id
                    customer = http.request.env["res.partner"].sudo().search([("id", "=", int(customer_id))])
                    temp = dict()
                    temp["name"] = customer[-1].name
                    temp["line1"] = customer[-1].street
                    temp["city"] = customer[-1].city
                    temp["state"] = customer[-1].state_id[0].name
                    temp["zip"] = customer[-1].zip
                    temp["country"] = customer[-1].country_id[0].name
                    temp["country_code"] = self.get_country_code(customer[-1].country_id[0].name)
                    res["customer_address"] = temp
                    res["customer_id"] = customer_id
                    self.response_handler(res)
                else:
                    self.response_handler("Error! Sale order not found.")
            except Exception as e:
                self.response_handler(e.__str__())
        return self.response

    @http.route(api_ver + "check-if-partner-exists", type="json", auth="none", methods=["POST"],
                csrf=False)
    def check_if_partner_exists(self, **params):
        if self.is_allowed(params):
            try:
                _conds = list()
                _conds.append(("name", "=", params["inputs"]["name"]))
                partner = http.request.env["res.partner"].sudo().search(_conds)
                if bool(partner):
                    res = dict()
                    res["partner_id"] = partner[-1].id
                    self.response_handler(res)
                else:
                    self.response_handler("Error! No such partner exists.")
            except Exception as e:
                self.response_handler(e.__str__())
        return self.response

    @http.route(api_ver + "check-if-location-exists", type="json", auth="none", methods=["POST"],
                csrf=False)
    def check_if_location_exists(self, **params):
        if self.is_allowed(params):
            try:
                _conds = list()
                _conds.append(("name", "=", params["inputs"]["name"]))
                partner = http.request.env["res.partner"].sudo().search(_conds)
                warehouse = http.request.env["stock.warehouse"].sudo().search([("partner_id", "=", int(partner[-1].id))])
                if bool(warehouse):
                    res = dict()
                    res["location_id"] = warehouse[-1].id
                    self.response_handler(res)
                else:
                    self.response_handler("Error! No such location exists.")
            except Exception as e:
                self.response_handler(e.__str__())
        return self.response

    @http.route(api_ver + "check-warehouse-code", type="json", auth="none", methods=["POST"],
                csrf=False)
    def check_warehouse_code(self, **params):
        if self.is_allowed(params):
            _conds = list()
            _conds.append(("code", "=", params["inputs"]["code"]))
            code = http.request.env["stock.warehouse"].sudo().search(_conds)
            if bool(code):
                self.response_handler("Error! Code already exists.")
            else:
                res = dict()
                res["code"] = params["inputs"]["code"]
                self.response_handler(res)
        return self.response

    @http.route(api_ver + "check-if-po-exists", type="json", auth="none", methods=["POST"],
                csrf=False)
    def check_if_po_exists(self, **params):
        if self.is_allowed(params):
            po = http.request.env["purchase.order"].sudo().search([("name", "=", params["inputs"]["name"])])
            if bool(po):
                res = dict()
                res["id"] = po[-1].id
                self.response_handler(res)
            else:
                self.response_handler("Error! Purchase order does not exist.")
        return self.response

    @http.route(api_ver + "check-if-so-exists", type="json", auth="none", methods=["POST"],
                csrf=False)
    def check_if_so_exists(self, **params):
        if self.is_allowed(params):
            so = http.request.env["sale.order"].sudo().search([("name", "=", params["inputs"]["name"])])
            if bool(so):
                res = dict()
                res["id"] = so[-1].id
                self.response_handler(res)
            else:
                self.response_handler("Error! Sale order does not exist.")
        return self.response

    @http.route(api_ver + "check-if-product-exists", type="json", auth="none", methods=["POST"],
                csrf=False)
    def check_if_product_exists(self, **params):
        if self.is_allowed(params):
            product = http.request.env["product.product"].sudo().search(
                [("barcode", "=", params["inputs"]["product_code"])])
            if bool(product):
                res = dict()
                res["product_id"] = product[-1].id
                res["product_tracking"] = product[-1].tracking
                self.response_handler(res)
            else:
                self.response_handler("Error! Product does not exist.")
        return self.response
