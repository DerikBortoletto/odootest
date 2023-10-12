from re import findall as regex_findall, split as regex_split
from collections import Counter, defaultdict


from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import OrderedSet
from odoo.tools.float_utils import float_round, float_compare, float_is_zero


class StockMove(models.Model):
    _inherit = "stock.move"
    
    display_assign_lot = fields.Boolean(compute='_compute_display_assign_serial')
    lot_name = fields.Char('Lot Number')
    
    
    @api.depends('has_tracking', 'picking_type_id.use_create_lots', 'picking_type_id.use_existing_lots', 'state')
    def _compute_display_assign_serial(self):
        super()._compute_display_assign_serial()
        for move in self:
            move.display_assign_lot = (move.display_assign_serial or (move.has_tracking == 'lot' and
                move.state in ('partially_available', 'assigned', 'confirmed') and
                move.picking_type_id.use_create_lots and not move.picking_type_id.use_existing_lots and
                not move.origin_returned_move_id.id))

    def _generate_serial_move_line_commands(self, lot_names, origin_move_line=None):
        """Return a list of commands to update the move lines (write on
        existing ones or create new ones).
        Called when user want to create and assign multiple serial numbers in
        one time (using the button/wizard or copy-paste a list in the field).

        :param lot_names: A list containing all serial number to assign.
        :type lot_names: list
        :param origin_move_line: A move line to duplicate the value from, default to None
        :type origin_move_line: record of :class:`stock.move.line`
        :return: A list of commands to create/update :class:`stock.move.line`
        :rtype: list
        """
        self.ensure_one()

        # Select the right move lines depending of the picking type configuration.
        move_lines = self.env['stock.move.line']
        if self.picking_type_id.show_reserved:
            move_lines = self.move_line_ids.filtered(lambda ml: not ml.lot_id and not (bool(ml.lot_name) or bool(ml.serial_name)))
        else:
            move_lines = self.move_line_nosuggest_ids.filtered(lambda ml: not ml.lot_id and not (bool(ml.lot_name) or bool(ml.serial_name)))

        if origin_move_line:
            location_dest = origin_move_line.location_dest_id
        else:
            location_dest = self.location_dest_id._get_putaway_strategy(self.product_id)
        move_line_vals = {
            'picking_id': self.picking_id.id,
            'location_dest_id': location_dest.id or self.location_dest_id.id,
            'location_id': self.location_id.id,
            'product_id': self.product_id.id,
            'product_uom_id': self.product_id.uom_id.id,
            'qty_done': 1,
        }
        if origin_move_line:
            # `owner_id` and `package_id` are taken only in the case we create
            # new move lines from an existing move line. Also, updates the
            # `qty_done` because it could be usefull for products tracked by lot.
            move_line_vals.update({
                'owner_id': origin_move_line.owner_id.id,
                'package_id': origin_move_line.package_id.id,
                'qty_done': origin_move_line.qty_done or 1,
            })

        move_lines_commands = []
        for lot_name in lot_names:
            # We write the lot name on an existing move line (if we have still one)...
            if move_lines:
                move_lines_commands.append((1, move_lines[0].id, {
                    'lot_name': self.lot_name,
                    'serial_name': lot_name,
                    'qty_done': 1,
                }))
                move_lines = move_lines[1:]
            # ... or create a new move line with the serial name.
            else:
                move_line_cmd = dict(move_line_vals, serial_name=lot_name, lot_name=self.lot_name)
                move_lines_commands.append((0, 0, move_line_cmd))
        return move_lines_commands

    
