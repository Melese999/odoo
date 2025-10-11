from odoo import models, fields, api, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
import logging
import time  # Added for the time.sleep in _update_manufacturing_dimensions

_logger = logging.getLogger(__name__)

class SaleOrderBankPayment(models.Model):
    _name = 'sale.order.bank.payment'
    _description = 'Sales Order Bank Payment'

    sale_order_id = fields.Many2one(
        'sale.order', string='Sales Order', ondelete='cascade'
    )
    bank_id = fields.Many2one(
        'res.bank', string='Bank', required=True
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

    bank_name = fields.Char(string="Bank Name")
    bank_account_id = fields.Many2one(
        'res.partner.bank',
        string='Bank Account',
        # NOTE: Using a hardcoded string ('AMG Holdings') in the domain for a Many2one
        # is generally a bad practice and will likely fail. Consider using a dynamic search
        # or the ID of the company partner record.
        domain="[('partner_id', '=', 'AMG Holdings')]",
        help="Select the bank account for this sale order."
    )

    bank_reference = fields.Char(
        string="Bank Reference / TT Number",
        copy=False,
        help="The Bank Reference / TT Number must be unique.",
        required=True
    )


    tin_number = fields.Char(string="TIN Number", help="The Tax Identification Number of the customer.")

    mobile_number = fields.Char(
        string="Mobile Number",
        compute='_compute_mobile_number',
        store=True,
        readonly=False,
        inverse='_set_mobile_number',
        help="The mobile number of the customer. It is automatically filled from the customer's "
             "contact information but can be manually overridden."
    )
    # ---------------------------------

   
    bank_payment_ids = fields.One2many(
        'sale.order.bank.payment', 'sale_order_id', string='Bank Payments'
    )

    advance_paid_amount = fields.Float(
        string='Advance Payment',
        compute='_compute_advance_payment',
        store=True,
        readonly=True
    )

    @api.depends('bank_payment_ids.amount')
    def _compute_advance_payment(self):
        for order in self:
            order.advance_paid_amount = sum(order.bank_payment_ids.mapped('amount'))

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
        return res


    def _create_invoices(self, *args, **kwargs):
        """Create invoices from SO and copy bank payments"""
        invoices = super(SaleOrder, self)._create_invoices(*args, **kwargs)
        
        for order in self:
            for inv in invoices:
                # Copy SO bank payments into Invoice Bank Payment
                for line in order.bank_payment_ids:
                    self.env['account.move.bank.payment'].create({
                        'invoice_id': inv.id,
                        'bank_id': line.bank_id.id,
                        'tt_number': line.tt_number,
                        'amount': line.amount,
                    })
        return invoices

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

 
        """
        Overrides the standard action to create an invoice from a sales order.
        Adds a security check to restrict non-manager salespersons from creating
        invoices for their own sales orders.
        """
        # Checks if the user is a manager (to allow them to bypass the restriction)
        is_manager = self.env.user.has_group('sales_team.group_sale_manager')

        for order in self:
            is_own_document = order.user_id == self.env.user

            # Deny invoice creation if it's their own document AND they are not a manager
            if is_own_document and not is_manager:
                raise UserError(_(
                    "You are not allowed to create an invoice for your own sales order. "
                    "Please ask a manager to handle the invoicing process."
                ))

        # If the check passes, proceed with the original Odoo invoice creation logic.
        return super(SaleOrder, self).action_create_invoice()
    # -----------------------------
# Invoice Bank Payment
# -----------------------------
class AccountMoveBankPayment(models.Model):
    _name = 'account.move.bank.payment'
    _description = 'Invoice Bank Payment'

    invoice_id = fields.Many2one('account.move', string='Customer Invoice', ondelete='cascade')
    bank_id = fields.Many2one('res.bank', string='Bank', required=True)
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

    bank_payment_ids = fields.One2many(
        'account.move.bank.payment', 'invoice_id', string='Bank Payments'
    )
    bank_payment_total = fields.Float(
        string='Bank Payment Total',
        compute='_compute_bank_payment_total', store=True
    )

    @api.depends('bank_payment_ids.amount')
    def _compute_bank_payment_total(self):
        for inv in self:
            inv.bank_payment_total = sum(inv.bank_payment_ids.mapped('amount'))

