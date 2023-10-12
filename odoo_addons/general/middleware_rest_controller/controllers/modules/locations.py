# -*- coding: utf-8 -*-
from odoo import http


class Locations(http.Controller):
    def __init__(self, *, company_id=None, user_id=None) -> None:
        self.company_id = company_id
        self.user_id = user_id
        self.request = http.request

        self.location_ids = list()
        pass

    def get_warehouse_name(self, w_id):
        warehouse_name = None
        data = self.request.env["stock.warehouse"].sudo().search([("company_id", "=", int(self.company_id)), ("id", "=", int(w_id))])
        for each in data:
            warehouse_name = each.name
        return warehouse_name

    def get_warehouse_name_by_stock_location(self, *, location_name=None):
        warehouse_name = None
        if bool(location_name):
            _temp = location_name.split("/")
            _l_name = _temp[0]
            if len(_temp) > 1:
                data = self.request.env["stock.warehouse"].sudo().search([("company_id", "=", int(self.company_id)), ("code", "=", _l_name)])
                for each in data:
                    warehouse_name = each.name
            else:
                warehouse_name = _l_name
            return warehouse_name

    def get_location_name_id(self, *, location_name=None, location_id=None, stock_location=False):
        if bool(location_name):
            location_id = None
            if bool(stock_location):
                data = self.request.env["stock.location"].sudo().search([("complete_name", "=", location_name)])
                for each in data:
                    location_id = each.id
            else:
                data = self.request.env["stock.warehouse"].sudo().search([("active", "=", True), ("company_id", "=", int(self.company_id)), ("name", "=", location_name)])
                for each in data:
                    location_id = each.id
            if not bool(location_id):
                raise Exception("Given location(" + str(location_name) + ") does not exist in Odoo!")
            return location_id

        if bool(location_id):
            location_name = None
            if bool(stock_location):
                data = self.request.env["stock.location"].sudo().search([("id", "=", int(location_id))])
                for each in data:
                    location_name = each.complete_name
            else:
                data = self.request.env["stock.warehouse"].sudo().search([("active", "=", True), ("company_id", "=", int(self.company_id)), ("lot_stock_id", "=", int(location_id))])
                for each in data:
                    location_name = each.name
            if not bool(location_name):
                raise Exception("Given location ID(" + str(location_id) + ") does not exist in Odoo!")
            return location_name

    def find_child_locations(self, location_id):
        query = """SELECT * FROM stock_location WHERE active = TRUE AND usage = 'internal' AND company_id = %d AND location_id = %d""" % (int(self.company_id), int(location_id))
        self.request.env.cr.execute(query)
        data = self.request.env.cr.dictfetchall()
        if bool(data):
            for each in data:
                if bool(each["id"]):
                    self.location_ids.append(str(each["id"]))
                    self.find_child_locations(each["id"])

    def get_location_ids_including_all_child_locations(self, *, location_name=None):
        if bool(location_name):
            location_stock_id = None
            data = self.request.env["stock.warehouse"].sudo().search([("active", "=", True), ("company_id", "=", int(self.company_id)), ("name", "=", location_name)])
            for each in data:
                location_stock_id = each.lot_stock_id[0].id
            if not bool(location_stock_id):
                data = self.request.env["stock.location"].sudo().search([("name", "=", location_name)])
                for each in data:
                    location_stock_id = each.id
            if not bool(location_stock_id):
                data = self.request.env["stock.location"].sudo().search([("complete_name", "=", location_name)])
                for each in data:
                    location_stock_id = each.id
            if not bool(location_stock_id):
                raise Exception("Given location(" + str(location_name) + ") does not exist in Odoo!")
            else:
                self.location_ids.append(str(location_stock_id))
                self.find_child_locations(location_stock_id)
        return self.location_ids

    def get_all_internal_location_ids(self):
        internal_location_ids = list()
        internal_locations = self.request.env["stock.location"].sudo().search([("usage", "=", "internal")])
        for each in internal_locations:
            internal_location_ids.append(str(each.id))
        return internal_location_ids

    def get_locations_list(self):
        _locations = list()
        data = self.request.env["stock.warehouse"].sudo().search([("active", "=", True), ("company_id", "=", int(self.company_id))])
        for each in data:
            _tmp = dict()
            _tmp["location_id"] = each.id
            _tmp["location_name"] = each.name
            _locations.append(_tmp)
        return _locations

    def get_warehouse_receipts_id(self, wh):
        warehouse = self.request.env["stock.warehouse"].sudo().search([("name", "=", wh)])
        warehouse_id = warehouse[-1].id
        stock_picking_type = self.request.env["stock.picking.type"].sudo().search([("warehouse_id", "=", int(warehouse_id)), ("sequence_code", "=", "IN")])
        return int(stock_picking_type[-1].id)

    def get_receiving_destination_locations(self, inputs):
        _records = list()
        _limit = inputs["limit"]
        _offset = inputs["offset"]
        warehouse = self.request.env["stock.warehouse"].sudo().search([("name", "=", inputs["location_name"])])
        if bool(warehouse):
            wh_code = warehouse[-1].code
            if bool(wh_code):
                wh_code = str(wh_code) + "/Stock%"
                query = """SELECT id, complete_name FROM stock_location WHERE complete_name LIKE '%s' ORDER BY id ASC LIMIT %d OFFSET %d""" % (wh_code, int(_limit), int(_offset))
                self.request.env.cr.execute(query)
                records = self.request.env.cr.dictfetchall()
                for each in records:
                    _records.append({"id": each["id"], "name": each["complete_name"]})
        return _records

    def get_picking_source_locations(self, inputs):
        _records = list()
        _limit = inputs["limit"]
        _offset = inputs["offset"]

        _location_ids = self.get_location_ids_including_all_child_locations(location_name=inputs["location_name"])
        if bool(_location_ids):
            _location_ids = "'" + "', '".join(_location_ids) + "'"

        _lot_name = None
        if "lot" in inputs and bool(inputs["lot"]):
            _lot_name = inputs["lot"]

        _serials = list()
        if "serials" in inputs and bool(inputs["serials"]):
            _serials = inputs["serials"]

        if "product_id" not in inputs or not bool(inputs["product_id"]):
            raise Exception("Product ID is required!")
        product_id = inputs["product_id"]

        if isinstance(_serials, list) and len(_serials) > 0:
            _repeat_locations = list()
            for _serial in _serials:
                query = """SELECT SL.id, SL.complete_name FROM stock_location AS SL INNER JOIN stock_quant AS SQ ON SL.id = SQ.location_id INNER JOIN stock_production_lot AS SPL ON SQ.lot_id = SPL.id WHERE SQ.quantity > 0 AND SL.usage = 'internal' AND SL.company_id = %d AND SQ.product_id = %d AND SPL.name = '%s' AND SQ.location_id IN (%s) GROUP BY SL.id, SL.complete_name ORDER BY SL.id ASC""" % (int(self.company_id), int(product_id), _serial, _location_ids)
                self.request.env.cr.execute(query)
                records = self.request.env.cr.dictfetchall()
                for each in records:
                    if each["complete_name"] not in _repeat_locations:
                        _repeat_locations.append(each["complete_name"])
                        _records.append({"id": each["id"], "name": each["complete_name"]})
            if (len(_repeat_locations) > 0 and len(_serials) > len(_records)) or (len(_serials) > 1 and len(_repeat_locations) > 1):
                raise Exception("Multiple sources found in Odoo! You can split serials for each source.")
            else:
                for _serial in _serials:
                    query = """SELECT SL.id, SL.complete_name FROM stock_location AS SL INNER JOIN stock_quant AS SQ ON SL.id = SQ.location_id INNER JOIN stock_production_lot AS SPL ON SQ.lot_id = SPL.id WHERE SQ.quantity > 0 AND SL.usage = 'internal' AND SL.company_id = %d AND SQ.product_id = %d AND SPL.name = '%s' AND SQ.location_id IN (%s) GROUP BY SL.id, SL.complete_name ORDER BY SL.id ASC LIMIT %d OFFSET %d""" % (int(self.company_id), int(product_id), _serial, _location_ids, int(_limit), int(_offset))
                    self.request.env.cr.execute(query)
                    records = self.request.env.cr.dictfetchall()
                    for each in records:
                        _records.append({"id": each["id"], "name": each["complete_name"]})
        else:
            if bool(_lot_name):
                query = """SELECT SL.id, SL.complete_name FROM stock_location AS SL INNER JOIN stock_quant AS SQ ON SL.id = SQ.location_id INNER JOIN stock_production_lot AS SPL ON SQ.lot_id = SPL.id WHERE SQ.quantity > 0 AND SL.usage = 'internal' AND SL.company_id = %d AND SQ.product_id = %d AND SPL.name = '%s' AND SQ.location_id IN (%s) GROUP BY SL.id, SL.complete_name ORDER BY SL.id ASC LIMIT %d OFFSET %d""" % (int(self.company_id), int(product_id), _lot_name, _location_ids, int(_limit), int(_offset))
                self.request.env.cr.execute(query)
                records = self.request.env.cr.dictfetchall()
                for each in records:
                    _records.append({"id": each["id"], "name": each["complete_name"]})
            else:
                query = """SELECT SL.id, SL.complete_name FROM stock_location AS SL INNER JOIN stock_quant AS SQ ON SL.id = SQ.location_id WHERE SQ.quantity > 0 AND SL.usage = 'internal' AND SL.company_id = %d AND SQ.product_id = %d AND SQ.lot_id IS NULL AND SQ.location_id IN (%s) GROUP BY SL.id, SL.complete_name ORDER BY SL.id ASC LIMIT %d OFFSET %d""" % (int(self.company_id), int(product_id), _location_ids, int(_limit), int(_offset))
                self.request.env.cr.execute(query)
                records = self.request.env.cr.dictfetchall()
                for each in records:
                    _records.append({"id": each["id"], "name": each["complete_name"]})
        if not bool(_records):
            raise Exception("No sources found!")
        return _records

    def get_receiving_destination_location_name(self, inputs):
        _data = dict()
        query = """SELECT complete_name FROM stock_location WHERE id = %d""" % (int(inputs["destination_id"]))
        self.request.env.cr.execute(query)
        records = self.request.env.cr.dictfetchall()
        for each in records:
            _data["name"] = each["complete_name"]
        return _data

    def get_picking_source_location_name(self, inputs):
        _data = dict()
        query = """SELECT complete_name FROM stock_location WHERE id = %d""" % (int(inputs["source_id"]))
        self.request.env.cr.execute(query)
        records = self.request.env.cr.dictfetchall()
        for each in records:
            _data["name"] = each["complete_name"]
        return _data

    def get_receiving_destination_location_id(self, inputs):
        _data = dict()
        warehouse_id = int(inputs["warehouse_id"])
        location_path = inputs["location"]
        if bool(warehouse_id):
            query = """SELECT lot_stock_id FROM stock_warehouse WHERE id = %d""" % (int(warehouse_id))
            self.request.env.cr.execute(query)
            records = self.request.env.cr.dictfetchall()
            location_id = None
            for each in records:
                location_id = int(each["lot_stock_id"])
            if bool(location_id):
                parent_location_id = None
                query = """SELECT id, complete_name FROM stock_location WHERE id = %d""" % (int(location_id))
                self.request.env.cr.execute(query)
                location_name = None
                records = self.request.env.cr.dictfetchall()
                for each in records:
                    parent_location_id = each["id"]
                    location_name = each["complete_name"]
                if bool(location_name):
                    complete_path = ""
                    if location_path[0] == "/":
                        complete_path += location_name + location_path
                    else:
                        complete_path += location_name + "/" + location_path
                    destination_id = None
                    query = """SELECT id FROM stock_location WHERE company_id = %d AND complete_name = '%s'""" % (int(self.company_id), complete_path)
                    self.request.env.cr.execute(query)
                    records = self.request.env.cr.dictfetchall()
                    for each in records:
                        destination_id = int(each["id"])
                    if not bool(destination_id):
                        _parts = location_path.split("/")
                        _loc_parts = list()
                        for _part in _parts:
                            if bool(_part):
                                _loc_parts.append(_part)
                        count = 0
                        search_loc_path = location_name
                        for _loc in _loc_parts:
                            count += 1
                            search_loc_path += "/" + _loc
                            query = """SELECT id FROM stock_location WHERE company_id = %d AND complete_name = '%s'""" % (int(self.company_id), search_loc_path)
                            self.request.env.cr.execute(query)
                            records = self.request.env.cr.dictfetchall()
                            if len(records) > 0:
                                for each in records:
                                    if len(_loc_parts) == count:
                                        destination_id = int(each["id"])
                                    else:
                                        parent_location_id = int(each["id"])
                            else:
                                payload = {
                                    "name": _loc,
                                    "location_id": int(parent_location_id),
                                    "company_id": int(self.company_id),
                                    "active": True
                                }
                                loc_created = self.request.env["stock.location"].sudo().create(payload)
                                if bool(loc_created):
                                    if len(_loc_parts) == count:
                                        destination_id = int(loc_created[-1].id)
                                    else:
                                        parent_location_id = int(loc_created[-1].id)
                    _data["destination_id"] = destination_id
        if not bool(_data):
            raise Exception("An error occurred to get the destination!")
        return _data

    def get_picking_source_location_id(self, inputs):
        _data = dict()
        warehouse_id = int(inputs["warehouse_id"])
        location_path = inputs["location"]
        if bool(warehouse_id):
            query = """SELECT lot_stock_id FROM stock_warehouse WHERE id = %d""" % (int(warehouse_id))
            self.request.env.cr.execute(query)
            records = self.request.env.cr.dictfetchall()
            location_id = None
            for each in records:
                location_id = int(each["lot_stock_id"])
            if bool(location_id):
                query = """SELECT id, complete_name FROM stock_location WHERE id = %d""" % (int(location_id))
                self.request.env.cr.execute(query)
                location_name = None
                records = self.request.env.cr.dictfetchall()
                for each in records:
                    location_name = each["complete_name"]
                if bool(location_name):
                    complete_path = ""
                    if location_path[0] == "/":
                        complete_path += location_name + location_path
                    else:
                        complete_path += location_name + "/" + location_path
                    query = """SELECT id FROM stock_location WHERE company_id = %d AND complete_name = '%s'""" % (int(self.company_id), complete_path)
                    self.request.env.cr.execute(query)
                    records = self.request.env.cr.dictfetchall()
                    for each in records:
                        _data["source_id"] = int(each["id"])
        if not bool(_data):
            raise Exception("An error occurred to get the source!")
        return _data

    def get_storage_location(self, stock_location_id):
        data = self.request.env["stock.location"].sudo().search([("company_id", "=", int(self.company_id)), ("id", "=", int(stock_location_id))])
        for each in data:
            return each.complete_name
        
    def create_warehouse(self, inputs):
        res = dict()
        payload = {
            "name": inputs["name"],
            "code": inputs["short_name"],
            "partner_id": int(inputs["partner_id"])
        }
        wh_created = self.request.env["stock.warehouse"].sudo().create(payload)
        if bool(wh_created):
            res["warehouse_id"] = wh_created[-1].id
            res["warehouse_location_id"] = wh_created[-1].view_location_id[0].id
            res["warehouse_code"] = payload["code"]
        else:
            raise Exception("Unable to create the warehouse!")
        return res

    def create_location(self, inputs):
        res = dict()
        payload = {
            "name": inputs["name"],
            "location_id": int(inputs["parent"]),
            "active": inputs["status"]
        }
        loc_created = self.request.env["stock.location"].sudo().create(payload)
        if bool(loc_created):
            res["location_id"] = loc_created[-1].id
        else:
            raise Exception("Unable to create the location!")
        return res
    
    def get_country_state_ids(self, inputs):
        country_id = None
        state_id = None
        country_name = inputs["country_name"]
        state_name = inputs["state_name"]
        countries = self.request.env["res.country"].sudo().search([])
        for each in countries:
            if country_name.lower() == "united states of america" and each.name.lower() == "united states":
                country_id = int(each.id)
            elif country_name.lower() in each.name.lower() and each.name.lower().endswith(country_name.lower()):
                country_id = int(each.id)
        if country_id is not None:
            states = self.request.env["res.country.state"].sudo().search([("country_id", "=?", country_id)])
            for each in states:
                if state_name.lower() in each.name.lower() and each.name.lower().startswith(state_name.lower()):
                    state_id = int(each.id)
        res = dict()
        res["country_id"] = country_id
        res["state_id"] = state_id
        return res

    def check_if_location_exists(self, inputs):
        res = dict()
        warehouse = self.request.env["stock.warehouse"].sudo().search([("name", "=", inputs["name"])])
        if bool(warehouse):
            res["location_id"] = warehouse[-1].id
        else:
            raise Exception("No such location exists!")
        return res
    
    def check_warehouse_code(self, inputs):
        res = dict()
        _conds = list()
        _conds.append(("code", "=", inputs["code"]))
        code = self.request.env["stock.warehouse"].sudo().search(_conds)
        if bool(code):
            raise Exception("Code already exists!")
        else:
            res["code"] = inputs["code"]
        return res

    def get_location_by_scan(self, inputs):
        res = dict()
        location_id = None
        if "po_id" in inputs and bool(inputs["po_id"]):
            po = self.request.env["purchase.order"].sudo().search([("id", "=", int(inputs["po_id"]))])
            location_id = po[-1].picking_type_id[0].warehouse_id[0].id
        elif "so_id" in inputs and bool(inputs["so_id"]):
            so = self.request.env["sale.order"].sudo().search([("id", "=", int(inputs["so_id"]))])
            location_id = so[-1].warehouse_id[0].id
        if bool(location_id):
            warehouse = self.request.env["stock.warehouse"].sudo().search([("id", "=", int(location_id))])
            if bool(warehouse):
                if "is_wh" in inputs and bool(inputs["is_wh"]):
                    res["id"] = warehouse[-1].id
                    res["name"] = warehouse[-1].name
                else:
                    wh_code = warehouse[-1].code
                    if bool(wh_code):
                        wh_code = str(wh_code) + "/Stock%"
                        query = """SELECT id, complete_name FROM stock_location WHERE complete_name LIKE '%s' AND id = %d""" % (wh_code, int(inputs["location_id"]))
                        self.request.env.cr.execute(query)
                        records = self.request.env.cr.dictfetchall()
                        for each in records:
                            res["id"] = each["id"]
                            res["name"] = each["complete_name"]
        else:
            location_id = int(inputs["location_id"])
            if -2147483648 <= location_id <= 2147483647: #int4
                if "is_wh" in inputs and bool(inputs["is_wh"]):
                    warehouse = self.request.env["stock.warehouse"].sudo().search([("id", "=", location_id)])
                    if bool(warehouse):
                        res["id"] = warehouse[-1].id
                        res["name"] = warehouse[-1].name
                    else:
                        query = """SELECT * FROM stock_location WHERE id = %d""" % (int(location_id))
                        self.request.env.cr.execute(query)
                        _stock_location = self.request.env.cr.dictfetchall()
                        if bool(_stock_location):
                            _wh_code = _stock_location[0]["complete_name"].split("/")[0]
                            if bool(_wh_code):
                                warehouse = self.request.env["stock.warehouse"].sudo().search([("code", "=", _wh_code)])
                                if bool(warehouse):
                                    res["id"] = warehouse[-1].id
                                    res["name"] = warehouse[-1].name
                else:
                    query = """SELECT * FROM stock_location WHERE id = %d""" % (int(location_id))
                    self.request.env.cr.execute(query)
                    _locations = self.request.env.cr.dictfetchall()
                    for _loc in _locations:
                        res["id"] = _loc["id"]
                        res["name"] = _loc["complete_name"]
        if not bool(res):
            raise Exception("No such location exists!")
        return res