class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    lot_name = fields.Char('Lot Number')
    serial_name = fields.Char('Serial Number')
    tracking = fields.Selection(related='product_id.tracking')
    
    @api.constrains('lot_id', 'product_id')
    def _check_lot_product(self):
        for line in self:
            if line.lot_id and line.product_id != line.lot_id.sudo().product_id:
                raise ValidationError(_('This lot %s is incompatible with this product %s' % (line.lot_id.display_name, line.product_id.display_name)))
    
    @api.onchange('serial_name', 'lot_name', 'lot_id')
    def onchange_serial_number(self):
        """ When the user is encoding a move line for a tracked product, we apply some logic to
        help him. This includes:
            - automatically switch `qty_done` to 1.0
            - warn if he has already encoded `lot_name` in another move line
        """
        res = {}
        if self.product_id.tracking == 'serial':
            if not self.qty_done:
                self.qty_done = 1

            message = None
            if self.serial_name or self.lot_id:
                move_lines_to_check = self._get_similar_move_lines() - self
                if self.serial_name:
                    counter = Counter([line.serial_name for line in move_lines_to_check])
                    if counter.get(self.serial_name) and counter[self.serial_name] > 1:
                        message = _('You cannot use the same serial number twice. Please correct the serial numbers encoded.')
                elif self.lot_id:
                    counter = Counter([line.lot_id.id for line in move_lines_to_check])
                    if counter.get(self.lot_id.id) and counter[self.lot_id.id] > 1:
                        message = _('You cannot use the same serial number twice. Please correct the serial numbers encoded.')

            if message:
                res['warning'] = {'title': _('Warning'), 'message': message}
        return res

    def _action_done(self):
        """ This method is called during a move's `action_done`. It'll actually move a quant from
        the source location to the destination location, and unreserve if needed in the source
        location.
    
        This method is intended to be called on all the move lines of a move. This method is not
        intended to be called when editing a `done` move (that's what the override of `write` here
        is done.
        """
        Quant = self.env['stock.quant']
    
        # First, we loop over all the move lines to do a preliminary check: `qty_done` should not
        # be negative and, according to the presence of a picking type or a linked inventory
        # adjustment, enforce some rules on the `lot_id` field. If `qty_done` is null, we unlink
        # the line. It is mandatory in order to free the reservation and correctly apply
        # `action_done` on the next move lines.
        ml_ids_tracked_without_lot = OrderedSet()
        ml_ids_to_delete = OrderedSet()
        ml_ids_to_create_lot = OrderedSet()
        for ml in self:
            # Check here if `ml.qty_done` respects the rounding of `ml.product_uom_id`.
            uom_qty = float_round(ml.qty_done, precision_rounding=ml.product_uom_id.rounding, rounding_method='HALF-UP')
            precision_digits = self.env['decimal.precision'].precision_get('Product Unit of Measure')
            qty_done = float_round(ml.qty_done, precision_digits=precision_digits, rounding_method='HALF-UP')
            if float_compare(uom_qty, qty_done, precision_digits=precision_digits) != 0:
                raise UserError(_('The quantity done for the product "%s" doesn\'t respect the rounding precision '
                                  'defined on the unit of measure "%s". Please change the quantity done or the '
                                  'rounding precision of your unit of measure.') % (ml.product_id.display_name, ml.product_uom_id.name))
    
            qty_done_float_compared = float_compare(ml.qty_done, 0, precision_rounding=ml.product_uom_id.rounding)
            if qty_done_float_compared > 0:
                if ml.product_id.tracking != 'none':
                    picking_type_id = ml.move_id.picking_type_id
                    if picking_type_id:
                        if picking_type_id.use_create_lots:
                            # If a picking type is linked, we may have to create a production lot on
                            # the fly before assigning it to the move line if the user checked both
                            # `use_create_lots` and `use_existing_lots`.
                            if ml.lot_name and not ml.lot_id:
                                if ml.product_id.tracking == 'lot':
                                    lot = self.env['stock.production.lot'].search([('company_id', '=', ml.company_id.id),
                                                                                   ('product_id', '=', ml.product_id.id),
                                                                                   ('name', '=', ml.lot_name),], limit=1)
                                else:
                                    lot = self.env['stock.production.lot'].search([('company_id', '=', ml.company_id.id),
                                                                                   ('product_id', '=', ml.product_id.id),
                                                                                   ('name', '=', ml.lot_name),
                                                                                   ('serial', '=', ml.serial_name),], limit=1)
                                if lot:
                                    ml.lot_id = lot.id
                                else:
                                    ml_ids_to_create_lot.add(ml.id)
                        elif not picking_type_id.use_create_lots and not picking_type_id.use_existing_lots:
                            # If the user disabled both `use_create_lots` and `use_existing_lots`
                            # checkboxes on the picking type, he's allowed to enter tracked
                            # products without a `lot_id`.
                            continue
                    elif ml.move_id.inventory_id:
                        # If an inventory adjustment is linked, the user is allowed to enter
                        # tracked products without a `lot_id`.
                        continue
    
                    if not ml.lot_id and ml.id not in ml_ids_to_create_lot:
                        ml_ids_tracked_without_lot.add(ml.id)
            elif qty_done_float_compared < 0:
                raise UserError(_('No negative quantities allowed'))
            else:
                ml_ids_to_delete.add(ml.id)
    
        if ml_ids_tracked_without_lot:
            mls_tracked_without_lot = self.env['stock.move.line'].browse(ml_ids_tracked_without_lot)
            raise UserError(_('You need to supply a Lot/Serial Number for product: \n - ') +
                              '\n - '.join(mls_tracked_without_lot.mapped('product_id.display_name')))
        ml_to_create_lot = self.env['stock.move.line'].browse(ml_ids_to_create_lot)
        ml_to_create_lot._create_and_assign_production_lot()
    
        mls_to_delete = self.env['stock.move.line'].browse(ml_ids_to_delete)
        mls_to_delete.unlink()
    
        mls_todo = (self - mls_to_delete)
        mls_todo._check_company()
    
        # Now, we can actually move the quant.
        ml_ids_to_ignore = OrderedSet()
        for ml in mls_todo:
            if ml.product_id.type == 'product':
                rounding = ml.product_uom_id.rounding
    
                # if this move line is force assigned, unreserve elsewhere if needed
                if not ml._should_bypass_reservation(ml.location_id) and float_compare(ml.qty_done, ml.product_uom_qty, precision_rounding=rounding) > 0:
                    qty_done_product_uom = ml.product_uom_id._compute_quantity(ml.qty_done, ml.product_id.uom_id, rounding_method='HALF-UP')
                    extra_qty = qty_done_product_uom - ml.product_qty
                    ml_to_ignore = self.env['stock.move.line'].browse(ml_ids_to_ignore)
                    ml._free_reservation(ml.product_id, ml.location_id, extra_qty, lot_id=ml.lot_id, package_id=ml.package_id, owner_id=ml.owner_id, ml_to_ignore=ml_to_ignore)
                # unreserve what's been reserved
                if not ml._should_bypass_reservation(ml.location_id) and ml.product_id.type == 'product' and ml.product_qty:
                    Quant._update_reserved_quantity(ml.product_id, ml.location_id, -ml.product_qty, lot_id=ml.lot_id, package_id=ml.package_id, owner_id=ml.owner_id, strict=True)
    
                # move what's been actually done
                quantity = ml.product_uom_id._compute_quantity(ml.qty_done, ml.move_id.product_id.uom_id, rounding_method='HALF-UP')
                available_qty, in_date = Quant._update_available_quantity(ml.product_id, ml.location_id, -quantity, lot_id=ml.lot_id, package_id=ml.package_id, owner_id=ml.owner_id)
                if available_qty < 0 and ml.lot_id:
                    # see if we can compensate the negative quants with some untracked quants
                    untracked_qty = Quant._get_available_quantity(ml.product_id, ml.location_id, lot_id=False, package_id=ml.package_id, owner_id=ml.owner_id, strict=True)
                    if untracked_qty:
                        taken_from_untracked_qty = min(untracked_qty, abs(quantity))
                        Quant._update_available_quantity(ml.product_id, ml.location_id, -taken_from_untracked_qty, lot_id=False, package_id=ml.package_id, owner_id=ml.owner_id)
                        Quant._update_available_quantity(ml.product_id, ml.location_id, taken_from_untracked_qty, lot_id=ml.lot_id, package_id=ml.package_id, owner_id=ml.owner_id)
                Quant._update_available_quantity(ml.product_id, ml.location_dest_id, quantity, lot_id=ml.lot_id, package_id=ml.result_package_id, owner_id=ml.owner_id, in_date=in_date)
            ml_ids_to_ignore.add(ml.id)
        # Reset the reserved quantity as we just moved it to the destination location.
        mls_todo.with_context(bypass_reservation_update=True).write({
            'product_uom_qty': 0.00,
            'date': fields.Datetime.now(),
        })

    def _create_and_assign_production_lot(self):
        """ Creates and assign new production lots for move lines."""
        lot_vals = []
        # It is possible to have multiple time the same lot to create & assign,
        # so we handle the case with 2 dictionaries.
        key_to_index = {}  # key to index of the lot
        key_to_mls = defaultdict(lambda: self.env['stock.move.line'])  # key to all mls
        for ml in self:
            if ml.product_id.tracking == 'lot':
                key = (ml.company_id.id, ml.product_id.id, ml.lot_name)
            elif ml.product_id.tracking == 'serial':
                key = (ml.company_id.id, ml.product_id.id, ml.lot_name, ml.serial_name)
            key_to_mls[key] |= ml
            if ml.tracking != 'lot' or key not in key_to_index:
                key_to_index[key] = len(lot_vals)
                lot_vals.append(ml._get_value_production_lot())

        lots = self.env['stock.production.lot'].create(lot_vals)
        for key, mls in key_to_mls.items():
            mls._assign_production_lot(lots[key_to_index[key]].with_prefetch(lots._ids))  # With prefetch to reconstruct the ones broke by accessing by index

    def _get_value_production_lot(self):
        self.ensure_one()
        return {
            'company_id': self.company_id.id,
            'name': self.lot_name,
            'serial': self.serial_name,
            'product_id': self.product_id.id
        }

    