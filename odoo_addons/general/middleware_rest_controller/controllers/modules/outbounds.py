# -*- coding: utf-8 -*-
import json
import ast
import datetime
from odoo import http
from .locations import Locations
from .partners import Partners
from .users import Users
from .products import Products

class Outbounds(http.Controller):
    def __init__(self, *, company_id=None, user_id=None) -> None:
        self.company_id = company_id
        self.user_id = user_id
        self.request = http.request
        pass
    
    def create_sales_order(self, inputs):
        _res = dict()
        payload = {
            "name": inputs["name"],
            "warehouse_id": int(inputs["warehouse_id"]),
            "partner_id": int(inputs["customer_id"]),
            "order_line": [(0, False, product) for product in json.loads(inputs["order_line"])]
        }
        so = self.request.env["sale.order"].sudo().create(payload)
        if bool(so):
            so.action_confirm()
            _res["sales_order_id"] = so[-1].id
        else:
            raise Exception("Unable to create the sales order!")
        return _res
    
    def so_creation_with_delivery(self, inputs):
        _res = dict()
        payload = {
            "name": inputs["name"],
            "warehouse_id": int(inputs["warehouse_id"]),
            "partner_id": int(inputs["customer_id"]),
            "order_line": [(0, False, product) for product in json.loads(inputs["order_line"])]
        }
        so = self.request.env["sale.order"].sudo().create(payload)
        if bool(so):
            so.action_confirm()
            sales_order_id = so[-1].id
            get_stock_picking = so.action_view_delivery()
            if bool(get_stock_picking) and bool(get_stock_picking["res_id"]):
                stock_picking = self.request.env["stock.picking"].sudo().search([("id", "=", get_stock_picking["res_id"])])
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

                    create_transfer = self.request.env["stock.immediate.transfer"].sudo().create(payload)
                    if bool(create_transfer):
                        stock_transfer_id = create_transfer[-1].id
                        transfer = self.request.env["stock.immediate.transfer"].sudo().search([("id", "=", stock_transfer_id)])
                        transfer.with_context(button_validate_picking_ids=transfer.pick_ids.ids).process()

                        _res["sales_order_id"] = sales_order_id
                    else:
                        raise Exception("Unable to arrange the stock transfer!")
                else:
                    raise Exception("Unable to create the sales order!")
            else:
                raise Exception("Unable to pick stock!")
        else:
            raise Exception("Unable to create the sales order!")
        return _res
    
    def sale_order_delivery(self, inputs):
        _res = dict()
        so = self.request.env["sale.order"].sudo().search([("id", "=", inputs["sales_order_id"])])
        if bool(so):
            get_stock_picking = so.action_view_delivery()
            if bool(get_stock_picking) and bool(get_stock_picking["res_id"]):
                stock_picking = self.request.env["stock.picking"].sudo().search([("id", "=", get_stock_picking["res_id"])])
                if bool(stock_picking):
                    if stock_picking[-1].state == "done":
                        raise Exception("Please check if already delivered!")
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

                        create_transfer = self.request.env["stock.immediate.transfer"].sudo().create(payload)
                        if bool(create_transfer):
                            stock_transfer_id = create_transfer[-1].id
                            transfer = self.request.env["stock.immediate.transfer"].sudo().search([("id", "=", stock_transfer_id)])
                            transfer.with_context(button_validate_picking_ids=transfer.pick_ids.ids).process()

                            _res["stock_transfer_id"] = stock_transfer_id
                        else:
                            raise Exception("Unable to arrange the stock transfer!")
                else:
                    raise Exception("Please check if already delivered!")
            else:
                raise Exception("Unable to deliver the order!")
        else:
            raise Exception("Sales order not found!")
        return _res

    @staticmethod
    def get_order_name(rec):
        _tmp = str(rec["date_order"])
        _tmp = _tmp.replace("-", "")
        _tmp = _tmp.replace(" ", "")
        _tmp = _tmp.replace(":", "")
        return rec["name"] + "-" + _tmp

    def get_location_n_customer_by_sale_order(self, so_id):
        location = None
        customer = None
        so = self.request.env["sale.order"].sudo().search([("id", "=", int(so_id))])
        if bool(so):
            location = so[-1].warehouse_id[0].name
            location = location.split(":")[0]
            customer = so[-1].partner_id[0].name
        return location, customer

    def check_duplicate_so_line_items(self, inputs):
        has_duplicate = False
        query = """SELECT * FROM sale_order_line WHERE order_id = %d""" % (int(inputs["so_id"]))
        self.request.env.cr.execute(query)
        line_items = self.request.env.cr.dictfetchall()
        _temp_line_item = list()
        for _li in line_items:
            if _li["product_id"] in _temp_line_item:
                has_duplicate = True
            _temp_line_item.append(_li["product_id"])
        return has_duplicate

    def list_sale_orders(self, inputs):
        _limit = int(inputs["limit"])
        _offset = 0
        if "page" in inputs and int(inputs["page"]) > 0:
            _offset = (int(inputs["page"]) - 1) * _limit
        state = "'" + "', '".join(["draft", "sent", "cancel"]) + "'"
        company_id = self.company_id
        query = """SELECT SO.* FROM sale_order AS SO LEFT JOIN sale_order_line AS SOL ON SO.id = SOL.order_id WHERE SO.id NOT IN (SELECT SOL2.order_id FROM sale_order_line AS SOL2 INNER JOIN product_product AS PP ON SOL2.product_id = PP.id WHERE (PP.barcode = '') IS NOT FALSE AND SOL2.order_id = SO.id) AND SOL.product_id NOT IN (SELECT PP2.id FROM product_product AS PP2 INNER JOIN product_template AS PT ON PP2.product_tmpl_id = PT.id WHERE PP2.id = SOL.product_id AND PT.type != 'product') AND SO.state NOT IN (%s) AND SO.company_id = %d AND SO.user_id = %d AND (SOL.product_uom_qty - SOL.qty_delivered) > 0 GROUP BY SO.id ORDER BY SO.id DESC LIMIT %d OFFSET %d""" % (state, int(company_id), int(self.user_id), _limit, _offset)
        if "is_all_users" in inputs and bool(inputs["is_all_users"]):
            query = """SELECT SO.* FROM sale_order AS SO LEFT JOIN sale_order_line AS SOL ON SO.id = SOL.order_id WHERE SO.id NOT IN (SELECT SOL2.order_id FROM sale_order_line AS SOL2 INNER JOIN product_product AS PP ON SOL2.product_id = PP.id WHERE (PP.barcode = '') IS NOT FALSE AND SOL2.order_id = SO.id) AND SOL.product_id NOT IN (SELECT PP2.id FROM product_product AS PP2 INNER JOIN product_template AS PT ON PP2.product_tmpl_id = PT.id WHERE PP2.id = SOL.product_id AND PT.type != 'product') AND SO.state NOT IN (%s) AND SO.company_id = %d AND (SOL.product_uom_qty - SOL.qty_delivered) > 0 GROUP BY SO.id ORDER BY SO.id DESC LIMIT %d OFFSET %d""" % (state, int(company_id), _limit, _offset)
        self.request.env.cr.execute(query)
        s_orders_data = self.request.env.cr.dictfetchall()
        sale_orders = list()
        for _so in s_orders_data:
            (location, customer) = self.get_location_n_customer_by_sale_order(_so["id"])
            temp = dict()
            temp["id"] = _so["id"]
            temp["duplicate_line_items"] = self.check_duplicate_so_line_items({"so_id": _so["id"]})
            temp["name"] = self.get_order_name(_so)
            temp["customer"] = customer
            temp["location"] = location
            temp["created_on"] = _so["date_order"]
            sale_orders.append(temp)
        return sale_orders
    
    def list_line_items_by_sale_order(self, inputs):
        list_line_items = list()
        so = self.request.env["sale.order"].sudo().search([("id", "=", int(inputs["so_id"]))])
        if bool(so):
            order_line = so[-1].order_line
            line_item_ids = list()
            for line in order_line:
                line_item_ids.append(line[0].id)
            if bool(line_item_ids):                
                for li_id in line_item_ids:
                    line_item = self.request.env["sale.order.line"].sudo().search([("id", "=", int(li_id))])
                    product = line_item[-1].product_id
                    temp = dict()
                    temp["transaction_type"] = "sale"
                    temp["product_id"] = product[0].id
                    temp["product_code"] = product[0].barcode if bool(product[0].barcode) else ""
                    temp["product_name"] = product[0].name
                    temp["product_demand_quantity"] = line_item[-1].product_uom_qty
                    temp["product_delivered_quantity"] = line_item[-1].qty_delivered
                    temp["product_qty_to_deliver"] = line_item[-1].product_uom_qty - line_item[-1].qty_delivered
                    list_line_items.append(temp)
            else:
                raise Exception("Line items not found for the given sale order!")
        else:
            raise Exception("Given sale order does not exist!")
        return list_line_items

    def check_availability(self, ls_id, qty):
        is_available = False
        available = self.request.env["stock.quant"].sudo().search([("lot_id", "=", int(ls_id)), ("company_id", "=", int(self.company_id)), ("quantity", ">", 0)], order="create_date desc")
        if bool(available):
            if float(qty) <= float(available[-1].quantity):
                is_available = True
        return is_available
    
    def picking_by_sale_order(self, inputs):
        _res = dict()
        is_backorder = False
        so = self.request.env["sale.order"].sudo().search([("id", "=", int(inputs["so_id"]))])
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
                    line_item = self.request.env["sale.order.line"].sudo().search([("id", "=", int(li_id))])
                    product = line_item[-1].product_id
                    products_id.append(int(product[0].id))

                    product_variant = self.request.env["product.product"].sudo().search([("id", "=", int(product[0].id))])
                    product_template = self.request.env["product.template"].sudo().search([("id", "=", int(product_variant[-1].product_tmpl_id))])
                    products_product_uom_id.append({"product_id": str(product[0].id), "uom_id": product_template[-1].uom_id[0].id})
                    products_qty_to_pick.append({"product_id": str(product[0].id), "qty_to_pick": line_item[-1].qty_to_deliver})

                go = True
                products_to_this_picking = list()
                invalid_product_details = False
                lot_name_not_exist = None
                serial_name_not_exist = None
                serial_ids = list()
                lot_ids = list()
                for l_item in inputs["line_items"]:
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
                                            lot_serial = self.request.env["stock.production.lot"].sudo().search([("name", "=", _check_ls_name), ("product_id", "=", int(_l_i["product_id"]))])
                                            if not bool(lot_serial):
                                                serial_name_not_exist = _check_ls_name
                                                go = False
                                            else:
                                                ls_id = lot_serial[-1].id
                                                is_available = self.check_availability(ls_id, 1)
                                                if not bool(is_available):
                                                    raise Exception("Requested quantity for the serial(" + _check_ls_name + ") is currently not available!")
                                                else:
                                                    serial_ids.append({_check_ls_name: ls_id})
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
                                            lot_serial = self.request.env["stock.production.lot"].sudo().search([("name", "=", _check_ls_name), ("product_id", "=", int(_l_i["product_id"]))])
                                            if not bool(lot_serial):
                                                lot_name_not_exist = _check_ls_name
                                                go = False
                                            else:
                                                ls_id = lot_serial[-1].id
                                                is_available = self.check_availability(ls_id, _l_i["qty_done"])
                                                if not bool(is_available):
                                                    raise Exception("Requested quantity for the lot(" + _check_ls_name + ") is currently not available!")
                                                else:
                                                    lot_ids.append({_check_ls_name: ls_id})
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
                    stock_picking = self.request.env["stock.picking"].sudo().search([("id", "=", stock_picking_id)])

                    revised_line_items = list()
                    for l_item in inputs["line_items"]:
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
                                            raise Exception("Invalid product uom id detected!")

                                        if go:
                                            temp = dict()
                                            for each in serial_ids:
                                                for _k, _v in each.items():
                                                    if _k == _l_i["serial_name"]:
                                                        temp["lot_id"] = int(_v)
                                                        temp["lot_name"] = _k
                                            temp["product_uom_id"] = int(product_uom_id)
                                            temp["product_id"] = int(_l_i["product_id"])
                                            temp["qty_done"] = float(_l_i["qty_done"])
                                            temp["company_id"] = stock_picking[-1].company_id[0].id
                                            temp["location_dest_id"] = stock_picking[-1].location_dest_id[0].id
                                            if "source" in _l_i and bool(_l_i["source"]):
                                                temp["location_id"] = int(_l_i["source"])
                                            else:
                                                temp["location_id"] = stock_picking[-1].location_id[0].id
                                            temp["picking_id"] = stock_picking_id
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
                                                    raise Exception("Picking quantity of a serial-based product is not possible to process!")
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
                                            raise Exception("Invalid product uom id detected!")

                                        if go:
                                            total_done_qty = total_done_qty + float(_l_i["qty_done"])
                                            temp = dict()
                                            for each in lot_ids:
                                                for _k, _v in each.items():
                                                    if _k == _l_i["lot_name"]:
                                                        temp["lot_id"] = int(_v)
                                                        temp["lot_name"] = _k
                                            temp["product_uom_id"] = int(product_uom_id)
                                            temp["product_id"] = int(_l_i["product_id"])
                                            temp["qty_done"] = float(_l_i["qty_done"])
                                            temp["company_id"] = stock_picking[-1].company_id[0].id
                                            temp["location_dest_id"] = stock_picking[-1].location_dest_id[0].id
                                            if "source" in _l_i and bool(_l_i["source"]):
                                                temp["location_id"] = int(_l_i["source"])
                                            else:
                                                temp["location_id"] = stock_picking[-1].location_id[0].id
                                            temp["picking_id"] = stock_picking_id
                                            temp["move_id"] = False
                                            temp["owner_id"] = False
                                            temp["package_id"] = False
                                            temp["package_level_id"] = False
                                            temp["result_package_id"] = False
                                            lots.append(temp)
                                    if bool(lots):
                                        for each in products_qty_to_pick:
                                            if int(each["product_id"]) == int(line_item_product_id):
                                                if float(each["qty_to_pick"]) > total_done_qty:
                                                    is_backorder = True
                                                if float(each["qty_to_pick"]) < total_done_qty:
                                                    raise Exception("Picking quantity of a lot-based product is not possible to process!")

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
                                            raise Exception("Invalid product uom id detected!")

                                        for each in products_qty_to_pick:
                                            if int(each["product_id"]) == int(line_item_product_id):
                                                if float(each["qty_to_pick"]) > float(_l_i["qty_done"]):
                                                    is_backorder = True
                                                if float(each["qty_to_pick"]) < float(_l_i["qty_done"]):
                                                    raise Exception("Picking quantity of a product is not possible to process!")
                                        if go:
                                            temp = dict()
                                            temp["product_uom_id"] = int(product_uom_id)
                                            temp["product_id"] = int(_l_i["product_id"])
                                            temp["qty_done"] = float(_l_i["qty_done"])
                                            temp["company_id"] = stock_picking[-1].company_id[0].id
                                            temp["location_dest_id"] = stock_picking[-1].location_dest_id[0].id
                                            if "source" in _l_i and bool(_l_i["source"]):
                                                temp["location_id"] = int(_l_i["source"])
                                            else:
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
                        for i in range(len(stock_picking[-1].move_ids_without_package)):
                            stock_move = self.request.env["stock.move"].sudo().search([("id", "=", stock_picking[-1].move_ids_without_package[i].id)])
                            if bool(stock_move):
                                try:
                                    _reserved_line_items_to_remove = list()
                                    stock_move_lines = self.request.env["stock.move.line"].sudo().search([("move_id", "=", int(stock_move[-1].id))])
                                    for _reserved_line in stock_move_lines:
                                        if bool(_reserved_line.id) and _reserved_line.id not in _reserved_line_items_to_remove:
                                            _reserved_line_items_to_remove.append(int(_reserved_line.id))
                                    if len(_reserved_line_items_to_remove) > 0:
                                        stock_move.sudo().write({"move_line_ids": [(2, _line_id, False) for _line_id in _reserved_line_items_to_remove]})
                                except Exception as e:
                                    e.__str__()
                                    pass
                                _line_items_to_move = list()
                                qty_to_pick = 0
                                for revised_line in revised_line_items:
                                    for line in revised_line:
                                        if int(line["product_id"]) == int(stock_move[-1].product_id[0].id):
                                            _line_items_to_move.append(line)
                                            qty_to_pick += float(line["qty_done"])
                                if qty_to_pick > 0:
                                    if float(stock_move[-1].product_qty) - float(stock_move[-1].quantity_done) >= qty_to_pick:
                                        stock_move.sudo().write({"move_line_ids": [(0, False, _line) for _line in _line_items_to_move]})
                                        go = True
                        if go:
                            try:
                                stock_picking.button_validate()
                                if is_backorder:
                                    data = dict()
                                    data["backorder_confirmation_line_ids"] = [(0, False, {"picking_id": stock_picking_id, "to_backorder": True})]
                                    data["pick_ids"] = [(6, False, [stock_picking_id])]
                                    data["show_transfers"] = False
                                    backorder = self.request.env["stock.backorder.confirmation"].sudo().create(data)
                                    backorder.with_context(button_validate_picking_ids=backorder.pick_ids.ids).process()
                                else:
                                    data = dict()
                                    data["immediate_transfer_line_ids"] = [(0, False, {"picking_id": stock_picking_id, "to_immediate": True})]
                                    data["pick_ids"] = [(6, False, [stock_picking_id])]
                                    data["show_transfers"] = False
                                    immediate = self.request.env["stock.immediate.transfer"].sudo().create(data)
                                    immediate.with_context(button_validate_picking_ids=immediate.pick_ids.ids).process()
                            except Exception as e:
                                if "lot" in e.__str__().lower() or "serial" in e.__str__().lower():
                                    raise Exception(e.__str__())
                                pass
                        else:
                            raise Exception("An unknown error occurred to pick!")
                else:
                    if bool(lot_name_not_exist):
                        raise Exception("Lot number(" + lot_name_not_exist + ") does not exist!")
                    elif bool(serial_name_not_exist):
                        raise Exception("Serial number(" + serial_name_not_exist + ") does not exist!")
                    elif bool(invalid_product_details):
                        raise Exception("Invalid product details supplied!")
            else:
                raise Exception("Line items not found for the given sale order!")
        else:
            raise Exception("Given sale order does not exist!")
        return _res

    def get_country_code(self, country):
        code = None
        _country = self.request.env["res.country"].sudo().search([("name", "=", country)])
        if bool(_country):
            code = _country[-1].code
        return code
    
    def get_sale_order_location_n_customer_addresses(self, inputs):
        res = dict()
        so = self.request.env["sale.order"].sudo().search([("id", "=", int(inputs["so_id"]))])
        if bool(so):
            location_id = so[-1].warehouse_id[0].id
            warehouse = self.request.env["stock.warehouse"].sudo().search([("id", "=", int(location_id))])
            warehouse_name = warehouse[-1].name
            location = self.request.env["res.partner"].sudo().search([("id", "=", int(warehouse[-1].partner_id.id))])
            if bool(location):
                res["location_id"] = location_id
                temp = dict()
                if bool(location[-1].country_id) and bool(location[-1].state_id):
                    temp["wh_name"] = warehouse_name
                    temp["name"] = location[-1].name if bool(location[-1].name) else warehouse_name
                    temp["line1"] = location[-1].street
                    temp["city"] = location[-1].city
                    temp["state"] = location[-1].state_id[0].name
                    temp["zip"] = location[-1].zip
                    temp["country"] = location[-1].country_id[0].name
                    temp["country_code"] = self.get_country_code(location[-1].country_id[0].name)
                res["location_address"] = temp

                customer_id = so[-1].partner_id[0].id
                customer = self.request.env["res.partner"].sudo().search([("id", "=", int(customer_id))])
                if bool(customer):
                    res["customer_id"] = customer_id
                    temp = dict()
                    if bool(customer[-1].country_id) and bool(customer[-1].state_id):
                        temp["name"] = customer[-1].name
                        temp["line1"] = customer[-1].street
                        temp["city"] = customer[-1].city
                        temp["state"] = customer[-1].state_id[0].name
                        temp["zip"] = customer[-1].zip
                        temp["country"] = customer[-1].country_id[0].name
                        temp["country_code"] = self.get_country_code(customer[-1].country_id[0].name)
                    res["customer_address"] = temp
        else:
            raise Exception("Sale order not found!")
        return res

    def check_if_so_exists(self, inputs):
        res = dict()
        so = self.request.env["sale.order"].sudo().search([("name", "=", inputs["name"])])
        if bool(so):
            res["id"] = so[-1].id
        else:
            raise Exception("Sale order does not exist!")
        return res

    @staticmethod
    def is_expiration_valid(expiry_date):
        is_valid = False
        if bool(expiry_date):
            x_dt = datetime.datetime.strptime(str(expiry_date), "%Y-%m-%d %H:%M:%S")
            if x_dt > datetime.datetime.now():
                is_valid = True
        return is_valid

    def validate_stock_with_tracking(self, p_id, inputs):
        is_valid = False
        if "quantity" in inputs and float(inputs["quantity"]) > 0:
            quantity = float(inputs["quantity"])
            serial_name = inputs["serial"]
            lot_name = inputs["lot_number"]
            locations = Locations(company_id=self.company_id, user_id=self.user_id)
            internal_ids = locations.get_all_internal_location_ids()
            _internal_loc_ids = "'" + "', '".join(internal_ids) + "'"
            if bool(serial_name):
                spl = self.request.env["stock.production.lot"].sudo().search([("name", "=", serial_name)])
                if bool(spl):
                    spl_id = spl[-1].id
                    query = """SELECT SUM(quantity) AS quantity, SUM(reserved_quantity) AS reserved_qty FROM stock_quant WHERE company_id = %d AND product_id = %d AND location_id IN (%s) AND lot_id = %d""" % (int(self.company_id), int(p_id), _internal_loc_ids, int(spl_id))
                    self.request.env.cr.execute(query)
                    records = self.request.env.cr.dictfetchall()
                    if len(records) > 0:
                        _quantity = 0
                        if bool(records[0]["quantity"]):
                            _quantity = records[0]["quantity"]
                        _reserved_qty = 0
                        # if bool(records[0]["reserved_qty"]):
                        #     _reserved_qty = records[0]["reserved_qty"]
                        if float(_quantity) - float(_reserved_qty) == quantity:
                            is_valid = True
            elif bool(lot_name):
                spl = self.request.env["stock.production.lot"].sudo().search([("name", "=", lot_name)])
                if bool(spl):
                    spl_id = spl[-1].id
                    query = """SELECT SUM(quantity) AS quantity, SUM(reserved_quantity) AS reserved_qty FROM stock_quant WHERE company_id = %d AND product_id = %d AND location_id IN (%s) AND lot_id = %d""" % (int(self.company_id), int(p_id), _internal_loc_ids, int(spl_id))
                    self.request.env.cr.execute(query)
                    records = self.request.env.cr.dictfetchall()
                    if len(records) > 0:
                        _quantity = 0
                        if bool(records[0]["quantity"]):
                            _quantity = records[0]["quantity"]
                        _reserved_qty = 0
                        # if bool(records[0]["reserved_qty"]):
                        #     _reserved_qty = records[0]["reserved_qty"]
                        if float(_quantity) - float(_reserved_qty) >= quantity:
                            is_valid = True
            else:
                query = """SELECT SUM(quantity) AS quantity, SUM(reserved_quantity) AS reserved_qty FROM stock_quant WHERE company_id = %d AND product_id = %d AND location_id IN (%s) AND lot_id IS NULL""" % (int(self.company_id), int(p_id), _internal_loc_ids)
                self.request.env.cr.execute(query)
                records = self.request.env.cr.dictfetchall()
                if len(records) > 0:
                    _quantity = 0
                    if bool(records[0]["quantity"]):
                        _quantity = records[0]["quantity"]
                    _reserved_qty = 0
                    # if bool(records[0]["reserved_qty"]):
                    #     _reserved_qty = records[0]["reserved_qty"]
                    if float(_quantity) - float(_reserved_qty) >= quantity:
                        is_valid = True
        return is_valid

    def validate_picking_lot_serial(self, inputs):
        _res = dict()
        _res["is_ok"] = False
        _res["product_tracking"] = None
        _res["msg"] = "An unknown error occurred!"
        product = self.request.env["product.product"].sudo().search([("barcode", "=", inputs["product_code"])])
        if bool(product):
            product_id = product[-1].id
            lot_name = None
            if not bool(inputs["lot_number"]) and not bool(inputs["serial"]):
                if self.validate_stock_with_tracking(product_id, inputs):
                    _res["is_ok"] = True
                    _res["msg"] = None
                    _res["product_tracking"] = "none"
                else:
                    _res["msg"] = "The product code " + str(inputs["product_code"]) + " has no no-tracking stock!"
            else:
                if bool(inputs["serial"]):
                    lot_name = inputs["serial"]
                elif bool(inputs["lot_number"]):
                    lot_name = inputs["lot_number"]
                if bool(lot_name):
                    _conds = list()
                    _conds.append(("name", "=", lot_name))
                    _conds.append(("product_id", "=", product_id))
                    _conds.append(("company_id", "=", self.company_id))
                    _found = self.request.env["stock.production.lot"].sudo().search(_conds)
                    if bool(_found) and float(_found[-1].product_qty) > 0:
                        if self.is_expiration_valid(_found[-1].expiration_date):
                            if self.validate_stock_with_tracking(product_id, inputs):
                                _res["is_ok"] = True
                                if bool(inputs["serial"]):
                                    _res["product_tracking"] = "serial"
                                else:
                                    _res["product_tracking"] = "lot"
                                _res["msg"] = None
                            else:
                                if bool(inputs["serial"]):
                                    _res["msg"] = "The product code " + str(inputs["product_code"]) + " has no serial-tracking stock!"
                                else:
                                    _res["msg"] = "The product code " + str(inputs["product_code"]) + " has no lot-tracking stock!"
                        else:
                            if bool(inputs["serial"]):
                                _res["msg"] = "The serial " + str(inputs["serial"]) + " has no valid expiration date!"
                            else:
                                _res["msg"] = "The lot " + str(inputs["lot_number"]) + " has no valid expiration date!"
                    else:
                        if bool(inputs["serial"]):
                            _res["msg"] = "The serial " + str(inputs["serial"]) + " does not exist or has no stock!"
                        else:
                            _res["msg"] = "The lot " + str(inputs["lot_number"]) + " does not exist or has no stock!"
        else:
            _res["msg"] = "The product code " + str(inputs["product_code"]) + " does not exist!"
        return _res

    def get_tracking(self, product_id, lot_id):
        _tracking = None
        if bool(lot_id):
            query = """SELECT * FROM stock_move_line WHERE qty_done > 0 AND company_id = %d AND product_id = %d AND lot_id = %d GROUP BY id HAVING MAX(qty_done) > 1 LIMIT 1""" % (
            int(self.company_id), int(product_id), int(lot_id))
            self.request.env.cr.execute(query)
            records = self.request.env.cr.dictfetchall()
            if len(records) > 0:
                _tracking = "lot"
            else:
                _tracking = "serial"
        return _tracking

    def get_lot_n_expiry(self, product_id, *, lot_id=None, lot_name=None):
        if bool(lot_id):
            lot_name = None
            expiry_date = None
            if lot_id != "x":
                query = """SELECT name, expiration_date FROM stock_production_lot WHERE id = %d AND company_id = %d AND product_id = %d""" % (
                int(lot_id), int(self.company_id), int(product_id))
                self.request.env.cr.execute(query)
                records = self.request.env.cr.dictfetchall()
                for _row in records:
                    lot_name = _row["name"]
                    expiry_date = _row["expiration_date"].strftime('%Y-%m-%d') if bool(
                        _row["expiration_date"]) and isinstance(_row["expiration_date"], datetime.datetime) else ""
            return lot_name, expiry_date
        if bool(lot_name):
            lot_id = None
            query = """SELECT id FROM stock_production_lot WHERE company_id = %d AND product_id = %d AND name = '%s'""" % (
            int(self.company_id), int(product_id), lot_name)
            self.request.env.cr.execute(query)
            records = self.request.env.cr.dictfetchall()
            for _row in records:
                lot_id = _row["id"]
            return lot_id

    def get_item_outbounds(self, _locations, _product, start_date, end_date, *, lot_serial=None):
        partners = Partners(company_id=self.company_id, user_id=self.user_id)
        users = Users(company_id=self.company_id, user_id=self.user_id)
        products = Products(company_id=self.company_id, user_id=self.user_id)
        locations = Locations(company_id=self.company_id, user_id=self.user_id)

        _tuple_list = list()
        query = """SELECT SML.company_id, SML.product_id, SM.origin, SM.warehouse_id, SO.partner_id, SOL.product_uom_qty AS ordered_qty, SML.qty_done AS delivered_qty, SML.location_id AS location_id, SML.lot_id, SML.write_date, SML.write_uid FROM stock_move_line AS SML JOIN stock_move AS SM ON SML.move_id = SM.id JOIN sale_order_line AS SOL ON SM.sale_line_id = SOL.id JOIN sale_order AS SO ON SOL.order_id = SO.id WHERE SML.state = 'done' AND SML.company_id = %d AND SML.product_id = %d AND SML.location_id IN (%s) AND SML.write_date BETWEEN '%s' AND '%s'"""
        _tuple_list.append(int(self.company_id))
        _tuple_list.append(int(_product))
        _loc_ids = "'" + "', '".join(_locations) + "'"
        _tuple_list.append(_loc_ids)
        _tuple_list.append(start_date)
        _tuple_list.append(end_date)

        if bool(lot_serial):
            query += """ AND SML.lot_id = %d"""
            _tuple_list.append(int(lot_serial))
        else:
            query += """ AND SML.lot_id IS NULL"""
        query += """ ORDER BY SML.id DESC"""

        query = query % tuple(_tuple_list)
        self.request.env.cr.execute(query)
        records = self.request.env.cr.dictfetchall()
        _history = list()
        for _rec in records:
            _temp = dict()
            _temp["erp"] = "Odoo"
            _temp["warehouse"] = locations.get_warehouse_name(_rec["warehouse_id"])
            _temp["product_name"] = products.get_product_name_id(p_id=_rec["product_id"])
            _temp["sales_order"] = _rec["origin"]
            _temp["customer"] = partners.get_partner_name(_rec["partner_id"], email=True)
            _temp["ordered_qty"] = int(_rec["ordered_qty"])
            _temp["picked_qty"] = int(_rec["delivered_qty"])
            _temp["location"] = locations.get_location_name_id(location_id=_rec["location_id"], stock_location=True)
            _temp["lot"] = None
            _temp["serial"] = None
            _temp["expiry_date"] = None
            _tracking = self.get_tracking(_rec["product_id"], _rec["lot_id"])
            if _tracking == "lot":
                (_temp["lot"], _temp["expiry_date"]) = self.get_lot_n_expiry(_rec["product_id"], lot_id=_rec["lot_id"])
            elif _tracking == "serial":
                (_temp["serial"], _temp["expiry_date"]) = self.get_lot_n_expiry(_rec["product_id"], lot_id=_rec["lot_id"])
            _temp["picked_by"] = users.get_user_name(_rec["write_uid"], email=True)
            _temp["picked_on"] = _rec["write_date"]
            _history.append(_temp)
        return _history