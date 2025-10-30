from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = 'account.move'

    # Define the selectable options for pitch (copied from sale.order)
    PITCH_SELECTIONS = [
        ('30', '30 cm'),
        ('35', '35 cm'),
        ('40', '40 cm'),
        ('45', '45 cm'),
        ('50', '50 cm'),
    ]

    # Define the selectable options for effective width (copied from sale.order)
    EFFECTIVE_WIDTH_SELECTIONS = [
        ('87', '87 cm'),
        ('90', '90 cm'),
        ('95', '95 cm'),
        ('100', '100 cm'),
    ]

    # New fields to inherit from the Sales Order
    pitch = fields.Selection(
        selection=PITCH_SELECTIONS,
        string='Pitch (cm)',
        readonly=True,  # Should be read-only on the invoice
        help="The distance between two consecutive points on the product, inherited from the Sales Order."
    )

    effective_width = fields.Selection(
        selection=EFFECTIVE_WIDTH_SELECTIONS,
        string='Effective Width (cm)',
        readonly=True,  # Should be read-only on the invoice
        help="The effective width selected for the product, inherited from the Sales Order."
    )

    commission_record_ids = fields.One2many(
        'commission_system.records',
        'invoice_id',
        string="Commission Records"
    )

    total_commission = fields.Monetary(
        string="Total Commission",
        currency_field='currency_id',
        compute='_compute_total_commission',
        store=True
    )

    agent_id = fields.Many2one(
        'res.partner',
        string="Agent",
        help="The agent responsible for this invoice",
        tracking=True
    )

    is_credit = fields.Boolean(string="Is Credit Order")
    credit_approver_id = fields.Many2one(
        'res.partner',
        string="Credit For",
        help="Credit Order Belongs to"
    )

    fs_number = fields.Char(
        string="FS Number",
        help="Fiscal Serial Number (FS) entered by cashier for Full Invoices.",
        copy=False
    )

    is_full_invoice = fields.Boolean(
        string="Is Full Invoice",
        compute="_compute_is_full_invoice",
        store=True
    )

    @api.depends('move_type')
    def _compute_is_full_invoice(self):
        """Flag only customer invoices (Full Invoices)."""
        for move in self:
            move.is_full_invoice = move.move_type == 'out_invoice'  # adjust if you use a custom type

    _sql_constraints = [
        (
            'unique_fs_number',
            'unique(fs_number)',
            'FS Number must be unique across all invoices!'
        ),
    ]

    # 1. Computed Many2one Field to find the Sale Order (Resolves previous KeyError)
    # sale_order_id = fields.Many2one(
    #     'sale.order',
    #     string='Source Sale Order',
    #     compute='_compute_sale_order_id',
    #     store=True,
    #     readonly=True
    # )

    @api.depends('commission_record_ids.amount')
    def _compute_total_commission(self):
        for record in self:
            record.total_commission = sum(record.commission_record_ids.mapped('amount'))

    def action_post(self):
        """Override action_post to trigger commission calculation after invoice validation."""
        res = super(AccountMove, self).action_post()

        for invoice in self.filtered(lambda i: i.move_type == 'out_invoice'):
            invoice._generate_or_update_commission_lines()

        return res

    def _generate_or_update_commission_lines(self):
        """Generate or update a single, consolidated commission line for this invoice."""
        self.ensure_one()

        # Check if a commission record already exists
        existing_commissions = self.env['commission_system.records'].search([
            ('invoice_id', '=', self.id)
        ])

        if existing_commissions:
            self._update_commission_lines(existing_commissions)
        else:
            self._create_commission_lines()

    def _create_commission_lines(self):
        """
        Create a single commission record for the entire invoice by aggregating
        commissions calculated by product category.
        """
        self.ensure_one()

        sales_order = False
        if self.invoice_origin:
            sales_order = self.env['sale.order'].search([('name', '=', self.invoice_origin)], limit=1)

        # 1. Group invoice lines by product category
        category_subtotals = {}
        for line in self.invoice_line_ids:
            if line.product_id and line.product_id.categ_id:
                category_id = line.product_id.categ_id.id
                category_subtotals.setdefault(category_id, {'amount': 0.0, 'rule_id': False})

                # Check for a specific product rule first, otherwise use category rule
                rule = self.env['commission_system.rules'].search([('product_id', '=', line.product_id.id)], limit=1)
                if not rule:
                    rule = self.env['commission_system.rules'].search([('category_id', '=', category_id)], limit=1)

                # Use the most specific rule found
                category_subtotals[category_id]['rule_id'] = rule.id if rule else False

                # Calculate the subtotal based on the defined dimensional UoM type
                try:
                    if line.product_id.dimensional_uom_type == 'length':
                        subtotal_for_line = line.total_length
                    elif line.product_id.dimensional_uom_type == 'weight':
                        subtotal_for_line = line.total_weight
                    else:
                        subtotal_for_line = line.price_subtotal
                except Exception as e:
                    _logger.error(f"Error determining subtotal for line {line.id}: {e}")
                    subtotal_for_line = line.price_subtotal

                category_subtotals[category_id]['amount'] += subtotal_for_line

        # 2. Calculate the total commission by applying rules to category subtotals
        total_commission_amount = 0.0
        rules = self.env['commission_system.rules'].browse(
            [val['rule_id'] for val in category_subtotals.values() if val['rule_id']])
        rules_map = {r.id: r.rate for r in rules}

        for category_id, data in category_subtotals.items():
            rule_rate = rules_map.get(data['rule_id'], 0.05)  # Default rate if no rule is found
            total_commission_amount += data['amount'] * rule_rate

        # 3. Create a single, consolidated commission record
        if total_commission_amount > 0:
            try:
                # Use the unique_code_generator model to get the unique code
                unique_code = self.env['unique.code.generator'].generate_unique_code('commission_record')
                # unique_code = self.env['unique.code.generator'].generate_unique_code('commission_system.records')
                # record_name = unique_code
                record_name = f"COM-LINE-{unique_code}"
            except Exception as e:
                _logger.warning(f"Failed to generate unique code: {e}")
                record_name = f"COM-{self.invoice_origin or self.name}"

            self.env['commission_system.records'].sudo().create({
                'name': record_name,
                'invoice_id': self.id,
                'sales_order_id': sales_order.id if sales_order else False,
                'salesperson_id': self.user_id.id,
                'agent_id': self.agent_id.id if self.agent_id else False,
                'amount': total_commission_amount,
                'customer_id': self.partner_id.id,
            })

    def _update_commission_lines(self, existing_commissions):
        """
        Delete existing commission lines and re-create a new one to reflect
        any changes in the invoice.
        """
        self.ensure_one()

        # Delete all existing commission records for the invoice
        existing_commissions.unlink()

        # Re-create a single commission record with the updated data
        self._create_commission_lines()

    # The rest of the original methods remain the same
    def _post_process_invoice_lines(self, lines):
        for line in lines:
            line._compute_amount()
        return lines

    def _get_move_lines(self):
        lines = super()._get_move_lines()
        for line in lines:
            if line.product_id and line.product_id.dimensional_uom_type:
                line._compute_amount()
        return lines

    @api.depends(
        'line_ids.matched_debit_ids.debit_move_id.move_id.payment_id.is_matched',
        'line_ids.matched_debit_ids.debit_move_id.move_id.line_ids.amount_residual',
        'line_ids.matched_debit_ids.debit_move_id.move_id.line_ids.amount_residual_currency',
        'line_ids.matched_credit_ids.credit_move_id.move_id.payment_id.is_matched',
        'line_ids.matched_credit_ids.credit_move_id.move_id.line_ids.amount_residual',
        'line_ids.matched_credit_ids.credit_move_id.move_id.line_ids.amount_residual_currency',
        'line_ids.balance',
        'line_ids.currency_id',
        'line_ids.amount_currency',
        'line_ids.amount_residual',
        'line_ids.amount_residual_currency',
        'line_ids.payment_id.state',
        'line_ids.full_reconcile_id',
        'state',
        'invoice_line_ids.total_length',
        'invoice_line_ids.total_weight',
    )
    def _compute_amount(self):
        super(AccountMove, self)._compute_amount()
        for move in self:
            if move.is_invoice(True):
                total_untaxed_recalculated = 0.0
                total_tax_recalculated = 0.0

                for line in move.invoice_line_ids:
                    # Your custom dimensional logic
                    if line.product_id.dimensional_uom_type in ('length', 'weight'):
                        # This part of the code is correct, assuming
                        # that _compute_totals on the line is working.
                        total_untaxed_recalculated += line.price_subtotal
                        total_tax_recalculated += line.price_total - line.price_subtotal
                    else:
                        # Fallback for standard products
                        total_untaxed_recalculated += line.price_subtotal
                        total_tax_recalculated += line.price_total - line.price_subtotal

                # Now, set the totals on the move record
                # The sign is determined by the move type (invoice vs refund)
                sign = move.direction_sign
                move.amount_untaxed = total_untaxed_recalculated
                move.amount_tax = total_tax_recalculated
                move.amount_total = total_untaxed_recalculated + total_tax_recalculated

                # These are the fields that Odoo's core validation relies on for the sign
                move.amount_untaxed_signed = -total_untaxed_recalculated * sign
                move.amount_tax_signed = -total_tax_recalculated * sign
                move.amount_total_signed = -(total_untaxed_recalculated + total_tax_recalculated) * sign
    def write(self, vals):
        if self.env.context.get('skip_agent_sync'):
            return super().write(vals)
        agent_changed = 'agent_id' in vals
        res = super().write(vals)
        if agent_changed:
            new_agent_id = vals['agent_id']
            for invoice in self:
                if invoice.commission_record_ids:
                    invoice.commission_record_ids.with_context(skip_agent_sync=True).write({
                        'agent_id': new_agent_id
                    })
                sale_orders = invoice.commission_record_ids.mapped('sales_order_id')
                if sale_orders:
                    sale_orders.with_context(skip_agent_sync=True).write({'agent_id': new_agent_id})
        return res
