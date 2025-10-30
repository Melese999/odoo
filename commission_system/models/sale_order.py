from odoo import models, fields, api, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError, AccessError
import logging
import time  # Added for the time.sleep in _update_manufacturing_dimensions

_logger = logging.getLogger(__name__)


class SaleOrderBankPayment(models.Model):
    _name = 'sale.order.bank.payment'
    _description = 'Sales Order Bank Payment'

    sale_order_id = fields.Many2one(
        'sale.order', string='Sales Order', ondelete='cascade'
    )
    bank_account_id = fields.Many2one(
        'res.partner.bank', string='Bank', required=True
    )
    tt_number = fields.Char(
        string='TT Number', required=True
    )
    amount = fields.Float(
        string='Amount', required=True
    )

    _sql_constraints = [
        ('unique_tt_number', 'unique(tt_number)', 'The TT number must be unique!')
    ]

    @api.constrains('amount')
    def _check_amount(self):
        for rec in self:
            if rec.amount <= 0:
                raise ValidationError("The amount must be greater than zero.")


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    PITCH_SELECTIONS = [
        ('30', '30 cm'),
        ('35', '35 cm'),
        ('40', '40 cm'),
        ('45', '45 cm'),
        ('50', '50 cm'),
    ]

    # Define the selectable options for effective width
    EFFECTIVE_WIDTH_SELECTIONS = [
        ('87', '87 cm'),
        ('90', '90 cm'),
        ('95', '95 cm'),
        ('100', '100 cm'),
    ]

    # --- New Computed Field for UI Control ---
    can_confirm_or_invoice = fields.Boolean(
        compute='_compute_can_confirm_or_invoice',
        string="Can Confirm/Invoice",
        help="Technical field to control visibility of Confirm and Create Invoice buttons."
    )
    # ----------------------------------------

    # --- Original Custom Fields ---
    commission_rule_id = fields.Many2one(
        'commission_system.rules',
        string="Commission Rule",
        help="Rule applied for calculating commission"
    )

    is_commissionable = fields.Boolean(string="Is Commissionable", default=True)
    agent_id = fields.Many2one(
        'res.partner',
        string="Agent",
        help="The agent responsible for this invoice"
    )


    tin_number = fields.Char(
        string='TIN Number',
        compute='_compute_tin_number',
        store=False,
        readonly=True,
        help="The Tax Identification Number of the customer."
    )

    mobile_number = fields.Char(
        string="Mobile Number",
        compute='_compute_mobile_number',
        store=True,
        readonly=False,
        inverse='_set_mobile_number',
        help="The mobile number of the customer. It is automatically filled from the customer's "
             "contact information but can be manually overridden."
    )

    bank_account_payment_ids = fields.One2many(
        'sale.order.bank.payment', 'sale_order_id', string='Bank Payments'
    )

    advance_paid_amount = fields.Float(
        string='Advance Payment',
        compute='_compute_advance_payment',
        store=True,
        readonly=True
    )

    production_priority = fields.Selection(
        selection=[
            ('low', 'Low Priority'),
            ('medium', 'Medium Priority'),
            ('high', 'High Priority'),
            ('urgent', 'Urgent'),
        ],
        string='Production Priority',
        default='medium',
        required=True,
        help="Priority level for production planning"
    )

    can_edit_priority = fields.Boolean(
        string='Can Edit Priority',
        compute='_compute_can_edit_priority',
        help="Technical field to control UI permissions"
    )

    pitch = fields.Selection(
        selection=PITCH_SELECTIONS,
        string='Pitch (cm)',
        help="The distance between two consecutive points on the product."
    )

    '''effective_width = fields.Float(
        string='Effective Width (cm)',
        help="The effective width measurement for the product or order."
    )'''

    effective_width = fields.Selection(
        selection=EFFECTIVE_WIDTH_SELECTIONS,
        string='Effective Width',
        help="The effective width (87 cm to 100 cm) selected for the product."
    )
    location_id = fields.Many2one(
        'stock.location', string='Production Location',
        help='Production location/plant for tracking (does not affect stock moves).'
    )
    is_credit = fields.Boolean(string="Is Credit Order")
    credit_approver_id = fields.Many2one(
        'res.partner',
        string="Credit For",
        help="Credit Order Belongs to"
    )
    @api.depends()
    def _compute_can_edit_priority(self):
        # Check if the current user is in the 'sales_team.group_sale_manager' group
        is_manager = self.env.user.has_group('sales_team.group_sale_manager')
        for record in self:
            record.can_edit_priority = is_manager

    @api.depends('partner_id', 'partner_id.vat')
    def _compute_tin_number(self):
        for order in self:
            if order.partner_id and order.partner_id.vat:
                order.tin_number = order.partner_id.vat
            else:
                order.tin_number = False

    @api.depends('bank_account_payment_ids.amount')
    def _compute_advance_payment(self):
        for order in self:
            order.advance_paid_amount = sum(order.bank_account_payment_ids.mapped('amount'))

    # --- New Compute Method for UI Control ---
    @api.depends('user_id', 'state')
    def _compute_can_confirm_or_invoice(self):
        # NOTE: 'sales_team.group_sale_manager' is the standard Odoo Manager group.
        # Ensure this is correct for your environment.
        is_manager = self.env.user.has_group('sales_team.group_sale_manager')

        for order in self:
            # The user can confirm/invoice if they are a manager OR they are NOT the assigned salesperson.
            is_own_document = order.user_id == self.env.user

            # Admins (user ID 1) should generally always be allowed regardless of groups
            is_admin = self.env.user.id == SUPERUSER_ID

            order.can_confirm_or_invoice = is_admin or is_manager or not is_own_document

    # ----------------------------------------

    # --- Original Custom Methods ---
    @api.constrains('advance_paid_amount', 'amount_total')
    def _check_advance_payment(self):
        for order in self:
            if order.amount_total and order.advance_paid_amount:
                fifty_percent_total = order.amount_total * 0.50
                if order.advance_paid_amount < fifty_percent_total:
                    raise ValidationError("Advance payment should be greater than 50 percent of the total price.")

    @api.depends('partner_id')
    def _compute_mobile_number(self):
        for order in self:
            order.mobile_number = order.partner_id.mobile

    def _set_mobile_number(self):
        for order in self:
            if order.partner_id and order.mobile_number:
                order.partner_id.mobile = order.mobile_number

    @api.onchange('order_line')
    def _onchange_order_line(self):
        self._compute_amounts()

    @api.depends('order_line', 'order_line.price_subtotal', 'order_line.price_tax')
    def _compute_amounts(self):
        for order in self:
            amount_untaxed = sum(order.order_line.mapped('price_subtotal'))
            amount_tax = sum(order.order_line.mapped('price_tax'))

            order.amount_untaxed = order.currency_id.round(amount_untaxed)
            order.amount_tax = order.currency_id.round(amount_tax)
            order.amount_total = order.amount_untaxed + order.amount_tax

    def _prepare_invoice(self):
        res = super(SaleOrder, self)._prepare_invoice()
        res['agent_id'] = self.agent_id.id
        res['pitch'] = self.pitch
        res['effective_width'] = self.effective_width
        res['is_credit'] = self.is_credit
        res['credit_approver_id'] = self.credit_approver_id.id if self.credit_approver_id else False
        return res

    def _create_invoices(self, *args, **kwargs):
        """Create invoices from SO and copy bank payments"""
        for order in self:
            if order.is_credit and order.state in ['sale', 'done']:
                for line in order.order_line.filtered(lambda l: not l.display_type):
                    line.qty_to_invoice = line.product_uom_qty - line.qty_invoiced

        invoices = super(SaleOrder, self)._create_invoices(*args, **kwargs)
        
        for order in self:
            for inv in invoices:
                # Copy SO bank payments into Invoice Bank Payment
                for line in order.bank_account_payment_ids:
                    self.env['account.move.bank.payment'].create({
                        'invoice_id': inv.id,
                        'bank_account_id': line.bank_account_id.id,
                        'tt_number': line.tt_number,
                        'amount': line.amount,
                    })
        for order in self.filtered(lambda o: o.is_credit and o.state in ['sale', 'done']):
            for line in order.order_line:
                if line.product_uom_qty <= line.qty_invoiced:
                    line.qty_to_invoice = 0

        self._compute_invoice_status()
        return invoices

    def _compute_invoice_status(self):
        for order in self:
            if order.is_credit and order.state in ['sale', 'done']:
                all_invoiced = all(
                    line.qty_invoiced >= line.product_uom_qty
                    for line in order.order_line
                    if not line.display_type
                )
                order.invoice_status = 'invoiced' if all_invoiced else 'to invoice'
            else:
                super(SaleOrder, order)._compute_invoice_status()

    def debug_manufacturing_links_detailed(self):
        # ... (Your original debug method) ...
        for order in self:
            _logger.info("=== DETAILED DEBUG: Order %s ===", order.name)

            all_mos = self.env['mrp.production'].search([('origin', 'ilike', order.name)])
            _logger.info("Total MOs found: %s", len(all_mos))

            for mo in all_mos:
                _logger.info("MO %s: Product: %s, Length: %s, Sale Line: %s",
                             mo.name, mo.product_id.name, mo.length,
                             mo.sale_line_id.id if mo.sale_line_id else "None")

                mo_moves = self.env['stock.move'].search([('production_id', '=', mo.id)])
                for move in mo_moves:
                    _logger.info("  Move %s: Sale Line: %s, Product: %s",
                                 move.id, move.sale_line_id.id if move.sale_line_id else "None",
                                 move.product_id.name)

            for line in order.order_line:
                _logger.info("Line %s: Product: %s, Length: %s",
                             line.id, line.product_id.name, line.length)

                line_moves = self.env['stock.move'].search([('sale_line_id', '=', line.id)])
                _logger.info("  Moves for line: %s", len(line_moves))

                for move in line_moves:
                    _logger.info("  Move %s: MO: %s, Product: %s",
                                 move.id, move.production_id.name if move.production_id else "None",
                                 move.product_id.name)

    def _update_manufacturing_dimensions(self):
        """Update manufacturing orders with dimensional data - FIXED VERSION"""
        for order in self:
            _logger.info("Updating manufacturing orders for order: %s", order.name)

            time.sleep(3)  # 3 second delay to ensure all MOs are created

            all_mos = self.env['mrp.production'].search([('origin', 'ilike', order.name)])
            _logger.info("Found %s manufacturing orders total for order %s", len(all_mos), order.name)

            product_mo_map = {}
            for mo in all_mos:
                if mo.product_id.id not in product_mo_map:
                    product_mo_map[mo.product_id.id] = []
                product_mo_map[mo.product_id.id].append(mo)
                _logger.info("MO: %s, Product: %s", mo.name, mo.product_id.name)

            for line in order.order_line:
                if line.product_id.type in ['product', 'consu']:
                    _logger.info("Processing line %s: Product: %s, Length: %s",
                                 line.id, line.product_id.name, line.length)

                    moves = self.env['stock.move'].search([
                        ('sale_line_id', '=', line.id),
                        ('production_id', '!=', False)
                    ])

                    _logger.info("Found %s moves for line %s", len(moves), line.id)

                    mo_to_update = None
                    if moves:
                        mo_to_update = moves[0].production_id
                        _logger.info("Linking line %s to MO %s via move", line.id, mo_to_update.name)

                    if not mo_to_update and line.product_id.id in product_mo_map:
                        mos_for_product = product_mo_map[line.product_id.id]

                        if len(mos_for_product) > 0:
                            mo_to_update = mos_for_product[0]
                            product_mo_map[line.product_id.id] = mos_for_product[1:] + [mos_for_product[0]]

                            _logger.info("Linking line %s to MO %s via product mapping", line.id, mo_to_update.name)

                    if mo_to_update:
                        needs_update = (
                                mo_to_update.length != line.length or
                                mo_to_update.weight != line.weight or
                                mo_to_update.pitch != line.pitch or
                                mo_to_update.sale_line_id != line
                        )

                        if needs_update:
                            update_vals = {
                                'sale_line_id': line.id,
                                'length': line.length,
                                'weight': line.weight,
                                'pitch': line.pitch,
                                'total_length': line.total_length,
                                'total_weight': line.total_weight,
                                'sketch_attachment_ids': line.sketch_attachment_ids,
                            }

                            mo_to_update.write(update_vals)
                            _logger.info("SUCCESS: Updated MO %s with length %s (from line %s)",
                                         mo_to_update.name, line.length, line.id)
                        else:
                            _logger.info("MO %s already has correct data", mo_to_update.name)
                    else:
                        _logger.warning("No manufacturing order found for line %s", line.id)

        # --- Override: Restrict Confirmation ---

    def action_confirm(self):

        restricted_group = self.env.ref('commission_system.group_restricted_users')
        if self.env.user in restricted_group.users:
            raise UserError("You are not allowed to confirm quotations.")

        # 2. STANDARD ODOO CONFIRMATION & EXISTING LOGIC
        result = super(SaleOrder, self).action_confirm()
        for order in self:
            if order.is_credit:
                self._create_invoices() 
        # 3. CUSTOM LOGIC
        self._update_manufacturing_dimensions()

        return result

    @api.model
    def default_get(self, fields_list):
        res = super(SaleOrder, self).default_get(fields_list)
        user_loc = self.env.user.production_location_id
        if user_loc:
            res.setdefault('location_id', user_loc.id)
        return res

    def write(self, vals):
        if 'location_id' in vals:
            allowed_group = self.env.ref(
                'commission_system.group_sales_location_manager',
                raise_if_not_found=False
            )
            if not allowed_group or (self.env.user and allowed_group not in self.env.user.groups_id):
                raise AccessError("You are not allowed to change the Production Location on a Sales Order.")

        # Proceed with the normal write
        res = super(SaleOrder, self).write(vals)

        # If the location_id was changed, update related manufacturing orders
        if 'location_id' in vals:
            for order in self:
                # Search by origin only, since sale_order_id doesn't exist on mrp.production
                mo_list = self.env['mrp.production'].search([
                    ('origin', '=', order.name)
                ])

                # Update only active (non-done/non-cancelled) MOs
                if mo_list:
                    mo_list.filtered(
                        lambda m: m.state not in ['done', 'cancel']
                    ).sudo().write({'location_id': order.location_id.id})

        return res

