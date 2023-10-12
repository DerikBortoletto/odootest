# -*- coding: utf-8 -*-
import json
import datetime
from odoo import http
from .locations import Locations
from .products import Products
from .inbounds import Inbounds
from .outbounds import Outbounds


class Inventories(http.Controller):
    def __init__(self, *, company_id=None, user_id=None) -> None:
        self.company_id = company_id
        self.user_id = user_id
        self.request = http.request
        self.is_inventory_audit = False
        self.is_no_tracking = False
        pass
    
    def get_allocation(self, product_id, location_id=None, lot_id=None):
        allocated_qty = 0
        if bool(lot_id):
            if self.get_tracking(product_id, lot_id) == "serial":
                return allocated_qty

        _tuple_list = list()
        query = """SELECT * FROM stock_move_line WHERE company_id = %d AND product_id = %d"""
        _tuple_list.append(int(self.company_id))
        _tuple_list.append(int(product_id))
        if bool(location_id):
            query += """ AND location_id = %d"""
            _tuple_list.append(int(location_id))
        if bool(lot_id):
            query += """ AND lot_id = %d"""
            _tuple_list.append(int(lot_id))
        else:
            if self.is_inventory_audit or self.is_no_tracking:
                query += """ AND lot_id IS NULL"""
        query = query % tuple(_tuple_list)
        self.request.env.cr.execute(query)
        records = self.request.env.cr.dictfetchall()
        stock_move_ids = list()
        for each in records:
            stock_move_ids.append(str(each["move_id"]))
        if bool(stock_move_ids):
            move_ids = "'" + "', '".join(stock_move_ids) + "'"
            query = """SELECT * FROM stock_move WHERE id IN ({}) AND sale_line_id IS NOT NULL""".format(move_ids)
            self.request.env.cr.execute(query)
            records = self.request.env.cr.dictfetchall()
            sale_line_ids = list()
            for each in records:
                sale_line_ids.append(str(each["sale_line_id"]))
            if bool(sale_line_ids):
                so_line_ids = "'" + "', '".join(sale_line_ids) + "'"
                state = "'" + "', '".join(["cancel"]) + "'"
                query = """SELECT SOL.* FROM sale_order_line AS SOL INNER JOIN sale_order AS SO ON SOL.order_id = SO.id WHERE SOL.id IN (%s) AND SO.state NOT IN (%s)""" % (so_line_ids, state)
                self.request.env.cr.execute(query)
                records = self.request.env.cr.dictfetchall()
                for each in records:
                    allocated_qty += float(each["product_uom_qty"]) - float(each["qty_delivered"])
        return float(allocated_qty)

    def get_quarantine(self, product_id, location_id=None, lot_id=None):
        quarantine = 0
        _tuple_list = list()
        query = """SELECT * FROM stock_location WHERE company_id = %d AND (scrap_location = 't' OR return_location = 't')"""
        _tuple_list.append(int(self.company_id))
        if bool(location_id):
            query += """ AND id = %d"""
            _tuple_list.append(int(location_id))

        query = query % tuple(_tuple_list)
        self.request.env.cr.execute(query)
        records = self.request.env.cr.dictfetchall()
        if bool(records):
            quarantine_location_ids = list()
            for each in records:
                quarantine_location_ids.append(str(each["id"]))
            if bool(quarantine_location_ids):
                _ql_ids = "'" + "', '".join(quarantine_location_ids) + "'"
                query = """SELECT * FROM stock_quant WHERE company_id = %d AND product_id = %d AND location_id IN (%s) AND lot_id IS NULL GROUP BY id, lot_id, product_id, location_id""" % (int(self.company_id), int(product_id), _ql_ids)
                if bool(lot_id):
                    query = """SELECT * FROM stock_quant WHERE company_id = %d AND product_id = %d AND location_id IN (%s) AND lot_id = %d GROUP BY id, lot_id, product_id, location_id""" % (int(self.company_id), int(product_id), _ql_ids, int(lot_id))
                self.request.env.cr.execute(query)
                _records = self.request.env.cr.dictfetchall()
                for each in _records:
                    quarantine += float(each["quantity"])
        return float(quarantine)

    def get_lot_n_expiry(self, product_id, *, lot_id=None, lot_name=None):
        if bool(lot_id):
            lot_name = None
            expiry_date = None
            if lot_id != "x":
                query = """SELECT name, expiration_date FROM stock_production_lot WHERE id = %d AND company_id = %d AND product_id = %d""" % (int(lot_id), int(self.company_id), int(product_id))
                self.request.env.cr.execute(query)
                records = self.request.env.cr.dictfetchall()
                for _row in records:
                    lot_name = _row["name"]
                    expiry_date = _row["expiration_date"].strftime('%Y-%m-%d') if bool(_row["expiration_date"]) and isinstance(_row["expiration_date"], datetime.datetime) else ""
            return lot_name, expiry_date
        if bool(lot_name):
            lot_id = None
            query = """SELECT id FROM stock_production_lot WHERE company_id = %d AND product_id = %d AND name = '%s'""" % (int(self.company_id), int(product_id), lot_name)
            self.request.env.cr.execute(query)
            records = self.request.env.cr.dictfetchall()
            for _row in records:
                lot_id = _row["id"]
            return lot_id

    def get_to_receive(self, location_ids, product_id, lot_id=None):
        _qty_to_receive = 0
        _tuple_list = list()
        query = """SELECT SUM(SML.product_qty) AS product_qty, SUM(SML.qty_done) AS qty_done, SML.product_id FROM stock_move_line AS SML INNER JOIN stock_move AS SM ON SML.move_id = SM.id WHERE SML.company_id = %d AND SML.product_id = %d AND SM.purchase_line_id::BOOLEAN = TRUE"""
        _tuple_list.append(int(self.company_id))
        _tuple_list.append(int(product_id))
        if bool(location_ids):
            _l_ids = "'" + "', '".join(location_ids) + "'"
            query += """ AND SML.location_dest_id IN (%s)"""
            _tuple_list.append(_l_ids)
        if bool(lot_id):
            query += """ AND SML.lot_id = %d"""
            _tuple_list.append(int(lot_id))
            query += """ GROUP BY SML.product_id, SML.lot_id"""
        else:
            if self.is_inventory_audit or self.is_no_tracking:
                query += """ AND SML.lot_id IS NULL"""
            query += """ GROUP BY SML.product_id"""

        query = query % tuple(_tuple_list)
        self.request.env.cr.execute(query)
        records = self.request.env.cr.dictfetchall()
        for each in records:
            _qty_to_receive = float(each["product_qty"])
        return _qty_to_receive

    def get_stock(self, location_ids, product_id, lot_id=None):
        in_stock = 0
        available = 0
        _tuple_list = list()
        query = """SELECT SUM(quantity) AS quantity, SUM(reserved_quantity) AS reserved_quantity FROM stock_quant WHERE company_id = %d AND product_id = %d"""
        _tuple_list.append(int(self.company_id))
        _tuple_list.append(int(product_id))
        if bool(location_ids):
            query += """ AND location_id IN (%s)"""
            _loc_ids = "'" + "', '".join(location_ids) + "'"
            _tuple_list.append(_loc_ids)
        if bool(lot_id):
            query += """ AND lot_id = %d GROUP BY product_id, lot_id"""
            _tuple_list.append(int(lot_id))
        else:
            if self.is_inventory_audit or self.is_no_tracking:
                query += """ AND lot_id IS NULL"""
            query += """ GROUP BY product_id"""
        query = query % tuple(_tuple_list)
        self.request.env.cr.execute(query)
        records = self.request.env.cr.dictfetchall()
        if bool(records):
            for each in records:
                allocated = self.get_allocation(product_id, None, lot_id)
                quarantine = self.get_quarantine(product_id, None, lot_id)
                in_stock = float(each["quantity"])
                available = float(in_stock - float(each["reserved_quantity"]))
                to_receive = self.get_to_receive(location_ids, product_id, lot_id)
                return int(in_stock), int(available), int(allocated), int(quarantine), int(to_receive)
        else:
            allocated = self.get_allocation(product_id, None, lot_id)
            quarantine = self.get_quarantine(product_id, None, lot_id)
            to_receive = self.get_to_receive(location_ids, product_id, lot_id)
            return int(in_stock), int(available), int(allocated), int(quarantine), int(to_receive)

    def get_stock_x(self, location_ids, p_name):
        _not_exist = 1
        in_stock = 0
        available = 0
        allocated = 0
        quarantine = 0
        to_be_received = 0

        products = Products(company_id=self.company_id, user_id=self.user_id)
        product_id = products.get_product_name_id(p_name=p_name)
        if bool(product_id):
            _not_exist = 0
            allocated = self.get_allocation(product_id)
            quarantine = self.get_quarantine(product_id)

            query = """SELECT SUM(SML.product_qty) AS product_qty, SUM(SML.qty_done) AS qty_done FROM stock_move_line AS SML INNER JOIN stock_move AS SM ON SML.move_id = SM.id WHERE SML.company_id = %d AND SML.product_id = %d AND SM.purchase_line_id IS NOT NULL GROUP BY SML.location_dest_id""" % (int(self.company_id), int(product_id))
            if bool(location_ids):
                _l_ids = "'" + "', '".join(location_ids) + "'"
                query = """SELECT SUM(SML.product_qty) AS product_qty, SUM(SML.qty_done) AS qty_done FROM stock_move_line AS SML INNER JOIN stock_move AS SM ON SML.move_id = SM.id WHERE SML.company_id = %d AND SML.product_id = %d AND SML.location_dest_id IN (%s) AND SM.purchase_line_id IS NOT NULL GROUP BY SML.location_dest_id""" % (int(self.company_id), int(product_id), _l_ids)
            self.request.env.cr.execute(query)
            records = self.request.env.cr.dictfetchall()
            for each in records:
                to_be_received += float(each["product_qty"])
        return bool(_not_exist), int(in_stock), int(available), int(allocated), int(quarantine), int(to_be_received)

    def get_item_wise_inventory(self, inputs):
        products = Products(company_id=self.company_id, user_id=self.user_id)
        product_codes = list()
        product_names = list()
        product_ids = list()
        if "products" in inputs and bool(inputs["products"]):
            _products = json.loads(inputs["products"])
            for each in _products:
                for key, val in each.items():
                    product_codes.append(key)
                    product_names.append(val)
            data = self.request.env["product.product"].sudo().search([("name", "in", product_names)])
            for each in data:
                if each.id not in product_ids:
                    product_ids.append(str(each.id))

        location_ids = list()
        if "location_name" in inputs and bool(inputs["location_name"]):
            locations = Locations(company_id=self.company_id, user_id=self.user_id)
            location_ids = locations.get_location_ids_including_all_child_locations(location_name=inputs["location_name"])

        _items = list()
        if bool(product_ids):
            query = """SELECT PP.id AS product_id FROM product_product AS PP WHERE PP.id IN ({})""".format("'" + "', '".join(product_ids) + "'")
            self.request.env.cr.execute(query)
            records = self.request.env.cr.dictfetchall()
            if bool(records):
                _tmp_items = list()
                for each in records:
                    _tmp = dict()
                    _tmp["erp"] = "Odoo"
                    _tmp["not_exist"] = False
                    (_tmp["product_code"], _tmp["product_name"]) = products.get_barcode(each["product_id"])
                    (_tmp["in_stock"], _tmp["available"], _tmp["allocated"], _tmp["quarantined"], _tmp["to_receive"]) = self.get_stock(location_ids, each["product_id"])
                    _tmp_items.append(_tmp)
                if len(_tmp_items) > 0:
                    i = -1
                    for p_name in product_names:
                        i += 1
                        is_not_found = True
                        for _item in _tmp_items:
                            if p_name == _item["product_name"]:
                                is_not_found = False
                        if is_not_found:
                            _tmp = dict()
                            _tmp["erp"] = "Odoo"
                            _tmp["product_code"] = None if product_codes[i] == "None" else product_codes[i]
                            _tmp["product_name"] = p_name
                            (_tmp["not_exist"], _tmp["in_stock"], _tmp["available"], _tmp["allocated"], _tmp["quarantined"], _tmp["to_receive"]) = self.get_stock_x(location_ids, p_name)
                            _items.append(_tmp)
                        else:
                            for _item in _tmp_items:
                                if p_name == _item["product_name"]:
                                    _items.append(_item)
        return _items

    def get_lot_stock(self, location_ids, product_id, lot_id):
        in_stock = 0
        available = 0
        _tuple_list = list()
        query = """SELECT SUM(quantity) AS quantity, SUM(reserved_quantity) AS reserved_quantity FROM stock_quant WHERE lot_id IS NOT NULL AND company_id = %d AND product_id = %d"""
        _tuple_list.append(int(self.company_id))
        _tuple_list.append(int(product_id))
        if bool(location_ids):
            query += """ AND location_id IN (%s)"""
            _loc_ids = "'" + "', '".join(location_ids) + "'"
            _tuple_list.append(_loc_ids)
        if bool(lot_id):
            query += """ AND lot_id = %d GROUP BY product_id, lot_id"""
            _tuple_list.append(int(lot_id))
        query = query % tuple(_tuple_list)
        self.request.env.cr.execute(query)
        records = self.request.env.cr.dictfetchall()
        if bool(records):
            for each in records:
                allocated = self.get_allocation(product_id, None, lot_id)
                quarantine = self.get_quarantine(product_id, None, lot_id)
                in_stock = float(each["quantity"])
                available = float(in_stock - float(each["reserved_quantity"]))
                to_receive = self.get_to_receive(location_ids, product_id, lot_id)
                return int(in_stock), int(available), int(allocated), int(quarantine), int(to_receive)
        else:
            allocated = self.get_allocation(product_id, None, lot_id)
            quarantine = self.get_quarantine(product_id, None, lot_id)
            to_receive = self.get_to_receive(location_ids, product_id, lot_id)
            return int(in_stock), int(available), int(allocated), int(quarantine), int(to_receive)

    def get_item_inventory_by_lots(self, inputs):
        products = Products(company_id=self.company_id, user_id=self.user_id)
        product_id = products.get_product_name_id(p_code=inputs["product_code"])
        product_name = products.get_product_name_id(p_id=product_id)

        limit = 1000
        offset = inputs["offset"]

        location_ids = list()
        if "location_name" in inputs:
            locations = Locations(company_id=self.company_id, user_id=self.user_id)
            location_ids = locations.get_location_ids_including_all_child_locations(location_name=inputs["location_name"])
        lot_id = None
        if "lot_name" in inputs:
            lot_id = self.get_lot_n_expiry(product_id, lot_name=inputs["lot_name"])
            if not bool(lot_id):
                raise Exception("The lot (" + inputs["lot_name"] + ") does not exist or it got expired in Odoo!")

        _tuple_list = list()
        query = """SELECT PP.id AS product_id, SPL.id AS lot_id FROM product_product AS PP LEFT JOIN stock_production_lot AS SPL ON PP.id = SPL.product_id WHERE PP.id = %d AND SPL.company_id = %d AND SPL.id IN (SELECT lot_id FROM stock_move_line WHERE qty_done > 0 AND company_id = %d AND product_id = %d AND lot_id IS NOT NULL GROUP BY id HAVING MAX(qty_done) > 1)"""
        _tuple_list.append(int(product_id))
        _tuple_list.append(int(self.company_id))
        _tuple_list.append(int(self.company_id))
        _tuple_list.append(int(product_id))
        if bool(lot_id):
            query += """ AND SPL.id = %d"""
            _tuple_list.append(int(lot_id))
        query += """ GROUP BY PP.id, SPL.id ORDER BY PP.id DESC LIMIT %d OFFSET %d"""
        _tuple_list.append(int(limit))
        _tuple_list.append(int(offset))

        query = query % tuple(_tuple_list)
        self.request.env.cr.execute(query)
        records = self.request.env.cr.dictfetchall()
        _records = list()
        for each in records:
            _tmp = dict()
            _tmp["erp"] = "Odoo"
            _tmp["product_name"] = product_name
            (_tmp["lot_name"], _tmp["expiry_date"]) = self.get_lot_n_expiry(each["product_id"], lot_id=each["lot_id"])
            (_tmp["in_stock"], _tmp["available"], _tmp["allocated"], _tmp["quarantined"], _tmp["to_receive"]) = self.get_lot_stock(location_ids, each["product_id"], each["lot_id"])
            _records.append(_tmp)
        return _records

    def get_location_stock(self, location_ids, product_id, limit, offset):
        products = Products(company_id=self.company_id, user_id=self.user_id)
        locations = Locations(company_id=self.company_id, user_id=self.user_id)

        _tuple_list = list()
        query = """SELECT SUM(quantity) AS quantity, SUM(reserved_quantity) AS reserved_quantity, product_id, location_id FROM stock_quant WHERE company_id = %d AND product_id = %d"""
        _tuple_list.append(int(self.company_id))
        _tuple_list.append(int(product_id))
        if bool(location_ids):
            query += """ AND location_id IN (%s)"""
            _loc_ids = "'" + "', '".join(location_ids) + "'"
            _tuple_list.append(_loc_ids)
        query += """ GROUP BY product_id, location_id LIMIT %d OFFSET %d"""
        _tuple_list.append(int(limit))
        _tuple_list.append(int(offset))
        query = query % tuple(_tuple_list)
        self.request.env.cr.execute(query)
        records = self.request.env.cr.dictfetchall()
        _records = list()
        if bool(records):
            for each in records:
                allocated = self.get_allocation(each["product_id"], each["location_id"])
                quarantine = self.get_quarantine(each["product_id"], each["location_id"])
                in_stock = float(each["quantity"])
                available = float(in_stock - float(each["reserved_quantity"]))
                to_receive = self.get_to_receive(location_ids, each["product_id"])
                _tmp = dict()
                _tmp["erp"] = "Odoo"
                _tmp["product_name"] = products.get_product_name_id(p_id=each["product_id"])
                _tmp["storage_location"] = locations.get_storage_location(each["location_id"])
                _tmp["in_stock"] = int(in_stock)
                _tmp["available"] = int(available)
                _tmp["allocated"] = int(allocated)
                _tmp["quarantined"] = int(quarantine)
                _tmp["to_receive"] = int(to_receive)
                _records.append(_tmp)
        return _records

    def get_item_inventory_by_locations(self, inputs):
        limit = inputs["limit"]
        offset = inputs["offset"]

        products = Products(company_id=self.company_id, user_id=self.user_id)
        product_id = products.get_product_name_id(p_code=inputs["product_code"])

        location_ids = list()
        if "location_name" in inputs:
            locations = Locations(company_id=self.company_id, user_id=self.user_id)
            location_ids = locations.get_location_ids_including_all_child_locations(location_name=inputs["location_name"])
        return self.get_location_stock(location_ids, product_id, limit, offset)

    def get_tracking(self, product_id, lot_id):
        _tracking = None
        if bool(lot_id):
            query = """SELECT * FROM stock_move_line WHERE qty_done > 0 AND company_id = %d AND product_id = %d AND lot_id = %d GROUP BY id HAVING MAX(qty_done) > 1 LIMIT 1""" % (int(self.company_id), int(product_id), int(lot_id))
            self.request.env.cr.execute(query)
            records = self.request.env.cr.dictfetchall()
            if len(records) > 0:
                _tracking = "lot"
            else:
                _tracking = "serial"
        return _tracking
    
    def list_suggestive_lots(self, inputs):
        _res = list()
        product = http.request.env["product.product"].sudo().search([("barcode", "=", inputs["product_code"])])
        if bool(product):
            locations = Locations(company_id=self.company_id, user_id=self.user_id)
            internal_ids = locations.get_all_internal_location_ids()
            _internal_loc_ids = "'" + "', '".join(internal_ids) + "'"
            query = """SELECT * FROM stock_quant WHERE quantity > 0 AND location_id IN (%s) AND product_id = %d AND lot_id IS NOT NULL GROUP BY id, lot_id ORDER BY id DESC""" % (_internal_loc_ids, int(product[-1].id))
            self.request.env.cr.execute(query)
            records = self.request.env.cr.dictfetchall()
            for _row in records:
                if self.get_tracking(product[-1].id, _row["lot_id"]) == "lot":
                    _tmp = dict()
                    _tmp["product_code"] = inputs["product_code"]
                    _tmp["available_quantity"] = float(_row["quantity"])
                    (_tmp["lot_name"], _tmp["expiry_date"]) = self.get_lot_n_expiry(product[-1].id, lot_id=_row["lot_id"])
                    _res.append(_tmp)
        return _res

    def list_all_lots(self, inputs):
        _res = list()
        products = Products(company_id=self.company_id, user_id=self.user_id)
        _product_codes = "'" + "', '".join(inputs["product_codes"]) + "'"

        locations = Locations(company_id=self.company_id, user_id=self.user_id)
        location_ids = locations.get_location_ids_including_all_child_locations(location_name=inputs["location_name"])
        _location_ids = "'" + "', '".join(location_ids) + "'"

        _limit = int(inputs["limit"])
        _offset = 0
        if "page" in inputs and int(inputs["page"]) > 0:
            _offset = (int(inputs["page"]) - 1) * _limit

        _tuple_list = list()
        query = """SELECT SML.product_id, SML.lot_name, PP.barcode FROM stock_move_line AS SML LEFT JOIN product_product AS PP ON SML.product_id = PP.id WHERE SML.qty_done > 0 AND SML.company_id = %d AND SML.location_dest_id IN (%s) AND PP.barcode IN (%s) AND SML.lot_id IS NOT NULL GROUP BY SML.id, SML.lot_id, PP.barcode HAVING MAX(SML.qty_done) > 1 LIMIT %d OFFSET %d"""
        _tuple_list.append(int(self.company_id))
        _tuple_list.append(_location_ids)
        _tuple_list.append(_product_codes)
        _tuple_list.append(int(_limit))
        _tuple_list.append(int(_offset))
        query = query % tuple(_tuple_list)
        self.request.env.cr.execute(query)
        records = self.request.env.cr.dictfetchall()
        for _row in records:
                _tmp = dict()
                _tmp["product_code"] = _row["barcode"]
                _tmp["product_name"] = products.get_product_name_id(p_id=_row["product_id"])
                _tmp["lot_name"] = _row["lot_name"]
                _res.append(_tmp)
        return _res

    def handle_inventory_audit_session(self, inputs):
        _session = inputs["session"]
        if bool(_session):
            _model_names = ["Purchase Order", "Sales Order", "Inventory", "Product Moves (Stock Move Line)", "Quants"]
            _model_names_str = "'" + "', '".join(_model_names) + "'"
            _models = list()
            query = """SELECT * FROM ir_model WHERE name IN ({})""".format(_model_names_str)
            self.request.env.cr.execute(query)
            records = self.request.env.cr.dictfetchall()
            for rec in records:
                _models.append(rec)
            if bool(_models):
                if _session == "start":
                    _exception_found = False
                    for _m in _models:
                        if not bool(_exception_found):
                            rule_exists = self.request.env["ir.rule"].sudo().search([("name", "like", "Middleware Inventory Audit"), ("model_id", "=", int(_m["id"]))])
                            if bool(rule_exists):
                                rule_exists.write({"groups": [(6, False, [])], "domain_force": "[(0, '=', 1)]", "active": True, "perm_read": False, "perm_create": True, "perm_write": True, "perm_unlink": True})
                            else:
                                _rule_name = None
                                if _m["name"] == "Purchase Order":
                                    _rule_name = "Middleware Inventory Audit - Purchase Order"
                                elif _m["name"] == "Sales Order":
                                    _rule_name = "Middleware Inventory Audit - Sales Order"
                                elif _m["name"] == "Inventory":
                                    _rule_name = "Middleware Inventory Audit - Inventory"
                                elif _m["name"] == "Product Moves (Stock Move Line)":
                                    _rule_name = "Middleware Inventory Audit - Product Moves"
                                elif _m["name"] == "Quants":
                                    _rule_name = "Middleware Inventory Audit - Quants"
                                if not bool(_rule_name):
                                    _exception_found = True
                                else:
                                    payload = dict()
                                    payload["name"] = _rule_name
                                    payload["model_id"] = int(_m["id"])
                                    payload["groups"] = [(6, False, [])]
                                    payload["domain_force"] = "[(0, '=', 1)]"
                                    payload["perm_read"] = False
                                    payload["perm_create"] = True
                                    payload["perm_write"] = True
                                    payload["perm_unlink"] = True
                                    payload["active"] = True
                                    rule_created = self.request.env["ir.rule"].sudo().create(payload)
                                    if not bool(rule_created):
                                        _exception_found = True
                    if _exception_found:
                        for _model in _models:
                            rule_exists = self.request.env["ir.rule"].sudo().search([("name", "like", "Middleware Inventory Audit"), ("model_id", "=", int(_model["id"]))])
                            if bool(rule_exists):
                                rule_exists.unlink()
                        raise Exception("Unable to start the inventory audit session!")
                elif _session == "end":
                    c = 0
                    for _model in _models:
                        rule_exists = self.request.env["ir.rule"].sudo().search([("name", "like", "Middleware Inventory Audit"), ("model_id", "=", int(_model["id"]))])
                        if bool(rule_exists):
                            rule_exists.unlink()
                            c += 1
                    if c > 0 and c != len(_models):
                        # raise Exception("Unable to end the inventory audit session!")
                        pass

    @staticmethod
    def get_physical_qty(inputs, barcode, lot=None):
        physical_qty = 0
        for _item in inputs["items"]:
            if str(_item["product_code"]) == str(barcode):
                if bool(lot):
                    for _itm_lot in _item["lots"]:
                        if str(_itm_lot["lot_number"]) == str(lot):
                            physical_qty = _itm_lot["quantity"]
                else:
                    for _itm_lot in _item["lots"]:
                        if not bool(_itm_lot["lot_number"]) and not bool(_itm_lot["p_serials"]):
                            physical_qty = _itm_lot["quantity"]
        return int(physical_qty)

    def get_item_inventory_count(self, inputs):
        self.is_inventory_audit = True
        limit = inputs["limit"]
        offset = inputs["offset"]
        products = Products(company_id=self.company_id, user_id=self.user_id)
        tracking_product_ids = None
        if "tracking_product_codes" in inputs and isinstance(inputs["tracking_product_codes"], list):
            _tmp_p_ids = list()
            _x_code = None
            for _p_code in inputs["tracking_product_codes"]:
                _p_id = products.get_product_name_id(p_code=_p_code, raise_exception=False)
                if bool(_p_id):
                    _tmp_p_ids.append(str(_p_id))
            if bool(_tmp_p_ids) and isinstance(_tmp_p_ids, list):
                tracking_product_ids = "'" + "', '".join(_tmp_p_ids) + "'"

        no_tracking_product_ids = None
        if "no_tracking_product_codes" in inputs and isinstance(inputs["no_tracking_product_codes"], list):
            _tmp_p_ids = list()
            for _p_code in inputs["no_tracking_product_codes"]:
                _p_id = products.get_product_name_id(p_code=_p_code, raise_exception=False)
                if bool(_p_id):
                    _tmp_p_ids.append(str(_p_id))
            if bool(_tmp_p_ids) and isinstance(_tmp_p_ids, list):
                no_tracking_product_ids = "'" + "', '".join(_tmp_p_ids) + "'"

        location_ids = list()
        _loc_ids = None
        if "location_name" in inputs:
            locations = Locations(company_id=self.company_id, user_id=self.user_id)
            location_ids = locations.get_location_ids_including_all_child_locations(location_name=inputs["location_name"])
            if bool(location_ids) and isinstance(location_ids, list):
                _loc_ids = "'" + "', '".join(location_ids) + "'"

        lot_ids = None
        if "lots" in inputs and isinstance(inputs["lots"], list):
            lot_names = "'" + "', '".join(inputs["lots"]) + "'"
            query = """SELECT id FROM stock_production_lot WHERE company_id = %d AND name IN (%s)""" % (int(self.company_id), lot_names)
            self.request.env.cr.execute(query)
            records = self.request.env.cr.dictfetchall()
            _tmp_lot_ids = list()
            for _row in records:
                _tmp_lot_ids.append(str(_row["id"]))
            if bool(_tmp_lot_ids):
                lot_ids = "'" + "', '".join(_tmp_lot_ids) + "'"

        _tuple_list = list()
        query = """SELECT SML.product_id, SML.lot_id FROM stock_move_line AS SML LEFT JOIN stock_production_lot AS SPL ON SML.lot_id = SPL.id WHERE SML.company_id = %d"""
        _tuple_list.append(int(self.company_id))

        if bool(_loc_ids):
            query += """ AND SML.location_dest_id IN (%s)"""
            _tuple_list.append(_loc_ids)

        if bool(lot_ids):
            if bool(no_tracking_product_ids):
                query += """ AND ((SML.product_id IN (%s) AND SML.lot_id IN (%s)) OR (SML.product_id IN (%s) AND SML.lot_id IN (%s)))"""
                _tuple_list.append(tracking_product_ids)
                _tuple_list.append(lot_ids)
                _tuple_list.append(no_tracking_product_ids)
                _tuple_list.append(lot_ids)
            else:
                if bool(tracking_product_ids):
                    query += """ AND SML.product_id IN (%s) AND SML.lot_id IN (%s)"""
                    _tuple_list.append(tracking_product_ids)
                    _tuple_list.append(lot_ids)
        else:
            if bool(no_tracking_product_ids):
                query += """ AND SML.product_id IN (%s) AND SML.lot_id IS NULL"""
                _tuple_list.append(no_tracking_product_ids)
        query += """ GROUP BY SML.product_id, SML.lot_id ORDER BY SML.product_id ASC LIMIT %d OFFSET %d"""
        _tuple_list.append(int(limit))
        _tuple_list.append(int(offset))

        query = query % tuple(_tuple_list)
        self.request.env.cr.execute(query)
        records = self.request.env.cr.dictfetchall()
        _records = list()
        if bool(records):
            for each in records:
                _tmp = dict()
                _tmp["erp"] = "Odoo"
                _tmp["warehouse"] = inputs["location_name"]
                (_tmp["barcode"], _tmp["product_name"]) = products.get_barcode(each["product_id"])
                _tracking = self.get_tracking(each["product_id"], each["lot_id"])
                if _tracking == "lot":
                    (_tmp["lot"], _tmp["expiry_date"]) = self.get_lot_n_expiry(each["product_id"], lot_id="x" if not bool(each["lot_id"]) else each["lot_id"])
                    _tmp["serial"] = None
                    _tmp["physical_qty"] = self.get_physical_qty(inputs, _tmp["barcode"], _tmp["lot"])
                elif _tracking == "serial":
                    (_tmp["serial"], _tmp["expiry_date"]) = self.get_lot_n_expiry(each["product_id"], lot_id="x" if not bool(each["lot_id"]) else each["lot_id"])
                    _tmp["lot"] = None
                    _tmp["physical_qty"] = 1
                else:
                    _tmp["lot"] = None
                    _tmp["serial"] = None
                    _tmp["expiry_date"] = None
                    _tmp["physical_qty"] = self.get_physical_qty(inputs, _tmp["barcode"])
                (_tmp["in_stock"], _tmp["available"], _tmp["allocated"], _tmp["quarantined"], _tmp["to_receive"]) = self.get_stock(location_ids, each["product_id"], each["lot_id"])
                _records.append(_tmp)
        return _records

    def get_location_wise_item_stock(self, warehouse, location_name, location_ids, product_id, lot_id):
        in_stock = 0
        available = 0
        products = Products(company_id=self.company_id, user_id=self.user_id)
        locations = Locations(company_id=self.company_id, user_id=self.user_id)

        _tuple_list = list()
        query = """SELECT SUM(quantity) AS quantity, SUM(reserved_quantity) AS reserved_quantity, product_id, location_id FROM stock_quant WHERE company_id = %d AND product_id = %d AND location_id IN (%s)"""
        _tuple_list.append(int(self.company_id))
        _tuple_list.append(int(product_id))
        _loc_ids = "'" + "', '".join(location_ids) + "'"
        _tuple_list.append(_loc_ids)

        if self.is_no_tracking:
            query += """ AND lot_id IS NULL"""
        else:
            query += """ AND lot_id = %d"""
            _tuple_list.append(int(lot_id))

        query += """ GROUP BY product_id, location_id"""
        query = query % tuple(_tuple_list)
        self.request.env.cr.execute(query)
        records = self.request.env.cr.dictfetchall()
        _records = list()
        if bool(records):
            for each in records:
                allocated = self.get_allocation(each["product_id"], each["location_id"], lot_id)
                quarantine = self.get_quarantine(each["product_id"], each["location_id"], lot_id)
                in_stock = float(each["quantity"])
                available = float(in_stock - float(each["reserved_quantity"]))
                to_receive = self.get_to_receive(location_ids, each["product_id"], lot_id)
                _tmp = dict()
                _tmp["erp"] = "Odoo"
                _tmp["warehouse"] = warehouse
                _tmp["storage_location"] = locations.get_storage_location(each["location_id"])
                (_tmp["barcode"], _tmp["product_name"]) = products.get_barcode(product_id)
                _tracking = self.get_tracking(each["product_id"], lot_id)
                if _tracking == "lot":
                    (_tmp["lot"], _tmp["expiry_date"]) = self.get_lot_n_expiry(each["product_id"], lot_id="x" if not bool(lot_id) else lot_id)
                    _tmp["serial"] = None
                elif _tracking == "serial":
                    (_tmp["serial"], _tmp["expiry_date"]) = self.get_lot_n_expiry(each["product_id"], lot_id="x" if not bool(lot_id) else lot_id)
                    _tmp["lot"] = None
                else:
                    _tmp["lot"] = None
                    _tmp["serial"] = None
                    _tmp["expiry_date"] = None
                _tmp["in_stock"] = int(in_stock)
                _tmp["available"] = int(available)
                _tmp["allocated"] = int(allocated)
                _tmp["quarantined"] = int(quarantine)
                _tmp["to_receive"] = int(to_receive)
                _records.append(_tmp)
        else:
            allocated = self.get_allocation(product_id, None, lot_id)
            quarantine = self.get_quarantine(product_id, None, lot_id)
            to_receive = self.get_to_receive(location_ids, product_id, lot_id)
            _tmp = dict()
            _tmp["erp"] = "Odoo"
            _tmp["warehouse"] = warehouse
            _tmp["storage_location"] = location_name
            (_tmp["barcode"], _tmp["product_name"]) = products.get_barcode(product_id)
            _tracking = self.get_tracking(product_id, lot_id)
            if _tracking == "lot":
                (_tmp["lot"], _tmp["expiry_date"]) = self.get_lot_n_expiry(product_id, lot_id="x" if not bool(lot_id) else lot_id)
                _tmp["serial"] = None
            elif _tracking == "serial":
                (_tmp["serial"], _tmp["expiry_date"]) = self.get_lot_n_expiry(product_id, lot_id="x" if not bool(lot_id) else lot_id)
                _tmp["lot"] = None
            else:
                _tmp["lot"] = None
                _tmp["serial"] = None
                _tmp["expiry_date"] = None
            _tmp["in_stock"] = int(in_stock)
            _tmp["available"] = int(available)
            _tmp["allocated"] = int(allocated)
            _tmp["quarantined"] = int(quarantine)
            _tmp["to_receive"] = int(to_receive)
            _records.append(_tmp)
        return _records

    def get_item_instant_inventory_details(self, inputs):
        product_code = str(inputs["product_code"])
        products = Products(company_id=self.company_id, user_id=self.user_id)
        product_id = products.get_product_name_id(p_code=product_code)

        location_name = inputs["location_name"]
        locations = Locations(company_id=self.company_id, user_id=self.user_id)
        location_ids = locations.get_location_ids_including_all_child_locations(location_name=location_name)

        start_date = inputs["start_date"]
        end_date = inputs["end_date"]

        lot_id = None
        if not bool(inputs["serial"]) and not bool(inputs["lot"]):
            self.is_no_tracking = True
        else:
            lot_name = None
            if bool(inputs["serial"]):
                lot_name = str(inputs["serial"])
            elif bool(inputs["lot"]):
                lot_name = str(inputs["lot"])
            if bool(lot_name):
                lot_id = self.get_lot_n_expiry(product_id, lot_name=lot_name)
                if not bool(lot_id):
                    raise Exception("The lot/serial (" + lot_name + ") does not exist in Odoo!")

        _response = dict()
        _tmp = dict()
        _tmp["erp"] = "Odoo"
        _tmp["warehouse"] = locations.get_warehouse_name_by_stock_location(location_name=location_name)
        _tmp["location"] = location_name
        (_tmp["barcode"], _tmp["product_name"]) = products.get_barcode(product_id)
        _tracking = self.get_tracking(product_id, lot_id)
        if _tracking == "lot":
            (_tmp["lot"], _tmp["expiry_date"]) = self.get_lot_n_expiry(product_id, lot_id="x" if not bool(lot_id) else lot_id)
            _tmp["serial"] = None
        elif _tracking == "serial":
            (_tmp["serial"], _tmp["expiry_date"]) = self.get_lot_n_expiry(product_id, lot_id="x" if not bool(lot_id) else lot_id)
            _tmp["lot"] = None
        else:
            _tmp["lot"] = None
            _tmp["serial"] = None
            _tmp["expiry_date"] = None
        (_tmp["in_stock"], _tmp["available"], _tmp["allocated"], _tmp["quarantined"], _tmp["to_receive"]) = self.get_stock(location_ids, product_id, lot_id)
        _response["stocks"] = _tmp

        _response["location_stocks"] = self.get_location_wise_item_stock(_tmp["warehouse"], location_name, location_ids, product_id, lot_id)

        inbounds = Inbounds(company_id=self.company_id, user_id=self.user_id)
        _response["inbounds"] = inbounds.get_item_inbounds(location_ids, product_id, start_date, end_date, lot_serial=lot_id)

        outbounds = Outbounds(company_id=self.company_id, user_id=self.user_id)
        _response["outbounds"] = outbounds.get_item_outbounds(location_ids, product_id, start_date, end_date, lot_serial=lot_id)

        return _response