# Invoice Bank Payment


class AccountMoveBankPayment(models.Model):
    _name = 'account.move.bank.payment'
    _description = 'Invoice Bank Payment'

    invoice_id = fields.Many2one('account.move', string='Customer Invoice', ondelete='cascade')
    bank_account_id = fields.Many2one('res.partner.bank', string='Bank', required=True)
    tt_number = fields.Char(string='TT Number', required=True)
    amount = fields.Float(string='Amount', required=True)

    _sql_constraints = [
        ('unique_tt_number_invoice', 'unique(tt_number)', 'The TT number must be unique!')
    ]

    @api.constrains('amount')
    def _check_amount(self):
        for rec in self:
            if rec.amount <= 0:
                raise ValidationError("The amount must be greater than zero.")


class AccountMove(models.Model):
    _inherit = 'account.move'

    bank_account_payment_ids = fields.One2many(
        'account.move.bank.payment', 'invoice_id', string='Bank Payments'
    )
    bank_payment_total = fields.Float(
        string='Bank Payment Total',
        compute='_compute_bank_payment_total', store=True
    )

    @api.depends('bank_account_payment_ids.amount')
    def _compute_bank_payment_total(self):
        for inv in self:
            inv.bank_payment_total = sum(inv.bank_account_payment_ids.mapped('amount'))
class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def _prepare_invoice_line(self, **optional_values):
        if self.display_type:
            return super()._prepare_invoice_line(**optional_values)

        vals = super()._prepare_invoice_line(**optional_values)
        if self.order_id.is_credit and self.order_id.state in ['sale', 'done'] and vals:
            vals['quantity'] = self.product_uom_qty
        return vals