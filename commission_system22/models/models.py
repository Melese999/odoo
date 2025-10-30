# -*- coding: utf-8 -*-
from odoo import models, fields, api, tools, _
from odoo import http
import uuid
from odoo.http import request
from werkzeug.utils import redirect
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo.tools.misc import format_date
import traceback
import logging

from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class BaseAuditMixin(models.AbstractModel):
    _name = 'base.audit.mixin'
    _description = 'Audit Mixin'

    def log_activity(self, action, description=None):
        """Create an audit log entry."""
        logs = []
        user_id = self.env.user.id
        ip_address = self.env.context.get('ip_address', 'Unknown')

        for record in self:
            logs.append({
                'user_id': user_id,
                'action': action,
                'model_name': record._name,
                'record_id': record.id,
                'description': description,
                'ip_address': ip_address,
            })

        if logs:
            self.env['commission_system.user_activity_log'].create(logs)

    def log_custom_action(self, description):
        """Log custom user actions that are not CRUD."""
        self.log_activity('custom', description)

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record in records:
            record.log_activity('create', f'Created record with ID {record.id}')
        return records

    def write(self, vals):
        """Log which fields changed, including old and new values."""
        ignored_fields = {'__last_update', 'write_date'}

        for record in self:
            changes = []
            for field, new_value in vals.items():
                if field in ignored_fields or not hasattr(record, field):
                    continue

                old_value = record[field]

                # Handle many2one fields
                field_type = record._fields[field].type
                if field_type == 'many2one':
                    old_display = old_value.name if old_value else 'None'
                    new_record = self.env[record._fields[field].comodel_name].browse(new_value)
                    new_display = new_record.name if new_record.exists() else 'None'
                    if old_display != new_display:
                        changes.append(f"{field}: {old_display} → {new_display}")
                else:
                    if old_value != new_value:
                        changes.append(f"{field}: {old_value} → {new_value}")

            if changes:
                description = "Updated fields: " + ", ".join(changes)
                record.log_activity('update', description)

        return super().write(vals)

    def unlink(self):
        """Log deletion of records."""
        for record in self:
            record.log_activity('delete', f'Deleted record with ID {record.id}')
        return super().unlink()


class CommissionRules(models.Model):
    _name = 'commission_system.rules'
    _inherit = 'base.audit.mixin'  # Inherit the audit mixin
    _description = 'Commission System Rules'

    name = fields.Char(string='Rule Name', required=True)
    type = fields.Selection([
        ('product', 'Product'),
        ('category', 'Product Category')
    ], required=True, default='product')
    product_id = fields.Many2one('product.product', string="Product", help="Specific product for this rule")
    category_id = fields.Many2one('product.category', string="Product Category", help="Product category for this rule")
    rate_type = fields.Selection([
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed Amount')
    ], required=True, default='fixed')
    rate = fields.Float(string="Rate", required=True, help="Commission rate (percentage or fixed amount)")
    active = fields.Boolean(string='Active', default=True)
    description = fields.Text()
    min_amount = fields.Float()
    max_amount = fields.Float()
    start_date = fields.Date()
    end_date = fields.Date()

    def compute_commission(self, line):
        """Compute commission amount for a given line based on the rule."""
        if self.rate_type == 'percentage':
            return (line.price_subtotal * self.rate) / 100
        elif self.rate_type == 'fixed':
            return self.rate * line.quantity
        return 0.0


class CommissionAssignment(models.Model):
    _name = 'commission_system.assignment'
    _inherit = 'base.audit.mixin'  # Inherit the audit mixin
    _description = 'Commission System Assignment'

    salesperson_id = fields.Many2one('res.users', string='Salesperson')
    sales_team_id = fields.Many2one('crm.team', string='Sales Team')
    agent_id = fields.Many2one('res.partner', string='Agent')
    rule_id = fields.Many2one('commission_system.rules', string='Commission Rule', required=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('archived', 'Archived'),
        ('cancelled', 'Cancelled'),
    ], default='draft', string='Status')

    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')

    _sql_constraints = [
        ('unique_assignment',
         'unique(salesperson_id, agent_id, rule_id)',
         'Each salesperson-agent-rule combination must be unique.')
    ]

    @api.onchange('sales_team_id')
    def _onchange_sales_team_id(self):
        if self.sales_team_id:
            return {
                'domain': {
                    'rule_id': [('team_id', '=', self.sales_team_id.id)]
                }
            }

    def name_get(self):
        result = []
        for record in self:
            name = f"{record.salesperson_id.name or 'N/A'} - {record.agent_id.name or 'N/A'}"
            result.append((record.id, name))
        return result


class CommissionRecords(models.Model):
    _name = 'commission_system.records'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'base.audit.mixin']
    _description = 'Commission System Records'
    _order = 'name desc'

    name = fields.Char(string="Name", required=True)
    rule_id = fields.Many2one('commission_system.rules', string="Commission Rule", ondelete='set null')
    invoice_id = fields.Many2one('account.move', string="Invoice", ondelete='cascade')
    sales_order_id = fields.Many2one('sale.order', string="Sales Order", ondelete='set null')
    salesperson_id = fields.Many2one('res.users', string="Salesperson", ondelete='set null')
    agent_id = fields.Many2one('res.partner', string="Agent", ondelete='set null', tracking=True)
    amount = fields.Float(string="Commission Amount", readonly=True, required=True)
    product_id = fields.Many2one('product.product', string="Product", ondelete='set null')
    sales_team_id = fields.Many2one('crm.team', string='Sales Team')
    payment_id = fields.Many2one('account.payment', string='Payment')
    bill_id = fields.Many2one('commission_system.bill', string="Bill")
    sales_order_line_id = fields.Many2one('sale.order.line', string='Sales Order Line')
    invoice_line_id = fields.Many2one('account.move.line', string='Invoice Line')
    worksheet_id = fields.Many2one('commission_system.worksheet', string='Worksheet', ondelete='cascade')
    invoice_date = fields.Date(related='invoice_id.invoice_date', store=True)

    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('checked', 'Checked'),
            ('approved', 'Approved'),
            ('billed', 'Billed'),
            ('confirmed', 'Confirmed'),
            ('audited', 'Audited'),
            ('paid', 'Paid'),
            ('completed', 'Completed')
        ],
        string='Status', default='draft', tracking=True
    )

    checked_by = fields.Many2one('res.users', string="Checked By", readonly=True)
    approved_by = fields.Many2one('res.users', string="Approved By", readonly=True)
    checked_date = fields.Datetime(string="Checked Date", readonly=True)
    approved_date = fields.Datetime(string="Approved Date", readonly=True)
    confirmed_by = fields.Many2one('res.users', string='Confirmed By', readonly=True)
    confirmed_date = fields.Datetime('Confirmation Date', readonly=True)
    audited_by = fields.Many2one('res.users', string='Audited By', readonly=True)
    audited_date = fields.Datetime('Audit Date', readonly=True)
    paid_by = fields.Many2one('res.users', string='Paid By', readonly=True)
    paid_date = fields.Datetime('Payment Date', readonly=True)

    agent_name = fields.Char(
        string="Agent Name",
        compute="_compute_agent_name",
        store=False
    )

    customer_id = fields.Many2one('res.partner', string="Customer", readonly=True)

    # New fields to be displayed in the view
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        related='invoice_id.currency_id',
        store=True,
        readonly=True
    )

    # Replaced Many2one with a computed One2many to show all sales order lines
    sales_order_line_ids = fields.One2many(
        'sale.order.line',
        compute='_compute_sales_order_lines',
        string="Sales Order Lines"
    )

    quantity = fields.Float(
        string="Quantity",
        related='invoice_line_id.quantity',
        store=True,
        readonly=True
    )

    length = fields.Float(
        string="Length",
        related='invoice_line_id.length',
        store=True,
        readonly=True
    )

    total_length = fields.Float(
        string="Tot. Length",
        related='invoice_line_id.total_length',
        store=True,
        readonly=True
    )

    weight = fields.Float(
        string="Weight",
        related='invoice_line_id.weight',
        store=True,
        readonly=True
    )

    total_weight = fields.Float(
        string="Tot. Weight",
        related='invoice_line_id.total_weight',
        store=True,
        readonly=True
    )

    uom_id = fields.Many2one(
        'uom.uom',
        string="Unit of Measure",
        related='invoice_line_id.product_uom_id',
        store=True,
        readonly=True
    )

    total_sale_amount = fields.Monetary(
        string="Total Sale Amount (Excl. Tax)",
        related='invoice_line_id.price_subtotal',
        store=True,
        readonly=True
    )
    price_total = fields.Monetary(
        string="Total Price (Incl. Tax)",
        related='invoice_line_id.price_total',
        store=True,
        readonly=True
    )

    price_unit = fields.Monetary(
        string="Total Price (Incl. Tax)",
        related='invoice_line_id.price_total',
        store=True,
        readonly=True
    )

    product_id = fields.Many2one(
        'product.product',
        string="Product",
        related='invoice_line_id.product_id',
        store=True,
        readonly=True
    )

    @api.depends('sales_order_id')
    def _compute_sales_order_lines(self):
        for rec in self:
            if rec.sales_order_id:
                rec.sales_order_line_ids = self.env['sale.order.line'].search([
                    ('order_id', '=', rec.sales_order_id.id)
                ])
            else:
                rec.sales_order_line_ids = False

    @api.depends('invoice_id.agent_id.name')
    def _compute_agent_name(self):
        for rec in self:
            rec.agent_name = rec.invoice_id.agent_id.name if rec.invoice_id and rec.invoice_id.agent_id else ''

    def unlink(self):
        """Prevent deletion of records in certain states or linked to bills"""
        for rec in self:
            if rec.state in ['billed', 'confirmed', 'audited', 'paid', 'completed']:
                raise UserError(_(
                    "Cannot delete commission record in %s state."
                ) % rec.state)
            if rec.bill_id:
                raise UserError(_(
                    "Please remove the record from bill %s before deleting."
                ) % rec.bill_id.name)
            if rec.sales_order_id:
                raise UserError(_(
                    "Commission record %s can only be removed by deleting the associated Sales Order %s."
                ) % (rec.name, rec.sales_order_id.name))
        return super().unlink()

    @api.model
    def create(self, vals):
        """Override create to handle automatic worksheet linking"""
        record = super().create(vals)
        state = vals.get('state', 'draft')
        if state in ['draft', 'checked', 'approved']:
            record._auto_assign_to_worksheet()
        return record

    def write(self, vals):
        """Complete state synchronization with proper field clearing"""
        if 'state' in vals:
            new_state = vals['state']
            current_states = {rec.id: rec.state for rec in self}

            user = self.env.user
            group_check = self.env.ref('commission_system.group_commission_check')
            group_approve = self.env.ref('commission_system.group_commission_approve')
            group_confirm = self.env.ref('commission_system.group_commission_confirm')
            group_audit = self.env.ref('commission_system.group_commission_audit')
            group_pay = self.env.ref('commission_system.group_commission_pay')

            # Prepare field updates including clearing confirmed/paid fields when reverting
            tracking_updates = {}
            for record in self:
                current_state = current_states[record.id]

                # Skip if state isn't changing
                if current_state == new_state:
                    continue

                # Add validation for completed state
                if new_state == 'completed' and current_state != 'paid':
                    raise UserError(_("Only paid commission records can be marked as completed."))

                if new_state == 'checked' and user not in group_check.users:
                    raise UserError(_("You are not allowed to check commissions."))

                if new_state == 'approved' and user not in group_approve.users:
                    raise UserError(_("You are not allowed to approve commissions."))
                if new_state == 'confirmed' and user not in group_confirm.users:
                    raise UserError(_("You are not allowed to Confirm bill commissions."))
                if new_state == 'audited' and user not in group_audit.users:
                    raise UserError(_("You are not allowed to Audit bill commissions."))

                if new_state == 'paid' and user not in group_pay.users:
                    raise UserError(_("You are not allowed to pay bill commissions."))

                # Validate transition
                allowed_transitions = {
                    'draft': ['checked'],
                    'checked': ['approved', 'draft'],
                    'approved': ['billed', 'checked'],
                    'billed': ['confirmed', 'approved', 'billed'],
                    'confirmed': ['billed', 'confirmed', 'audited'],
                    'audited': ['confirmed', 'audited', 'paid'],
                    'paid': ['completed', 'audited'],  # Allow transition to completed
                    'completed': []  # Final state
                }

                # Special case for checked->confirmed in approved worksheets
                if not (current_state == 'checked' and new_state == 'confirmed' and new_state == 'audited' and
                        record.worksheet_id and record.worksheet_id.state == 'approved'):
                    if new_state not in allowed_transitions.get(current_state, []):
                        raise UserError(_(
                            "Invalid transition from %(current)s to %(new)s.\n"
                            "Allowed: %(allowed)s"
                        ) % {
                                            'current': current_state,
                                            'new': new_state,
                                            'allowed': " → ".join(allowed_transitions[current_state])
                                        })

                # Field updates - both setting and clearing
                if new_state == 'completed':
                    tracking_updates[record.id] = {
                        # No specific user tracking for completed state
                        # as it's automatically set via bill summary
                    }
                elif new_state == 'checked':
                    tracking_updates[record.id] = {
                        'checked_by': self.env.user.id,
                        'checked_date': fields.Datetime.now(),
                        'approved_by': False,
                        'approved_date': False,
                        'confirmed_by': False,  # Clear if reverting
                        'confirmed_date': False,
                        'audited_by': False,
                        'audited_date': False,
                        'paid_by': False,
                        'paid_date': False
                    }
                elif new_state == 'approved':
                    tracking_updates[record.id] = {
                        'approved_by': self.env.user.id,
                        'approved_date': fields.Datetime.now(),
                        'confirmed_by': False,  # Clear if reverting
                        'confirmed_date': False,
                        'audited_by': False,
                        'audited_date': False,
                        'paid_by': False,
                        'paid_date': False
                    }
                elif new_state == 'confirmed':
                    tracking_updates[record.id] = {
                        'confirmed_by': self.env.user.id,
                        'confirmed_date': fields.Datetime.now(),
                        'audited_by': False,
                        'audited_date': False
                    }
                elif new_state == 'audited':
                    tracking_updates[record.id] = {
                        'audited_by': self.env.user.id,
                        'audited_date': fields.Datetime.now()
                    }
                elif new_state == 'paid':
                    tracking_updates[record.id] = {
                        'paid_by': self.env.user.id,
                        'paid_date': fields.Datetime.now()
                    }
                elif new_state == 'billed' and current_state == 'confirmed':
                    # Special handling for revert - clear confirmation fields
                    tracking_updates[record.id] = {
                        'confirmed_by': False,
                        'confirmed_date': False,
                        'audited_by': False,
                        'audited_date': False,
                        'paid_by': False,
                        'paid_date': False
                    }
                elif new_state == 'draft' and current_state == 'checked':
                    tracking_updates[record.id] = {
                        'checked_by': False,
                        'checked_date': False
                    }

            # Apply tracking updates
            for rec_id, updates in tracking_updates.items():
                rec = self.browse(rec_id)
                rec.write(updates)

        # Execute the main write operation
        result = super().write(vals)

        if 'agent_id' in vals:
            for record in self:
                if record.invoice_id:
                    record.invoice_id.write({'agent_id': vals['agent_id']})
                if record.sales_order_id:
                    record.sales_order_id.write({'agent_id': vals['agent_id']})

        # Post-write synchronization
        if 'state' in vals and not self.env.context.get('skip_sync'):
            new_state = vals['state']

            # 1. Sync with bill (if exists)
            bills = self.mapped('bill_id').filtered(lambda b: b.state != new_state)
            if bills:
                bills.with_context(skip_sync=True).write({
                    'state': new_state,
                    # Clear confirmation fields when reverting
                    **({'confirmed_by': False, 'date_confirmed': False, 'audited_by': False,
                        'audited_date': False} if new_state == 'billed' else {})
                })

            # 2. Sync with worksheet (if exists)
            worksheets = self.mapped('worksheet_id').filtered(
                lambda w: w.state != new_state
            )
            if worksheets:
                worksheets.with_context(skip_sync=True).write({
                    'state': new_state,
                    # Clear confirmation fields when reverting
                    **({'confirmed_by': False, 'confirmed_date': False, 'audited_by': False,
                        'audited_date': False} if new_state == 'billed' else {})
                })

                # Sync worksheet lines
                if hasattr(worksheets, 'line_ids'):
                    worksheets.mapped('line_ids').filtered(
                        lambda l: l.state != new_state
                    ).with_context(skip_sync=True).write({
                        'state': new_state,
                        # Clear confirmation fields when reverting
                        **({'confirmed_by': False, 'confirmed_date': False, 'audited_by': False,
                            'audited_date': False} if new_state == 'billed' else {})
                    })

            # 3. Auto-assign to worksheet if needed
            if new_state in ['checked', 'approved']:
                for record in self.filtered(lambda r: not r.worksheet_id):
                    record._auto_assign_to_worksheet()

        return result

    def _auto_assign_to_worksheet(self):
        """Automatically assign record to matching worksheet"""
        self.ensure_one()
        if not self.agent_id:
            return False

        ref_date = self.invoice_date if self.invoice_date else fields.Date.context_today(self)
        domain = [
            ('agent_id', '=', self.agent_id.id),
            ('start_date', '<=', ref_date),
            ('end_date', '>=', ref_date),
            ('state', '=', self.state)
        ]

        worksheet = self.env['commission_system.worksheet'].search(domain, limit=1)
        if worksheet:
            if not self.worksheet_id or self.worksheet_id != worksheet:
                self.write({
                    'worksheet_id': worksheet.id,
                })
                _logger.info("Auto-assigned record %s to worksheet %s", self.id, worksheet.id)
                return True
        return False

    def get_approved_records_for_agent(self, agent_id, start_date=None, end_date=None):
        """Returns approved commission records for a specific agent"""
        domain = [
            ('agent_id', '=', agent_id),
            ('state', '=', 'approved'),
            ('bill_id', '=', False)
        ]

        if start_date and end_date:
            domain.extend([
                ('invoice_date', '>=', start_date),
                ('invoice_date', '<=', end_date)
            ])

        return self.search(domain)

    def add_to_bill(self, bill_id):
        """Links commission records to a bill and updates their state"""
        if not bill_id:
            raise UserError(_("Please select a valid bill."))

        for record in self:
            if record.state != 'approved':
                raise UserError(_(
                    "Record %s is not in approved state and cannot be added to a bill."
                ) % record.name)
            if record.bill_id:
                raise UserError(_(
                    "Record %s is already linked to bill %s."
                ) % (record.name, record.bill_id.name))

        return self.write({
            'bill_id': bill_id,
            'state': 'billed'
        })

    def reset_to_approved_if_bill_deleted(self):
        """Reset state to approved when linked bill is deleted"""
        for rec in self:
            if rec.state in ['billed', 'confirmed', 'audited', 'paid', 'completed'] and (
                    not rec.bill_id or rec.bill_id.state != 'paid'):
                rec.write({
                    'state': 'approved',
                    'bill_id': False
                })
        return True

    @api.constrains('state')
    def _check_state_transition(self):
        allowed = {
            'draft': ['checked'],
            'checked': ['approved', 'draft'],
            'approved': ['billed'],
            'billed': ['confirmed'],
            'confirmed': ['audited'],
            'audited': ['paid'],
            'paid': ['completed'],
            'completed': []
        }
        for record in self:
            if record.state not in allowed:
                continue
            next_states = allowed[record.state]
            if record.state != 'completed' and not next_states:
                raise ValidationError(_(
                    "Records in %s state cannot be modified"
                ) % record.state)

    def _validate_state_transition(self, new_state):
        """Allow reverting from confirmed to billed"""
        allowed_transitions = {
            'draft': ['checked'],
            'checked': ['approved', 'draft'],
            'approved': ['billed', 'checked'],
            'billed': ['confirmed', 'approved', 'billed'],
            'confirmed': ['audited', 'confirmed', 'billed'],
            'audited': ['paid', 'confirmed', 'audited'],
            'paid': ['completed', 'audited'],  # Allow transition to completed
            'completed': []  # Final state
        }
        for record in self:
            if record.state not in allowed_transitions:
                continue
            if new_state not in allowed_transitions[record.state]:
                raise UserError(_(
                    "Cannot change record %(name)s from %(current)s to %(new)s"
                ) % {
                                    'name': record.name,
                                    'current': record.state,
                                    'new': new_state
                                })

    def _check_state_consistency(self):
        """Verify record state matches related documents"""
        for record in self:
            if record.bill_id and record.state != record.bill_id.state:
                _logger.warning(
                    "State mismatch between record %s and bill %s",
                    record.name, record.bill_id.name
                )

            if record.worksheet_id and record.state != record.worksheet_id.state:
                _logger.warning(
                    "State mismatch between record %s and worksheet %s",
                    record.name, record.worksheet_id.name
                )

    def _clear_confirmation_fields(self):
        """Utility method to clear confirmation fields"""
        return {
            'confirmed_by': False,
            'confirmed_date': False,
            'audited_by': False,
            'audited_date': False,
            'paid_by': False,
            'paid_date': False
        }

    def _validate_revert(self, new_state):
        """Additional validation for revert operations"""
        if new_state == 'billed' and self.state == 'confirmed' and self.state == 'audited':
            if any(line.payment_id for line in self.line_ids):
                raise UserError(_(
                    "Cannot revert to billed with existing payments"
                ))

    def _post_state_change_operations(self, new_state):
        """Handle all post-state-change operations"""
        # 1. Sync with worksheet
        worksheets = self.mapped('worksheet_id').filtered(
            lambda w: w.state != new_state
        )
        if worksheets:
            worksheets.with_context(skip_record_update=True).write({
                'state': new_state,
                # Ensure worksheet also clears confirmed/paid fields when reverting
                **({'confirmed_by': False, 'confirmed_date': False, 'audited_by': False,
                    'audited_date': False} if new_state == 'billed' else {})
            })

        # 2. Sync with bill
        bills = self.mapped('bill_id').filtered(
            lambda b: b.state != new_state
        )
        if bills:
            bills.with_context(skip_record_update=True).write({
                'state': new_state,
                # Clear bill confirmation fields when reverting
                **({
                       'confirmed_by': False,
                       'date_confirmed': False,
                       'audited_by': False,
                       'audited_date': False,
                       'paid_by': False,
                       'date_paid': False
                   } if new_state == 'billed' else {})
            })

        # 3. Special case - add records when approving
        if new_state == 'approved':
            for record in self.filtered(lambda r: not r.worksheet_id):
                record._auto_assign_to_worksheet()


class CommissionWorksheet(models.Model):
    _name = 'commission_system.worksheet'
    _inherit = ['base.audit.mixin', 'mail.thread', 'mail.activity.mixin']
    _description = 'Commission Worksheet'
    _order = 'sequence, name'

    # State transition rules
    STATE_TRANSITIONS = {
        'draft': ['checked', 'confirmed'],
        'checked': ['approved', 'draft'],
        'approved': ['billed', 'checked'],
        'billed': ['confirmed'],
        'confirmed': ['audited'],
        'audited': ['paid'],
        'paid': [],
    }

    LINE_STATE_TRANSITIONS = {
        'draft': ['checked'],
        'checked': ['approved', 'draft'],
        'approved': ['billed', 'checked'],
        'billed': ['confirmed', 'approved'],
        'confirmed': ['audited', 'billed'],
        'confirmed': ['paid', 'confirmed'],
        'paid': []
    }

    # Fields
    name = fields.Char(string='Worksheet Name', compute='_compute_name', store=True, readonly=False, required=True)
    salesperson_id = fields.Many2one('res.users', string='Salesperson')
    sales_team_id = fields.Many2one('crm.team', string='Sales Team')
    agent_id = fields.Many2one('res.partner', string='Agent', required=True, domain=[('is_agent', '=', True)])
    start_date = fields.Date(string='Start Date', default=lambda self: fields.Date.today().replace(day=1),
                             required=True)
    end_date = fields.Date(string='End Date', default=lambda self: fields.Date.today(), required=True)
    total_commission = fields.Float(string='Total Commission', compute='_compute_total', store=True, digits='Account')
    commission_records = fields.One2many('commission_system.records', 'worksheet_id', string='Commission Records')
    line_ids = fields.One2many('commission_system.line', 'worksheet_id', string='Commission Lines')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('checked', 'Checked'),
        ('approved', 'Approved'),
        ('billed', 'Billed'),
        ('confirmed', 'Confirmed'),
        ('audited', 'Audited'),
        ('paid', 'Paid'),
    ], string='Status', default='draft', tracking=True)
    '''checker_id = fields.Many2one('res.users', string='Checked By', readonly=True)
    approver_id = fields.Many2one('res.users', string='Approved By', readonly=True)'''
    checked_by = fields.Many2one('res.users', string="Checked By", readonly=True)
    approved_by = fields.Many2one('res.users', string="Approved By", readonly=True)
    checked_date = fields.Datetime(string='Checked On', readonly=True)
    approved_date = fields.Datetime(string='Approved On', readonly=True)
    sequence = fields.Integer(string='Sequence', default=10)
    commission_line_ids = fields.One2many(
        'commission_system.records',
        'worksheet_id',
        string='Commission Records'
    )

    _sql_constraints = [
        ('check_date_range', 'CHECK(start_date <= end_date)',
         'Start Date cannot be after End Date.'),
    ]

    # Name Generation Methods
    def _generate_name(self):
        """Generate worksheet name with unique identifier if duplicates exist"""
        self.ensure_one()
        agent_name = self.agent_id.name or "Agent"
        start_str = self.start_date.strftime('%Y-%m-%d') if self.start_date else 'Undefined'
        end_str = self.end_date.strftime('%Y-%m-%d') if self.end_date else 'Undefined'

        base_name = f"{agent_name}/{start_str}-{end_str}"

        # Check for existing worksheets with the same base name
        if self.id:  # For existing records (update case)
            existing = self.search([
                ('agent_id', '=', self.agent_id.id),
                ('start_date', '=', self.start_date),
                ('end_date', '=', self.end_date),
                ('id', '!=', self.id)
            ])
        else:  # For new records (create case)
            existing = self.search([
                ('agent_id', '=', self.agent_id.id),
                ('start_date', '=', self.start_date),
                ('end_date', '=', self.end_date)
            ])

        if existing:
            # Count how many duplicates exist (add 1 for the current one)
            duplicate_count = len(existing) + 1
            return f"{base_name}-{duplicate_count}"
        return base_name

    @api.depends('agent_id', 'start_date', 'end_date')
    def _compute_name(self):
        """Automatically update name when agent or dates change"""
        for worksheet in self:
            worksheet.name = worksheet._generate_name()

    # Constraints and Validation
    @api.constrains('agent_id', 'start_date', 'end_date')
    def _check_duplicate_worksheets(self):
        """Prevent duplicate worksheets unless existing records are paid"""
        for worksheet in self:
            existing = self.search([
                ('agent_id', '=', worksheet.agent_id.id),
                ('start_date', '=', worksheet.start_date),
                ('end_date', '=', worksheet.end_date),
                ('id', '!=', worksheet.id or False),
            ])

            for existing_ws in existing:
                if any(rec.state != 'paid' for rec in existing_ws.commission_records):
                    raise ValidationError(
                        _("A worksheet for agent %(agent)s in period %(start)s to %(end)s already exists "
                          "with non-paid commission records. Please use the existing worksheet.") % {
                            'agent': worksheet.agent_id.name,
                            'start': worksheet.start_date,
                            'end': worksheet.end_date,
                        }
                    )

    @api.model
    def create(self, vals):
        """Override create to generate initial name and check for duplicates"""
        # First create temp object to check dates
        temp_obj = self.new(vals)

        # Check for duplicates with non-paid records
        if temp_obj.agent_id and temp_obj.start_date and temp_obj.end_date:
            existing = self.search([
                ('agent_id', '=', temp_obj.agent_id.id),
                ('start_date', '=', temp_obj.start_date),
                ('end_date', '=', temp_obj.end_date),
            ])

            if existing and any(
                    rec.state != 'paid'
                    for ws in existing
                    for rec in ws.commission_records
            ):
                raise ValidationError(
                    _("A worksheet for this agent in this period already exists "
                      "with non-paid commission records. Please use the existing worksheet.")
                )

        if not vals.get('name') or vals.get('name') == 'New':
            vals['name'] = temp_obj._generate_name()

        worksheet = super().create(vals)
        worksheet._sync_lines()
        return worksheet

    '''def write(self, vals):
        """Enhanced write method with guaranteed record synchronization"""
        if 'state' in vals:
            new_state = vals['state']
            current_states = {rec.id: rec.state for rec in self}

            # Validate transitions and prepare tracking fields
            for rec in self:
                old_state = current_states[rec.id]

                if old_state == new_state:
                    continue

                # Validate the transition
                rec._validate_worksheet_transition(old_state, new_state)

                # Set tracking fields
                if new_state == 'checked':
                    if not rec.checked_by:
                        vals.setdefault('checked_by', self.env.user.id)
                        if 'checked_date' in rec._fields:
                            vals.setdefault('checked_date', fields.Datetime.now())

                elif new_state == 'approved':
                    if not rec.approved_by:
                        vals.setdefault('approved_by', self.env.user.id)
                        if 'approved_date' in rec._fields:
                            vals.setdefault('approved_date', fields.Datetime.now())

                    # Check records from both relations
                    unchecked_items = []

                    # Check commission records
                    unchecked_records = rec.commission_records.filtered(
                        lambda r: r.state != 'checked'
                    )
                    if unchecked_records:
                        # Auto-check records before approval
                        unchecked_records.write({'state': 'checked'})
                        _logger.info(
                            "Auto-checked %d records for worksheet %s",
                            len(unchecked_records), rec.name
                        )

                    # Check commission lines
                    unchecked_lines = rec.line_ids.filtered(
                        lambda r: r.state != 'checked'
                    )
                    if unchecked_lines:
                        # Auto-check lines before approval
                        unchecked_lines.write({'state': 'checked'})
                        _logger.info(
                            "Auto-checked %d lines for worksheet %s",
                            len(unchecked_lines), rec.name
                        )

                    # Add matching approved records
                    if not self.env.context.get('skip_add_records'):
                        rec._add_matching_records('approved')

        # Process the write operation with context protection
        result = super(CommissionWorksheet, self.with_context(
            skip_state_propagation=True
        )).write(vals)

        # Post-write synchronization with additional protection
        if 'state' in vals and not self.env.context.get('skip_propagation'):
            new_state = vals['state']

            for rec in self:
                # Use direct search to bypass cache issues
                domain = [('worksheet_id', '=', rec.id)]

                # Sync commission records
                records_to_sync = self.env['commission_system.records'].search(
                    domain + [('state', '!=', new_state)]
                )
                if records_to_sync:
                    records_to_sync.write({'state': new_state})

                # Sync commission lines
                if hasattr(rec, 'line_ids'):
                    lines_to_sync = rec.line_ids.filtered(
                        lambda r: r.state != new_state
                    )
                    if lines_to_sync:
                        lines_to_sync.write({'state': new_state})

                # Final approval steps
                if new_state == 'approved':
                    rec._finalize_approval()

        # Handle name changes
        if any(field in vals for field in ['agent_id', 'start_date', 'end_date']):
            self._compute_name()

        return result'''

    def write(self, vals):
        """Enhanced write method with guaranteed record synchronization"""
        if 'state' in vals:
            new_state = vals['state']
            current_states = {rec.id: rec.state for rec in self}

            # Validate transitions and prepare tracking fields
            for rec in self:
                old_state = current_states[rec.id]

                if old_state == new_state:
                    continue

                # Validate the transition
                rec._validate_worksheet_transition(old_state, new_state)

                # Set tracking fields
                if new_state == 'checked':
                    if not rec.checked_by:
                        vals.setdefault('checked_by', self.env.user.id)
                        if 'checked_date' in rec._fields:
                            vals.setdefault('checked_date', fields.Datetime.now())

                elif new_state == 'approved':
                    if not rec.approved_by:
                        vals.setdefault('approved_by', self.env.user.id)
                        if 'approved_date' in rec._fields:
                            vals.setdefault('approved_date', fields.Datetime.now())

                    # Check records from both relations
                    unchecked_records = rec.commission_records.filtered(
                        lambda r: r.state != 'checked'
                    )
                    if unchecked_records:
                        unchecked_records.write({'state': 'checked'})
                        _logger.info(
                            "Auto-checked %d records for worksheet %s",
                            len(unchecked_records), rec.name
                        )

                    # Check commission lines
                    unchecked_lines = rec.line_ids.filtered(
                        lambda r: r.state != 'checked'
                    )
                    if unchecked_lines:
                        unchecked_lines.write({'state': 'checked'})
                        _logger.info(
                            "Auto-checked %d lines for worksheet %s",
                            len(unchecked_lines), rec.name
                        )

                    # Add matching approved records
                    if not self.env.context.get('skip_add_records'):
                        rec._add_matching_records('approved')

                    # NEW: Auto-approve all checked records
                    checked_records = rec.commission_records.filtered(
                        lambda r: r.state == 'checked'
                    )
                    if checked_records:
                        checked_records.write({'state': 'approved'})
                        _logger.info(
                            "Auto-approved %d records for worksheet %s",
                            len(checked_records), rec.name
                        )

        # Process the write operation with context protection
        result = super(CommissionWorksheet, self.with_context(
            skip_state_propagation=True
        )).write(vals)

        # Post-write synchronization with additional protection
        if 'state' in vals and not self.env.context.get('skip_propagation'):
            new_state = vals['state']

            for rec in self:
                # Sync commission records (separately from lines)
                records_to_sync = rec.commission_records.filtered(
                    lambda r: r.state != new_state
                )
                if records_to_sync:
                    records_to_sync.write({'state': new_state})

                # Sync commission lines (separately from records)
                if hasattr(rec, 'line_ids'):
                    lines_to_sync = rec.line_ids.filtered(
                        lambda r: r.state != new_state
                    )
                    if lines_to_sync:
                        lines_to_sync.write({'state': new_state})

                # Final approval steps
                if new_state == 'approved':
                    rec._finalize_approval()

        # Handle name changes
        if any(field in vals for field in ['agent_id', 'start_date', 'end_date']):
            self._compute_name()

        return result

    # Commission Calculation
    @api.depends('commission_records.amount', 'line_ids.total_commission')
    def _compute_total(self):
        for worksheet in self:
            worksheet.total_commission = (
                    sum(worksheet.commission_records.mapped('amount')) +
                    sum(worksheet.line_ids.mapped('total_commission'))
            )

    # State Management Methods
    def _check_state_transition(self, old_state, new_state):
        """Validate state transition against defined rules"""
        if new_state not in self.STATE_TRANSITIONS.get(old_state, []):
            allowed = ', '.join(self.STATE_TRANSITIONS[old_state])
            raise ValidationError(
                _("Invalid transition from %(old)s to %(new)s. Allowed: %(allowed)s") % {
                    'old': old_state,
                    'new': new_state,
                    'allowed': allowed
                }
            )

    def _propagate_state_to_related(self, new_state):
        """Update state on related records"""
        self.commission_records.write({'state': new_state})
        self.line_ids.write({'state': new_state})

    def _post_state_change_updates(self, new_state):
        """Handle updates needed after state change"""
        if new_state in ['checked', 'approved', 'draft']:
            self.add_commissions_to_worksheet()
        self._sync_lines()

    # Record Synchronization Methods
    def _add_matching_records(self, state):
        """Add commission records that match the worksheet criteria"""
        self.ensure_one()
        _logger.info("Adding matching records for worksheet %s in state %s", self.name, state)

        if not self.start_date or not self.end_date:
            raise UserError(_("Start Date and End Date must be set before adding commissions."))

        domain = [
            ('state', '=', state),
            ('worksheet_id', '=', False),
            ('agent_id', '=', self.agent_id.id),
            ('create_date', '>=', self.start_date),
            ('create_date', '<=', self.end_date),
        ]

        commissions = self.env['commission_system.records'].search(domain)
        if commissions:
            commissions.write({'worksheet_id': self.id})
            self.message_post(body=_(
                "%d commission records in %s state were automatically added.") % (len(commissions), state))

    def _sync_lines(self):
        """Enhanced sync that properly handles billed records and worksheet states"""
        for worksheet in self:
            _logger.info("Syncing lines for worksheet %s (state: %s)", worksheet.name, worksheet.state)

            # Build base domain
            domain = [
                ('agent_id', '=', worksheet.agent_id.id),
                ('create_date', '>=', worksheet.start_date),
                ('create_date', '<=', worksheet.end_date),
            ]

            # Different logic based on worksheet state
            if worksheet.state == 'approved':
                # For approved worksheets, get both approved records AND checked records from approved worksheets
                domain += [
                    ('worksheet_id', '=', False),
                    '|',
                    ('state', '=', 'approved'),
                    '&',
                    ('state', '=', 'checked'),
                    ('worksheet_id.state', '=', 'approved')
                ]
            else:
                # For other states, normal sync behavior
                domain += [
                    ('worksheet_id', '=', False),
                    ('state', '=', worksheet.state)
                ]

            # Exclude records already linked to bills
            domain.append(('bill_id', '=', False))

            new_lines = self.env['commission_system.records'].search(domain)
            if new_lines:
                new_lines.write({'worksheet_id': worksheet.id})
                worksheet.message_post(body=_(
                    "%d commission records in %s state were synchronized.") % (len(new_lines), worksheet.state))

    # Business Logic Methods
    def add_commissions_to_worksheet(self):
        """Add matching commission records to this worksheet"""
        self.ensure_one()
        _logger.info("Manually adding commissions to worksheet %s", self.name)

        if self.state == 'paid':
            raise UserError(_("Cannot add commissions to a paid worksheet."))
        if not self.start_date or not self.end_date:
            raise UserError(_("Start Date and End Date must be set before adding commissions."))

        domain = [
            ('state', 'in', ['checked', 'approved']),
            ('create_date', '>=', self.start_date),
            ('create_date', '<=', self.end_date),
            ('worksheet_id', '=', False),
            ('agent_id', '=', self.agent_id.id)
        ]

        commissions = self.env['commission_system.records'].search(domain)
        if commissions:
            commissions.write({'worksheet_id': self.id})
            if not self.checked_by:
                self.checked_by = self.env.user.id
            if self.state == 'approved' and not self.approved_by:
                self.approved_by = self.env.user.id

            self.message_post(body=_(
                "%d commission records added based on worksheet state.") % len(commissions))

    # Utility Methods
    @api.model
    def _get_previous_month_range(self):
        """Get date range for previous month"""
        today = fields.Date.today()
        first_day_this_month = today.replace(day=1)
        last_day_prev_month = first_day_this_month - timedelta(days=1)
        first_day_prev_month = last_day_prev_month.replace(day=1)
        return first_day_prev_month, last_day_prev_month

    @api.model
    def generate_monthly_worksheets(self):
        """Generate worksheets for all agents for previous month"""
        start_date, end_date = self._get_previous_month_range()
        agents = self.env['res.partner'].search([('is_agent', '=', True)])

        created = self.env['commission_system.worksheet']
        for agent in agents:
            # Check if there's an existing worksheet with non-paid records
            existing = self.search([
                ('agent_id', '=', agent.id),
                ('start_date', '=', start_date),
                ('end_date', '=', end_date),
            ])

            # Only create new if no existing or all records are paid
            if not existing or all(
                    rec.state == 'paid'
                    for ws in existing
                    for rec in ws.commission_records
            ):
                worksheet = self.create({
                    'agent_id': agent.id,
                    'start_date': start_date,
                    'end_date': end_date,
                })
                created += worksheet

        if created:
            created[0].message_post(body=_(
                "%d monthly commission worksheets generated.") % len(created))

        return created

    # Action Methods
    def button_add_commissions(self):
        """Button to manually add commissions to worksheet"""
        self.ensure_one()
        self.add_commissions_to_worksheet()

    def action_set_state(self, new_state):
        """Nuclear option - guaranteed state synchronization"""
        for worksheet in self:
            if worksheet.state == new_state:
                continue

            # Validate transition
            worksheet._validate_worksheet_transition(worksheet.state, new_state)

            try:
                with self.env.cr.savepoint():
                    # SPECIAL HANDLING FOR APPROVAL
                    if new_state == 'approved':
                        # 1. Direct SQL update to avoid ORM caching issues
                        self.env.cr.execute("""
                            UPDATE commission_system_records
                            SET state = 'approved'
                            WHERE worksheet_id = %s
                            AND state IN ('checked', 'approved')
                        """, (worksheet.id,))

                        # 2. Force update any remaining records
                        self.env.cr.execute("""
                            UPDATE commission_system_records
                            SET state = 'approved'
                            WHERE worksheet_id = %s
                        """, (worksheet.id,))

                        # Invalidate cache to ensure consistency
                        worksheet.commission_records.invalidate_cache(['state'])

                    # Update worksheet with maximum context protection
                    worksheet.with_context(
                        __skip_state_update__=True,
                        __skip_worksheet_sync__=True
                    ).write({'state': new_state})

                    # Direct field updates to avoid recursion
                    if new_state == 'checked':
                        worksheet.checked_by = self.env.user.id
                    elif new_state == 'approved':
                        worksheet.approved_by = self.env.user.id

                    # Final verification for approval
                    if new_state == 'approved':
                        unapproved = worksheet.commission_records.search([
                            ('worksheet_id', '=', worksheet.id),
                            ('state', '!=', 'approved')
                        ], limit=1)
                        if unapproved:
                            raise UserError(_(
                                "Critical synchronization error detected. "
                                "Please contact support."
                            ))

            except Exception as e:
                _logger.critical(
                    "STATE TRANSITION FAILURE: %s\n%s",
                    str(e), traceback.format_exc()
                )
                raise UserError(_(
                    "System cannot complete this operation. "
                    "Technical team has been notified."
                ))

        return True

    def unlink(self):
        """Prevent deletion of paid worksheets and clean up related records"""
        if any(record.state == 'paid' for record in self):
            raise UserError(_("Cannot delete paid worksheets."))
        self.commission_records.write({'worksheet_id': False})
        return super().unlink()

    def _valid_field_parameter(self, field, name):
        """Override to allow tracking parameter on state field"""
        return name == 'tracking' or super()._valid_field_parameter(field, name)

    # Cron Job for Automatic Sync
    @api.model
    def _cron_sync_commission_records(self):
        """Regularly sync records with worksheets"""
        _logger.info("Running commission record sync cron job")
        worksheets = self.search([('state', 'in', ['checked', 'approved'])])
        for worksheet in worksheets:
            worksheet._sync_lines()
            worksheet._compute_total()

    def _sync_worksheet_from_bill(self, bill_state):
        """Sync worksheet state based on bill state"""
        state_mapping = {
            'billed': 'billed',
            'confirmed': 'confirmed',
            'audited': 'audited',
            'paid': 'paid',
            'draft': 'approved'
        }
        target_state = state_mapping.get(bill_state)
        if target_state:
            self.filtered(lambda w: w.state != target_state).write({'state': target_state})
            # Now sync the worksheet's commission records
            self._sync_worksheet_records()

    def _sync_worksheet_records(self):
        """Sync all records belonging to this worksheet"""
        for worksheet in self:
            worksheet.commission_record_ids.write({
                'state': worksheet.state
            })

    # In commission_system.worksheet model
    def _validate_state_transition(self, new_state):
        """Allow reverting from confirmed to billed"""
        allowed_transitions = {
            'draft': ['approved'],
            'approved': ['billed'],
            'billed': ['confirmed', 'billed'],  # Allow staying in billed
            'confirmed': ['audited', 'confirmed', 'billed'],  # Explicitly allow revert
            'audited': ['paid', 'confirmed', 'audited'],  # Explicitly allow revert
            'paid': ['paid', 'audited']  # Allow partial revert
        }
        for worksheet in self:
            if worksheet.state not in allowed_transitions:
                continue
            if new_state not in allowed_transitions[worksheet.state]:
                raise UserError(_(
                    "Cannot change worksheet %(name)s from %(current)s to %(new)s"
                ) % {
                                    'name': worksheet.name,
                                    'current': worksheet.state,
                                    'new': new_state
                                })

    # In commission_system.worksheet model
    def _sync_worksheet_lines(self):
        """Complete and robust line synchronization with all state transitions"""
        for worksheet in self:
            target_state = worksheet.state

            # Define ALL allowed state transitions for lines
            ALLOWED_TRANSITIONS = {
                'draft': ['checked'],
                'checked': ['approved', 'draft'],
                'approved': ['billed', 'checked'],
                'billed': ['confirmed', 'approved'],
                'confirmed': ['audited', 'billed'],
                'audited': ['paid', 'confirmed'],
                'paid': []  # Final state
            }

            # Find all lines that need updating
            updateable_lines = worksheet.line_ids.filtered(
                lambda line: (
                        line.state != target_state and  # Only if state differs
                        target_state in ALLOWED_TRANSITIONS.get(line.state, [])  # Valid transition
                )
            )

            if updateable_lines:
                try:
                    # Batch update for better performance
                    updateable_lines.write({'state': target_state})

                    _logger.info(
                        "Successfully updated %d lines to %s for worksheet %s",
                        len(updateable_lines),
                        target_state,
                        worksheet.name
                    )

                    # Post-sync validation
                    failed_lines = updateable_lines.filtered(
                        lambda l: l.state != target_state
                    )
                    if failed_lines:
                        _logger.warning(
                            "%d lines failed to update in worksheet %s",
                            len(failed_lines),
                            worksheet.name
                        )

                except Exception as e:
                    _logger.error(
                        "Critical error syncing lines for worksheet %s: %s",
                        worksheet.name,
                        str(e),
                        exc_info=True
                    )
                    # Continue with other worksheets even if one fails
                    continue

    def _validate_worksheet_transition(self, old_state, new_state):
        """Ensure valid state changes with business rules"""
        allowed = {
            'draft': ['checked'],
            'checked': ['approved', 'draft'],
            'approved': ['billed', 'checked'],
            'billed': ['confirmed', 'approved'],
            'confirmed': ['audited', 'billed'],
            'audited': ['paid', 'confirmed'],
            'paid': []
        }
        if new_state not in allowed.get(old_state, []):
            raise UserError(_(
                "Invalid worksheet transition from %(old)s to %(new)s\n"
                "Allowed: %(allowed)s"
            ) % {
                                'old': old_state,
                                'new': new_state,
                                'allowed': ' → '.join(allowed[old_state])
                            })

    '''def _finalize_approval(self):
        """Enhanced approval validation with proper error handling"""
        for worksheet in self:
            # Find all unchecked records (both in lines and commission_records)
            invalid_lines = worksheet.line_ids.filtered(
                lambda r: r.state != 'checked'
            )
            invalid_records = worksheet.commission_records.filtered(
                lambda r: r.state != 'checked'
            )

            all_invalid = invalid_lines + invalid_records

            if all_invalid:
                error_msg = _(
                    "Cannot approve worksheet with unchecked records:\n%s\n\n"
                    "Please check all records before approving."
                ) % "\n".join(all_invalid.mapped('name'))
                _logger.warning(error_msg)
                raise UserError(error_msg)

            # Additional approval business logic
            worksheet.message_post(body=_(
                "Worksheet approved by %s with %d records and %d lines"
            ) % (
                                            self.env.user.name,
                                            len(worksheet.commission_records),
                                            len(worksheet.line_ids)
                                        ))'''

    @api.constrains('state', 'commission_records.state')
    def _check_state_consistency(self):
        """State consistency check that allows during transitions"""
        if self.env.context.get('skip_state_validation'):
            return
        for ws in self:
            if ws.state == 'approved' and any(
                    r.state != 'approved'
                    for r in ws.commission_records
                    if not self.env.context.get('approving')
            ):
                raise ValidationError(_(
                    "State synchronization incomplete. "
                    "Please use the 'Sync States' button if this persists."
                ))

    '''def action_force_sync(self):
        """Manual synchronization button"""
        for ws in self:
            ws.commission_records.write({'state': ws.state})
        return {'type': 'ir.actions.client', 'tag': 'reload'}'''

    def _finalize_approval(self):
        """Final approval with context protection"""
        self.with_context(approving=True)._check_state_consistency()
        for worksheet in self:
            # 1. Auto-check any unchecked records
            unchecked_records = worksheet.commission_records.filtered(
                lambda r: r.state != 'checked'
            )

            if unchecked_records:
                unchecked_records.write({'state': 'checked'})
                _logger.info("Auto-checked %d records for worksheet %s",
                             len(unchecked_records), worksheet.name)

            # 2. Verify all records are checked
            still_unchecked = worksheet.commission_records.filtered(
                lambda r: r.state != 'checked'
            )

            if still_unchecked:
                raise UserError(_(
                    "Cannot approve - %d records still unchecked:\n%s"
                ) % (len(still_unchecked), "\n".join(still_unchecked.mapped('name'))))

            # 3. Perform the actual approval
            try:
                # Update worksheet state first
                worksheet.write({
                    'state': 'approved',
                    'approved_by': self.env.user.id,
                    'approved_date': fields.Datetime.now()
                })

                # Then update all related records
                worksheet.commission_records.write({'state': 'approved'})

                _logger.info("Successfully approved worksheet %s with %d records",
                             worksheet.name, len(worksheet.commission_records))

                worksheet.message_post(body=_(
                    "Worksheet approved by %s with %d records"
                ) % (self.env.user.name, len(worksheet.commission_records)))

            except Exception as e:
                _logger.error("Failed to approve worksheet %s: %s", worksheet.name, str(e))
                raise UserError(_(
                    "Failed to approve worksheet. Error: %s"
                ) % str(e))

    @api.constrains('state')
    def _check_approval_consistency(self):
        """Ensure approved worksheets only contain approved records"""
        for ws in self.filtered(lambda w: w.state == 'approved'):
            if ws.commission_records.filtered(lambda r: r.state != 'approved'):
                _logger.warning(
                    "Worksheet %s approved with unapproved records", ws.name
                )


class CommissionLine(models.Model):
    _name = 'commission_system.line'
    _inherit = 'base.audit.mixin'
    _description = 'Commission Line'

    name = fields.Char(string='Description')
    worksheet_id = fields.Many2one('commission_system.worksheet', ondelete='cascade')
    sale_order_id = fields.Many2one('sale.order', string='Source Sale Order', required=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('checked', 'Checked'),
        ('approved', 'Approved'),
        ('billed', 'Billed'),
        ('confirmed', 'Confirmed'),
        ('audited', 'audited'),
        ('paid', 'Paid'),
        ('completed', 'Completed')
    ], default='draft', string='Status')
    total_commission = fields.Monetary(string='Total Commission')
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    creator_id = fields.Many2one('res.users', string='Created By', default=lambda self: self.env.user)
    bill_id = fields.Many2one('commission_system.bill', string='Commission Bill', ondelete='cascade')
    amount = fields.Float(string='Amount', digits='Account')
    confirmed_by = fields.Many2one('res.users', string='Confirmed By', readonly=True)
    date_confirmed = fields.Datetime('Confirmation Date', readonly=True)
    audited_by = fields.Many2one('res.users', string='Audited By', readonly=True)
    audited_date = fields.Datetime('Audit Date', readonly=True)
    checked_by = fields.Many2one('res.users', string="Checked By", readonly=True)
    approved_by = fields.Many2one('res.users', string="Approved By", readonly=True)
    checked_date = fields.Datetime(string="Checked Date", readonly=True)
    approved_date = fields.Datetime(string='Approved On', readonly=True)

    def unlink(self):
        raise UserError("Commission lines cannot be deleted directly. Remove the related sales order to delete.")


class CommissionBill(models.Model):
    _name = 'commission_system.bill'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'base.audit.mixin']
    _description = 'Commission System Bill'
    _order = 'start_date desc, name desc'

    # State definitions
    DRAFT = 'draft'
    BILLED = 'billed'
    CONFIRMED = 'confirmed'
    AUDITED = 'audited'
    PAID = 'paid'
    COMPLETED = 'completed'
    STATES = [
        (DRAFT, 'Draft'),
        (BILLED, 'Billed'),
        (CONFIRMED, 'Confirmed'),
        (AUDITED, 'Audited'),
        (PAID, 'Paid'),
        (COMPLETED, 'Completed'),
    ]

    # Fields
    name = fields.Char(string='Bill Number', readonly=True, required=True, default='New', index=True)
    salesperson_id = fields.Many2one('res.users', string='Salesperson', compute='_compute_sales_info', store=True)
    sales_team_id = fields.Many2one('crm.team', string='Sales Team', compute='_compute_sales_info', store=True)
    agent_id = fields.Many2one('res.partner', string='Agent', required=True, domain=[('is_agent', '=', True)])
    start_date = fields.Date(string='Start Date', required=True,
                             default=lambda self: fields.Date.today().replace(day=1))
    end_date = fields.Date(string='End Date', required=True, default=fields.Date.today)
    commission_records = fields.One2many('commission_system.records', 'bill_id', string='Commission Records')
    line_ids = fields.One2many('commission_system.line', 'bill_id', string='Commission Lines')
    total_commission = fields.Float(string='Total Commission', compute='_compute_total', store=True,
                                    digits='Account')
    total_tax = fields.Float(string='Total Tax', compute='_compute_tax', store=True, digits='Account')
    tax_paid = fields.Float(string='Tax Paid So Far', default=0.0, digits='Account')
    incremental_tax = fields.Float(string='Tax for Current Period', compute='_compute_incremental_tax', store=True,
                                   digits='Account')
    net_commission = fields.Float(string='Net Commission', compute='_compute_net_commission', store=True,
                                  digits='Account')
    state = fields.Selection(STATES, string='Status', default=DRAFT, tracking=True, group_expand='_expand_states')
    created_by = fields.Many2one('res.users', string='Created By', readonly=True,
                                 default=lambda self: self.env.user)
    state_changed_by = fields.Many2one('res.users', string='State Changed By', readonly=True)
    date_billed = fields.Datetime('Billed Date', readonly=True)
    date_confirmed = fields.Datetime('Confirmation Date', readonly=True)
    audited_date = fields.Datetime('Audit Date', readonly=True)
    date_paid = fields.Datetime('Payment Date', readonly=True)
    audited_by = fields.Many2one('res.users', string='Audited By', readonly=True)
    paid_by = fields.Many2one('res.users', string='Paid By', readonly=True)
    month = fields.Char(string="Month")

    # New summary field
    summary_id = fields.Many2one('commission_system.bill.summary', string='Bill Summary', readonly=True)

    bank_name = fields.Char(string='Bank Name', related='agent_id.bank_name', readonly=True)
    iban = fields.Char(string='IBAN', related='agent_id.iban', readonly=True)
    bank_account_id = fields.Many2one(
        'res.partner.bank',
        string='Bank Account',
        related='agent_id.bank_account_id',
        readonly=True
    )

    # Add confirmed_by field for consistency
    confirmed_by = fields.Many2one('res.users', string='Confirmed By', readonly=True)

    # SQL Constraints
    _sql_constraints = [
        ('date_check', 'CHECK(start_date <= end_date)', 'Start date must be before end date.'),
        ('name_unique', 'UNIQUE(name)', 'Bill number must be unique.'),
    ]

    @api.depends('agent_id')
    def _compute_sales_info(self):
        for bill in self:
            bill.salesperson_id = bill.agent_id.user_id.id if bill.agent_id.user_id else False
            bill.sales_team_id = bill.agent_id.team_id.id if bill.agent_id.team_id else False

    @api.depends('commission_records.amount', 'line_ids.amount')
    def _compute_total(self):
        for bill in self:
            bill.total_commission = sum(bill.commission_records.mapped('amount')) + sum(
                bill.line_ids.mapped('amount'))

    @api.depends('agent_id', 'total_commission', 'start_date')
    def _compute_tax(self):
        for bill in self:
            if not bill.agent_id or not bill.total_commission:
                bill.total_tax = 0.0
                bill.tax_paid = 0.0
                bill.incremental_tax = 0.0
                continue

            # Use date range instead of month field
            domain = [
                ('state', 'in', [self.BILLED, self.CONFIRMED, self.AUDITED, self.PAID, self.COMPLETED]),
                ('agent_id', '=', bill.agent_id.id),
                ('start_date', '<', bill.start_date),  # Previous periods
            ]

            if bill.id:
                domain.append(('id', '!=', bill.id))

            prev_bills = self.search(domain)

            previous_total = sum(prev_bills.mapped('total_commission'))
            previous_tax_paid = sum(prev_bills.mapped('incremental_tax'))

            cumulative_total = previous_total + bill.total_commission
            cumulative_tax = bill._calculate_marginal_tax(cumulative_total)

            bill.total_tax = cumulative_tax
            bill.tax_paid = previous_tax_paid
            bill.incremental_tax = cumulative_tax - previous_tax_paid

    @api.depends('total_tax', 'tax_paid')
    def _compute_incremental_tax(self):
        for bill in self:
            bill.incremental_tax = bill.total_tax - bill.tax_paid

    @api.depends('total_commission', 'incremental_tax')
    def _compute_net_commission(self):
        for bill in self:
            bill.net_commission = bill.total_commission - bill.incremental_tax

    # === Tax Bracket Logic ===
    def _calculate_marginal_tax(self, amount):
        tax_brackets = self.env['commission_system.tax_bracket'].search([], order='lower_bound asc')

        if not tax_brackets:
            return 0.0

        applicable_bracket = None
        for bracket in tax_brackets:
            if amount >= bracket.lower_bound:
                applicable_bracket = bracket
            else:
                break

        if applicable_bracket:
            return (amount * (applicable_bracket.rate / 100)) - applicable_bracket.deduction
        return 0.0

    @api.model
    def create_bill_for_commission(self, agent_id, start_date, end_date, commission_lines):
        """Creates a new bill when commission arrives within the period."""
        bill = self.create({
            'agent_id': agent_id.id,
            'start_date': start_date,
            'end_date': end_date,
            'line_ids': [(0, 0, line_vals) for line_vals in commission_lines]
        })
        bill._compute_total()
        bill._compute_tax()
        bill._compute_net_commission()
        return bill

    def _get_monthly_commission_summary(self, agent_id):
        """Helper method to get the summary of commissions for an agent in the current month."""
        month_start = fields.Date.today().replace(day=1)
        this_month_bills = self.search([
            ('agent_id', '=', agent_id.id),
            ('start_date', '>=', month_start),
            ('state', '!=', 'draft')
        ])

        total_commission = sum(this_month_bills.mapped('total_commission'))
        total_tax_paid = sum(this_month_bills.mapped('tax_paid'))

        return total_commission, total_tax_paid

    @api.model
    def create(self, vals):
        """Create with enhanced error handling for worksheet records"""
        try:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self._generate_bill_name(vals)

            # Find existing bills with overlapping date ranges
            existing_bill = self._find_overlapping_bill(
                vals.get('agent_id'),
                vals.get('start_date'),
                vals.get('end_date')
            )

            if existing_bill:
                return self._merge_bills(existing_bill, vals)

            # Proceed with normal creation
            vals.update({
                'created_by': self.env.user.id,
                'state': self.DRAFT
            })
            bill = super().create(vals)

            if not self.env.context.get('install_mode') and not self.env.context.get('test_enable'):
                if not bill._auto_bill():
                    _logger.warning(f"Auto-bill failed for new bill {bill.id}")
            return bill
        except Exception as e:
            _logger.error(f"Failed to create bill: {str(e)}")
            raise UserError(_("Failed to create bill. Please check the logs for details."))

    def _sync_records_to_bill_state(self):
        """Synchronize all commission records to match bill state"""
        for bill in self:
            state_mapping = {
                self.BILLED: 'billed',
                self.CONFIRMED: 'confirmed',
                self.AUDITED: 'audited',
                self.PAID: 'paid',
                self.COMPLETED: 'completed',
                self.DRAFT: 'approved'
            }

            if bill.state in state_mapping:
                target_state = state_mapping[bill.state]
                # Only update records that need changing
                records = bill.commission_records.filtered(
                    lambda r: r.state != target_state
                )
                if records:
                    records.write({'state': target_state})

    def _validate_state_sync(self):
        """Post-transition verification"""
        mismatched_records = self.commission_records.filtered(
            lambda r: r.state != self._get_expected_record_state()
        )
        mismatched_lines = self.line_ids.filtered(
            lambda l: l.state != self._get_expected_record_state()
        )

        if mismatched_records or mismatched_lines:
            _logger.error(
                "State sync failed for Bill %s: %d records, %d lines mismatched",
                self.name,
                len(mismatched_records),
                len(mismatched_lines)
            )
            return False
        return True

    def _get_expected_record_state(self):
        """Determines what state child records should have"""
        return {
            self.BILLED: 'billed',
            self.CONFIRMED: 'confirmed',
            self.AUDITED: 'audited',
            self.PAID: 'paid',
            self.COMPLETED: 'completed',
            self.DRAFT: 'approved'
        }.get(self.state, False)

    def write(self, vals):
        if 'state' in vals:
            # Validate before writing
            self._validate_state_transition(vals['state'])

            if vals['state'] == self.CONFIRMED:
                for bill in self:
                    # Updated search domain to use correct field name
                    worksheets = self.env['commission_system.worksheet'].search([
                        ('commission_line_ids.bill_id', '=', bill.id)
                    ])

                    invalid_worksheets = worksheets.filtered(
                        lambda w: w.state != 'billed'
                    )
                    if invalid_worksheets:
                        raise UserError(_(
                            "Cannot confirm bill with worksheets not in billed state: %s"
                        ) % ", ".join(invalid_worksheets.mapped('name')))

        result = super().write(vals)

        if 'state' in vals:
            self._sync_all_related_documents()

        return result

    def _auto_bill(self):
        """Enhanced auto-bill that properly handles worksheet-approved records"""
        self.ensure_one()
        if self.state != self.DRAFT:
            return False

        # Find eligible records (both directly approved and worksheet-approved)
        domain = [
            ('agent_id', '=', self.agent_id.id),
            ('bill_id', '=', False),
            ('invoice_date', '>=', self.start_date),
            ('invoice_date', '<=', self.end_date),
            '|',
            ('state', '=', 'approved'),  # Directly approved records
            '&',
            ('state', '=', 'checked'),  # Worksheet-approved records
            ('worksheet_id.state', '=', 'approved')
        ]

        records = self.env['commission_system.records'].search(domain)
        if records:
            # First update the bill state
            self.write({
                'state': self.BILLED,
                'state_changed_by': self.env.user.id,
                'date_billed': fields.Datetime.now()
            })

            # Process records in batches to avoid state transition errors
            for record in records:
                try:
                    record.write({
                        'bill_id': self.id,
                        'state': 'billed'
                    })
                except Exception as e:
                    _logger.warning(f"Failed to update record {record.id}: {str(e)}")
                    continue

            # Sync any affected worksheets
            worksheets = records.mapped('worksheet_id').filtered(lambda w: w.state == 'approved')
            for worksheet in worksheets:
                try:
                    worksheet._sync_lines()
                except Exception as e:
                    _logger.error(f"Failed to sync worksheet {worksheet.id}: {str(e)}")

            return True
        return False

    def _generate_bill_name(self, vals):
        """Generate structured bill name: AgentName/YYYY-MM-DD-YYYY-MM-DD with duplicate handling"""
        agent = self.env['res.partner'].browse(vals.get('agent_id'))
        agent_name = agent.name or "Agent"

        start_date = fields.Date.from_string(vals.get('start_date'))
        end_date = fields.Date.from_string(vals.get('end_date'))

        start_str = start_date.strftime('%Y-%m-%d') if start_date else 'Undefined'
        end_str = end_date.strftime('%Y-%m-%d') if end_date else 'Undefined'

        base_name = f"Bill-{agent_name}/{start_str}-{end_str}"

        # Check for existing duplicates and append counter if needed
        existing = self.search_count([('name', '=like', f"{base_name}%")])
        if existing:
            return f"{base_name}-{existing + 1}"
        return base_name

    def _expand_states(self, states, domain, order):
        """Ensure all states show in status bar even when empty"""
        return [key for key, val in self.STATES]

    def action_bill(self):
        """Manual billing for draft bills"""
        for bill in self:
            if bill.state != self.DRAFT:
                raise UserError(_("Only draft bills can be billed"))
            bill._auto_bill()
        return True

    def action_confirm(self):
        """
        Confirm the commission bill and synchronize all related documents
        - Validates all prerequisites
        - Updates bill state to confirmed
        - Synchronizes worksheets, lines and commission records
        - Provides detailed error handling
        """
        for bill in self:
            # Validate bill is in correct starting state
            if bill.state != self.BILLED:
                raise UserError(_("Only billed bills can be confirmed"))

            # Find all related worksheets
            worksheets = self.env['commission_system.worksheet'].search([
                ('commission_line_ids.bill_id', '=', bill.id)
            ])

            # Pre-validate worksheets and lines
            validation_errors = []
            for worksheet in worksheets:
                if worksheet.state != 'billed':
                    validation_errors.append(
                        _("Worksheet %s must be in billed state") % worksheet.name
                    )

                invalid_lines = worksheet.line_ids.filtered(
                    lambda l: l.state not in ['billed', 'confirmed']
                )
                if invalid_lines:
                    invalid_states = ", ".join(sorted(set(
                        invalid_lines.mapped('state')
                    )))
                    validation_errors.append(
                        _("Worksheet %s has lines in invalid states: %s") % (
                            worksheet.name,
                            invalid_states
                        )
                    )

            if validation_errors:
                raise UserError("\n".join([
                    _("Cannot confirm bill due to the following issues:"),
                    *validation_errors
                ]))

            # Perform confirmation
            bill.write({
                'state': self.CONFIRMED,
                'confirmed_by': self.env.user.id,
                'date_confirmed': fields.Datetime.now(),
                'state_changed_by': self.env.user.id
            })

            # Synchronize all related documents
            try:
                bill._sync_all_related_documents()
                bill.message_post(body=_(
                    "Bill successfully confirmed. Synchronized %d worksheets and %d records."
                ) % (len(worksheets), len(bill.commission_records)))
            except Exception as e:
                _logger.error(
                    "Post-confirmation sync failed for bill %s (ID: %d): %s",
                    bill.name, bill.id, str(e),
                    exc_info=True
                )
                bill.message_post(body=_(
                    "Bill confirmed but synchronization encountered issues. "
                    "Some related documents may not have been updated. Error: %s"
                ) % str(e))

        return True

    def action_audit(self):
        """
        Audit the commission bill and synchronize all related documents
        - Validates all prerequisites
        - Updates bill state to Audited
        - Synchronizes worksheets, lines and commission records
        - Provides detailed error handling
        """
        for bill in self:
            # Validate bill is in correct starting state
            if bill.state != self.CONFIRMED:
                raise UserError(_("Only Confirmed bills can be audited"))

            # Find all related worksheets
            worksheets = self.env['commission_system.worksheet'].search([
                ('commission_line_ids.bill_id', '=', bill.id)
            ])

            # Pre-validate worksheets and lines
            validation_errors = []
            for worksheet in worksheets:
                if worksheet.state != 'confirmed':
                    validation_errors.append(
                        _("Worksheet %s must be in Confirmed state") % worksheet.name
                    )

                invalid_lines = worksheet.line_ids.filtered(
                    lambda l: l.state not in ['confirmed', 'audited']
                )
                if invalid_lines:
                    invalid_states = ", ".join(sorted(set(
                        invalid_lines.mapped('state')
                    )))
                    validation_errors.append(
                        _("Worksheet %s has lines in invalid states: %s") % (
                            worksheet.name,
                            invalid_states
                        )
                    )

            if validation_errors:
                raise UserError("\n".join([
                    _("Cannot Audit bill due to the following issues:"),
                    *validation_errors
                ]))

            # Perform confirmation
            bill.write({
                'state': self.AUDITED,
                'audited_by': self.env.user.id,
                'audited_date': fields.Datetime.now(),
                'state_changed_by': self.env.user.id
            })

            # Synchronize all related documents
            try:
                bill._sync_all_related_documents()
                bill.message_post(body=_(
                    "Bill successfully Audited. Synchronized %d worksheets and %d records."
                ) % (len(worksheets), len(bill.commission_records)))
            except Exception as e:
                _logger.error(
                    "Post-audit sync failed for bill %s (ID: %d): %s",
                    bill.name, bill.id, str(e),
                    exc_info=True
                )
                bill.message_post(body=_(
                    "Bill audited but synchronization encountered issues. "
                    "Some related documents may not have been updated. Error: %s"
                ) % str(e))

        return True

    def action_pay(self):
        """Pay the bill and trigger summary generation for monthly paid bills"""
        for bill in self:
            if bill.state != self.AUDITED:
                raise UserError(_("Only audited bills can be paid"))

            # Update bill to paid state
            bill.write({
                'state': self.PAID,
                'paid_by': self.env.user.id,
                'date_paid': fields.Datetime.now(),
                'tax_paid': bill.total_tax
            })

            # Sync commission records first
            bill._sync_records_to_bill_state()

            bill.message_post(body=_(
                "Bill marked as paid by %(user)s.<br>"
                "Updated %(records)d commission records."
            ) % {
                                       'user': self.env.user.name,
                                       'records': len(bill.commission_records)
                                   })

        # IMPORTANT: Trigger summary generation after ALL bills are processed
        # Use a delayed job or direct call to ensure it runs after commit
        self.env.cr.commit()  # Ensure paid state is saved

        # Call summary generation for all paid bills without summary
        paid_bills = self.search([
            ('state', '=', self.PAID),
            ('summary_id', '=', False)
        ])

        if paid_bills:
            _logger.info("Triggering summary generation for %d paid bills", len(paid_bills))
            paid_bills._generate_monthly_summary()

    def action_force_complete(self):
        """Manually force bills to completed state and create summary"""
        for bill in self:
            if bill.state != self.PAID:
                raise UserError(_("Only paid bills can be completed"))

            if bill.summary_id:
                raise UserError(_("Bill is already linked to a summary"))

            # Get the month range for this bill
            month_start = bill.start_date.replace(day=1)
            next_month = month_start.replace(month=month_start.month % 12 + 1,
                                             year=month_start.year + (month_start.month // 12))
            month_end = next_month - timedelta(days=1)

            # Find all paid bills in the same month for the same agent
            domain = [
                ('agent_id', '=', bill.agent_id.id),
                ('state', '=', self.PAID),
                ('summary_id', '=', False),
                ('start_date', '>=', month_start),
                ('start_date', '<=', month_end),
            ]

            paid_bills = self.search(domain)

            if paid_bills:
                # Create the summary
                summary = self._create_monthly_summary(paid_bills, month_start, month_end)
                if summary:
                    # Link bills to summary
                    paid_bills.write({'summary_id': summary.id})

                    # Update state to completed
                    paid_bills.write({'state': self.COMPLETED})

                    # Update commission records and lines
                    for paid_bill in paid_bills:
                        if paid_bill.commission_records:
                            paid_bill.commission_records.write({'state': 'completed'})
                        if paid_bill.line_ids:
                            paid_bill.line_ids.write({'state': 'completed'})

                    summary._compute_totals()

                    bill.message_post(body=_(
                        "Bill forcefully completed and added to summary %s"
                    ) % summary.name)

            else:
                raise UserError(_("No paid bills found for summary generation"))

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Force Completion'),
                'message': _('Bills have been forcefully completed and summary created.'),
                'type': 'success',
                'sticky': False,
            }
        }

    def _generate_monthly_summary(self):
        """Generate monthly summary when bills are paid and update states to completed"""
        _logger.info("=== STARTING MONTHLY SUMMARY GENERATION ===")

        # Group bills by agent and month
        bills_by_agent_month = {}

        # Find all paid bills without summary
        paid_bills = self.search([
            ('state', '=', self.PAID),
            ('summary_id', '=', False)
        ])

        _logger.info("Found %d paid bills without summary", len(paid_bills))

        if not paid_bills:
            _logger.info("No paid bills found for summary generation")
            return

        # Group bills by agent and month
        for bill in paid_bills:
            month_start = bill.start_date.replace(day=1)
            key = (bill.agent_id.id, month_start)

            if key not in bills_by_agent_month:
                bills_by_agent_month[key] = []

            bills_by_agent_month[key].append(bill)

        _logger.info("Grouped into %d agent-month combinations", len(bills_by_agent_month))

        # Process each group
        for (agent_id, month_start), bills in bills_by_agent_month.items():
            next_month = month_start.replace(month=month_start.month % 12 + 1,
                                             year=month_start.year + (month_start.month // 12))
            month_end = next_month - timedelta(days=1)

            _logger.info("Processing agent %s, month %s to %s with %d bills",
                         bills[0].agent_id.name, month_start, month_end, len(bills))

            # Create the summary
            summary = self._create_monthly_summary(bills, month_start, month_end)
            if not summary:
                _logger.error("Failed to create summary for agent %s, month %s",
                              bills[0].agent_id.name, month_start)
                continue

            _logger.info("Created summary: %s (ID: %s)", summary.name, summary.id)

            # The state update now happens in the summary's _auto_assign_bills method
            # which is called automatically after summary creation

        _logger.info("=== MONTHLY SUMMARY GENERATION COMPLETE ===")

    def _create_monthly_summary(self, bills, month_start, month_end):
        """Create a monthly bill summary - enhanced version"""
        try:
            _logger.info("Creating summary for %d bills, period %s to %s",
                         len(bills), month_start, month_end)

            # Generate base name using the first bill's agent
            agent = bills[0].agent_id if bills else None
            if not agent:
                _logger.error("No agent found for bills")
                return False

            agent_name = agent.name if agent else "Multiple"

            start_str = month_start.strftime('%Y-%m-%d')
            end_str = month_end.strftime('%Y-%m-%d')
            base_name = f"Bill-Summary-{agent_name}-{start_str}-{end_str}"

            # Check for existing summaries with same name
            existing_count = self.env['commission_system.bill.summary'].search_count([
                ('name', '=like', f"{base_name}%")
            ])

            if existing_count:
                summary_name = f"{base_name}-{existing_count + 1}"
            else:
                summary_name = base_name

            _logger.info("Creating summary with name: %s", summary_name)

            # Create the summary
            summary = self.env['commission_system.bill.summary'].create({
                'name': summary_name,
                'date_range': f"{start_str} to {end_str}",
                'start_date': month_start,
                'end_date': month_end,
                'generated_by': self.env.user.id,
            })

            _logger.info("Summary created successfully: %s (ID: %s)", summary.name, summary.id)
            return summary

        except Exception as e:
            _logger.error("Failed to create monthly summary: %s", str(e))
            _logger.error("Traceback:", exc_info=True)
            return False

    def debug_check_bill_state(self):
        """Debug method to check bill states and summary linking"""
        _logger.info("=== DEBUG BILL STATES ===")
        for bill in self:
            _logger.info("Bill: %s (ID: %s), State: %s, Summary: %s, Agent: %s",
                         bill.name, bill.id, bill.state,
                         bill.summary_id.name if bill.summary_id else 'None',
                         bill.agent_id.name)

            # Check commission records
            if bill.commission_records:
                states = bill.commission_records.mapped('state')
                state_count = {}
                for state in states:
                    state_count[state] = state_count.get(state, 0) + 1
                _logger.info("  Commission Records: %s", state_count)

            # Check commission lines
            if bill.line_ids:
                states = bill.line_ids.mapped('state')
                state_count = {}
                for state in states:
                    state_count[state] = state_count.get(state, 0) + 1
                _logger.info("  Commission Lines: %s", state_count)

    def action_complete(self):
        """Manually mark bill and records as completed (for edge cases)"""
        for bill in self:
            if bill.state != self.PAID:
                raise UserError(_("Only paid bills can be marked as completed"))

            bill.write({
                'state': self.COMPLETED
            })

            # Update commission records
            if bill.commission_records:
                bill.commission_records.write({
                    'state': 'completed'
                })

            # Update commission lines
            if bill.line_ids:
                bill.line_ids.write({
                    'state': 'completed'
                })

            bill.message_post(body=_(
                "Bill and all related records marked as completed by %s"
            ) % self.env.user.name)

        return True

    # Add a method to debug bill linking
    def debug_check_summary_linking(self):
        """Debug method to check bill-summary linking"""
        _logger.info("=== DEBUG BILL SUMMARY LINKING ===")

        # Check all completed bills
        completed_bills = self.search([('state', '=', 'completed')])
        _logger.info("Total completed bills: %d", len(completed_bills))

        for bill in completed_bills:
            _logger.info("Bill: %s (ID: %d), Summary: %s (ID: %s)",
                         bill.name, bill.id,
                         bill.summary_id.name if bill.summary_id else 'None',
                         bill.summary_id.id if bill.summary_id else 'None')

        # Check all summaries
        summaries = self.env['commission_system.bill.summary'].search([])
        _logger.info("Total summaries: %d", len(summaries))

        for summary in summaries:
            _logger.info("Summary: %s (ID: %d), Bills: %d",
                         summary.name, summary.id, len(summary.bill_ids))
            for bill in summary.bill_ids:
                _logger.info("  - Bill: %s (ID: %d)", bill.name, bill.id)

    def debug_check_summary_records(self):
        """Debug method to check commission records in summary"""
        for summary in self:
            _logger.info(f"=== DEBUG SUMMARY: {summary.name} ===")
            _logger.info(f"Total Bills: {len(summary.bill_ids)}")

            total_records = 0
            for bill in summary.bill_ids:
                record_count = len(bill.commission_records)
                total_records += record_count
                _logger.info(f"Bill {bill.name}: {record_count} commission records")

            _logger.info(f"Total Commission Records: {total_records}")
            _logger.info(f"Computed Records: {len(summary.commission_record_ids)}")

    def action_reopen(self):
        """Improved reopen method with complete field resetting - updated for COMPLETED state"""
        for bill in self:
            if bill.state == self.COMPLETED:
                # Remove from summary first
                bill.write({
                    'summary_id': False,
                    'state': self.PAID
                })

            elif bill.state == self.PAID:
                bill.commission_records.write({
                    'paid_by': False,
                    'paid_date': False,
                    'audited_by': False,
                    'audited_date': False,
                    'confirmed_by': False,
                    'confirmed_date': False,
                    'state': 'audited'
                })

                if bill.line_ids:
                    bill.line_ids.write({
                        'paid_by': False,
                        'paid_date': False,
                        'confirmed_by': False,
                        'confirmed_date': False,
                        'audited_by': False,
                        'audited_date': False,
                        'state': 'audited'
                    })

                bill.write({
                    'state': self.AUDITED,
                    'paid_by': False,
                    'date_paid': False
                })

            elif bill.state == self.AUDITED:
                bill.commission_records.write({
                    'audited_by': False,
                    'audited_date': False,
                    'state': 'confirmed'
                })

                if bill.line_ids:
                    bill.line_ids.write({
                        'audited_by': False,
                        'audited_date': False,
                        'state': 'confirmed'
                    })

                bill.write({
                    'state': self.CONFIRMED,
                    'audited_by': False,
                    'audited_date': False
                })

            elif bill.state == self.CONFIRMED:
                bill.commission_records.write({
                    'confirmed_by': False,
                    'confirmed_date': False,
                    'state': 'billed'
                })

                if bill.line_ids:
                    bill.line_ids.write({
                        'confirmed_by': False,
                        'confirmed_date': False,
                        'state': 'billed'
                    })

                bill.write({
                    'state': self.BILLED,
                    'confirmed_by': False,
                    'date_confirmed': False
                })

            elif bill.state == self.BILLED:
                bill.commission_records.write({
                    'state': 'approved',
                    'bill_id': False
                })

                if bill.line_ids:
                    bill.line_ids.write({
                        'state': 'approved',
                        'bill_id': False
                    })

                bill.state = self.DRAFT

            else:
                raise UserError(_("Cannot reopen a bill in this state"))

            bill.message_post(body=_(
                "Bill reopened from %(old_state)s to %(new_state)s by %(user)s. "
                "Updated %(records)d records and %(lines)d lines."
            ) % {
                                       'old_state': bill._fields['state'].convert_to_export(bill.state, bill),
                                       'new_state': self._fields['state'].convert_to_export(
                                           self.PAID if bill.state == self.COMPLETED else
                                           self.AUDITED if bill.state == self.PAID else
                                           self.CONFIRMED if bill.state == self.AUDITED else
                                           self.BILLED if bill.state == self.CONFIRMED else
                                           self.DRAFT,
                                           bill
                                       ),
                                       'user': self.env.user.name,
                                       'records': len(bill.commission_records),
                                       'lines': len(bill.line_ids)
                                   })

    # ========= HELPER METHODS =========
    def _validate_state_transition(self, new_state):
        """Centralized transition validation"""
        allowed_transitions = {
            self.DRAFT: [self.BILLED],
            self.BILLED: [self.CONFIRMED, self.DRAFT],
            self.CONFIRMED: [self.AUDITED, self.BILLED],
            self.AUDITED: [self.PAID, self.CONFIRMED],
            self.PAID: [self.COMPLETED, self.AUDITED],  # Allow transition to completed
            self.COMPLETED: []  # Final state, no transitions out
        }

        for bill in self:
            if new_state not in allowed_transitions.get(bill.state, []):
                raise UserError(_(
                    "Invalid transition from %(current)s to %(new)s. "
                    "Allowed: %(allowed)s"
                ) % {
                                    'current': bill.state,
                                    'new': new_state,
                                    'allowed': ', '.join(allowed_transitions[bill.state])
                                })

    def action_view_records(self):
        """View all commission records linked to this bill"""
        self.ensure_one()
        return {
            'name': _('Commission Records'),
            'type': 'ir.actions.act_window',
            'res_model': 'commission_system.records',
            'view_mode': 'tree,form',
            'domain': [('bill_id', '=', self.id)],
            'context': {'create': False},
        }

    def action_add_records(self):
        for bill in self:
            if bill.state in ['draft', 'approved']:
                # Only get records that are approved, not linked to a bill yet
                new_records = self.env['commission_system.records'].search([
                    ('state', '=', 'approved'),
                    ('agent_id', '=', bill.agent_id.id),
                    ('bill_id', '=', False),
                    ('invoice_date', '>=', bill.start_date),
                    ('invoice_date', '<=', bill.end_date),
                ])

                for rec in new_records:
                    vals = {'bill_id': bill.id}
                    # Only attempt to change state if it's not already 'billed'
                    if rec.state != 'billed':
                        vals['state'] = 'billed'
                    rec.write(vals)

    def unlink(self):
        """Override unlink to properly handle commission record states when bills are deleted"""
        for bill in self:
            # Prevent deletion of paid or completed bills
            if bill.state in [self.PAID, self.COMPLETED]:
                raise UserError(_("Cannot delete a paid or completed commission bill. Please void it instead."))

            # Reset associated commission records first
            if bill.commission_records:
                bill.commission_records.write({
                    'state': 'approved',
                    'bill_id': False
                })

            # Reset associated commission lines if they exist
            if bill.line_ids:
                bill.line_ids.write({
                    'state': 'approved',
                    'bill_id': False
                })

        return super().unlink()

    def _find_overlapping_bill(self, agent_id, start_date, end_date):
        """Find bills with overlapping date ranges for merging"""
        domain = [
            ('agent_id', '=', agent_id),
            ('state', 'in', [self.BILLED, self.CONFIRMED, self.AUDITED]),
            '|',
            '&', ('start_date', '<=', end_date), ('end_date', '>=', end_date),
            '&', ('start_date', '<=', start_date), ('end_date', '>=', start_date)
        ]
        return self.search(domain, limit=1)

    def _merge_bills(self, original_bill, new_bill_vals):
        """Enhanced merge that properly handles worksheet records"""
        # Update date range
        start_date = min(
            fields.Date.from_string(original_bill.start_date),
            fields.Date.from_string(new_bill_vals.get('start_date'))
        )
        end_date = max(
            fields.Date.from_string(original_bill.end_date),
            fields.Date.from_string(new_bill_vals.get('end_date'))
        )

        original_bill.write({
            'start_date': start_date,
            'end_date': end_date,
            'name': self._generate_merged_name(original_bill, new_bill_vals)
        })

        # Find records to merge (including worksheet-approved)
        domain = [
            ('agent_id', '=', new_bill_vals.get('agent_id')),
            ('bill_id', '=', False),
            ('invoice_date', '>=', new_bill_vals.get('start_date')),
            ('invoice_date', '<=', new_bill_vals.get('end_date')),
            '|',
            ('state', '=', 'approved'),
            '&',
            ('state', '=', 'checked'),
            ('worksheet_id.state', '=', 'approved')
        ]

        records = self.env['commission_system.records'].search(domain)
        if records:
            # Process records individually to handle state transitions
            for record in records:
                try:
                    record.write({
                        'bill_id': original_bill.id,
                        'state': original_bill.state
                    })
                except Exception as e:
                    _logger.warning(f"Failed to update record {record.id} during merge: {str(e)}")
                    continue

            # Sync worksheets
            worksheets = records.mapped('worksheet_id').filtered(lambda w: w.state == 'approved')
            for worksheet in worksheets:
                try:
                    worksheet._sync_lines()
                except Exception as e:
                    _logger.error(f"Failed to sync worksheet {worksheet.id}: {str(e)}")

        original_bill.message_post(body=_(
            "Merged with new bill for period %(start)s to %(end)s. "
            "Added %(records)d commission records (%(worksheet)d from worksheets)."
        ) % {
                                            'start': new_bill_vals.get('start_date'),
                                            'end': new_bill_vals.get('end_date'),
                                            'records': len(records),
                                            'worksheet': len([r for r in records if r.worksheet_id])
                                        })

        return original_bill

    def _generate_merged_name(self, original_bill, new_bill_vals):
        """Generate a name that reflects the merged date range"""
        agent = original_bill.agent_id
        agent_name = agent.name or "Agent"

        # Get the merged date range
        start_date = min(
            fields.Date.from_string(original_bill.start_date),
            fields.Date.from_string(new_bill_vals.get('start_date'))
        )
        end_date = max(
            fields.Date.from_string(original_bill.end_date),
            fields.Date.from_string(new_bill_vals.get('end_date'))
        )

        return f"Bill-{agent_name}/{start_date}-{end_date}"

    def _sync_all_related_documents(self):
        """Handle forced state changes during revert"""
        state_mapping = {
            self.BILLED: 'billed',
            self.CONFIRMED: 'confirmed',
            self.AUDITED: 'audited',
            self.PAID: 'paid',
            self.COMPLETED: 'completed',
            self.DRAFT: 'approved'
        }

        for bill in self:
            target_state = state_mapping.get(bill.state)
            if not target_state:
                continue

            # Use force context when reverting
            force = bill.state == self.BILLED and \
                    self._context.get('reverting', False)

            ctx = {'force_state_change': True} if force else {}

            # Process worksheets
            worksheets = self.env['commission_system.worksheet'].with_context(**ctx).search([
                ('commission_line_ids.bill_id', '=', bill.id)
            ])
            if worksheets:
                worksheets.write({'state': target_state})

                # Process records through worksheets to maintain relations
                worksheets.mapped('commission_line_ids').write({
                    'state': target_state
                })

            # Handle orphaned records
            bill.commission_records.filtered(
                lambda r: not r.worksheet_id
            ).with_context(**ctx).write({
                'state': target_state
            })

    def action_revert_to_billed(self):
        """Complete revert solution with full synchronization"""
        for bill in self:
            if bill.state != self.CONFIRMED:
                raise UserError(_("Only confirmed bills can be reverted"))

            # Validate no payments exist
            if bill.line_ids.filtered(lambda l: l.payment_id):
                raise UserError(_(
                    "Cannot revert bill with existing payments. "
                    "Please cancel payments first."
                ))

            # Update bill state first
            bill.write({
                'state': self.BILLED,
                'state_changed_by': self.env.user.id,
                'date_billed': fields.Datetime.now(),
                'confirmed_by': False,
                'date_confirmed': False
            })

            # Process in proper order: Worksheets → Records
            worksheets = self.env['commission_system.worksheet'].search([
                ('commission_line_ids.bill_id', '=', bill.id)
            ])

            # Update worksheets with safe_write to bypass validation if needed
            worksheets.with_context(force_state_change=True).write({
                'state': 'billed'
            })

            # Update all related records
            bill.commission_records.with_context(force_state_change=True).write({
                'state': 'billed'
            })

            bill.message_post(body=_(
                "Bill and all related documents reverted to billed by %s"
            ) % self.env.user.name)

        return True

    def print_report(self):
        """Generate the PDF report with proper error handling"""
        try:
            report = self.env.ref('commission_system.action_report_commission_bill')
            if not report:
                raise UserError(_("Report template not found. Please contact your administrator."))

            # Ensure we're passing the IDs correctly
            return report.report_action(self.ids)
        except Exception as e:
            raise UserError(_("Failed to generate report: %s") % str(e))

    def preview_report(self):
        """Preview with better error handling"""
        report_action = self.print_report()
        report_action['target'] = 'new'
        return report_action

    def _compute_display_name(self):
        """Override display name for better PDF filename"""
        for bill in self:
            bill.display_name = f"Commission_Bill_{bill.name}_{bill.start_date}_{bill.end_date}"

    def action_generate_monthly_summary(self):
        """Manual action to generate monthly summary for paid bills"""
        for bill in self:
            if bill.state != self.PAID:
                raise UserError(_("Only paid bills can be included in monthly summaries"))

            bill._generate_monthly_summary()

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Summary Generation'),
                'message': _('Monthly summary generation initiated for paid bills.'),
                'type': 'success',
                'sticky': False,
            }
        }

    # === CONSTRAINTS ===
    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for bill in self:
            if bill.start_date > bill.end_date:
                raise ValidationError(_("Start date must be before end date."))
            if bill.end_date > fields.Date.today():
                raise ValidationError(_("End date cannot be in the future."))

    @api.constrains('agent_id')
    def _check_agent_commissionable(self):
        for bill in self:
            if bill.agent_id and not bill.agent_id.is_agent:
                raise ValidationError(_("Selected partner is not configured as an agent."))

    def action_view_summary(self):
        """View the bill summary associated with this bill"""
        self.ensure_one()
        if not self.summary_id:
            raise UserError(_("This bill is not associated with any summary."))
        return {
            'name': _('Bill Summary'),
            'type': 'ir.actions.act_window',
            'res_model': 'commission_system.bill.summary',
            'view_mode': 'form',
            'res_id': self.summary_id.id,
            'context': {'create': False},
        }

    def debug_bill_summary_creation(self):
        """Debug method to check bill summary creation process"""
        _logger.info("=== DEBUG BILL SUMMARY CREATION ===")

        paid_bills = self.search([('state', '=', 'paid')])
        _logger.info("Found %d paid bills without summary", len(paid_bills))

        for bill in paid_bills:
            _logger.info("Bill: %s (ID: %s), Agent: %s, Start Date: %s",
                         bill.name, bill.id, bill.agent_id.name, bill.start_date)

            # Check if bill should be in a summary
            month_start = bill.start_date.replace(day=1)
            next_month = month_start.replace(month=month_start.month % 12 + 1,
                                             year=month_start.year + (month_start.month // 12))
            month_end = next_month - timedelta(days=1)

            domain = [
                ('agent_id', '=', bill.agent_id.id),
                ('state', '=', 'paid'),
                ('summary_id', '=', False),
                ('start_date', '>=', month_start),
                ('start_date', '<=', month_end),
            ]

            matching_bills = self.search(domain)
            _logger.info("  Would create summary with %d bills for period %s to %s",
                         len(matching_bills), month_start, month_end)

        # Check existing summaries
        summaries = self.env['commission_system.bill.summary'].search([])
        _logger.info("=== EXISTING SUMMARIES ===")
        for summary in summaries:
            _logger.info("Summary: %s (ID: %s), Bills: %d",
                         summary.name, summary.id, len(summary.bill_ids))
            for bill in summary.bill_ids:
                _logger.info("  - Bill: %s, State: %s", bill.name, bill.state)

    def action_fix_completed_state(self):
        """Manually fix bills that have summaries but are not in completed state"""
        _logger.info("=== FIXING COMPLETED STATE ===")

        # Find bills that have summaries but are not completed
        bills_to_fix = self.search([
            ('summary_id', '!=', False),
            ('state', '!=', self.COMPLETED)
        ])

        _logger.info("Found %d bills with summaries but wrong state", len(bills_to_fix))

        fixed_count = 0
        for bill in bills_to_fix:
            _logger.info("Fixing bill: %s (Current state: %s, Summary: %s)",
                         bill.name, bill.state, bill.summary_id.name)

            # Update bill state to completed
            bill.write({
                'state': self.COMPLETED
            })

            # Update commission records
            if bill.commission_records:
                bill.commission_records.write({'state': 'completed'})

            # Update commission lines
            if bill.line_ids:
                bill.line_ids.write({'state': 'completed'})

            fixed_count += 1
            _logger.info("Fixed bill %s", bill.name)

        _logger.info("Fixed %d bills", fixed_count)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('State Fix Complete'),
                'message': _('Fixed %d bills with incorrect states') % fixed_count,
                'type': 'success',
                'sticky': False,
            }
        }

class CommissionBillReport(models.AbstractModel):
    _name = 'report.commission_system.report_commission_bill'
    _description = 'Commission Bill Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['commission_system.bill'].browse(docids)
        company = self.env.company

        # Ensure logo is properly formatted
        logo = company.logo and company.logo.decode('utf-8') if isinstance(company.logo, bytes) else company.logo

        def format_amount(amount):
            return self.env['ir.qweb.field.monetary'].value_to_html(
                amount,
                {'display_currency': company.currency_id}
            )

        def format_date(date):
            if not date:
                return ''
            return fields.Date.to_string(date)

        def get_company_address(company):
            address = []
            if company.street: address.append(company.street)
            if company.street2: address.append(company.street2)
            city_line = []
            if company.city: city_line.append(company.city)
            if company.state_id: city_line.append(company.state_id.name)
            if company.zip: city_line.append(company.zip)
            if company.country_id: city_line.append(company.country_id.name)
            if city_line: address.append(', '.join(filter(None, city_line)))
            return address

        return {
            'doc_ids': docids,
            'doc_model': 'commission_system.bill',
            'docs': docs,
            'doc': docs[0] if docs else None,
            'company': company,
            'format_amount': format_amount,
            'format_date': format_date,
            'get_company_address': get_company_address,
            'company_logo': logo,  # Pass the decoded logo
            'today': fields.Date.today(),
        }


class CommissionReport(models.Model):
    _name = "commission_system.report"
    _description = "Commission Report"
    _auto = False
    _rec_name = 'invoice_date'

    salesperson_id = fields.Many2one('res.users', string="Salesperson")
    agent_id = fields.Many2one('res.partner', string="Agent")
    sales_team_id = fields.Many2one('crm.team', string="Sales Team")
    rule_id = fields.Many2one('commission_system.rules', string="Commission Rule")
    product_id = fields.Many2one('product.product', string="Product")
    product_category_id = fields.Many2one('product.category', string="Product Category")
    invoice_date = fields.Date(string="Invoice Date")
    total_sales = fields.Float(string="Total Sales")
    total_commission = fields.Float(string="Total Commission")
    average_commission = fields.Float(string="Average Commission")
    commission_rate = fields.Float(string="Commission Rate")
    num_sales = fields.Integer(string="Number of Sales")
    net_revenue = fields.Float(string="Net Revenue")
    customer_id = fields.Many2one('res.partner', string="Customer")

    # Custom Date Range Filters
    custom_start_date = fields.Date(string="Start Date")
    custom_end_date = fields.Date(string="End Date")

    def init(self):
        tools.drop_view_if_exists(self.env.cr, 'commission_system_report')
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW commission_system_report AS (
                SELECT
                    MIN(cr.id) AS id,
                    cr.salesperson_id,
                    cr.agent_id,
                    cr.sales_team_id,
                    cr.rule_id,
                    i.partner_id AS customer_id,
                    i.invoice_date,
                    SUM(aml.price_subtotal) AS total_sales,  -- Per product line
                    SUM(cr.amount) AS total_commission,
                    COUNT(cr.id) AS num_sales,
                    COALESCE(SUM(cr.amount) / NULLIF(COUNT(cr.id), 0), 0) AS average_commission,
                    CASE 
                        WHEN SUM(aml.price_subtotal) > 0 
                        THEN (SUM(cr.amount) / SUM(aml.price_subtotal)) * 100 
                        ELSE 0 
                    END AS commission_rate,
                    SUM(aml.price_subtotal) - SUM(cr.amount) AS net_revenue,
                    cr.product_id,
                    pt.categ_id AS product_category_id
                FROM commission_system_records cr
                LEFT JOIN product_product p ON cr.product_id = p.id
                LEFT JOIN product_template pt ON p.product_tmpl_id = pt.id
                LEFT JOIN account_move i ON cr.invoice_id = i.id
                LEFT JOIN account_move_line aml ON aml.move_id = i.id AND aml.product_id = cr.product_id
                WHERE i.state = 'posted'
                GROUP BY 
                    cr.salesperson_id,
                    cr.agent_id,
                    cr.sales_team_id,
                    cr.rule_id,
                    i.partner_id,
                    i.invoice_date,
                    cr.product_id,
                    pt.categ_id
                        )

                    """)

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        ctx = self.env.context or {}

        # Custom date filters from context
        custom_start_date = ctx.get('custom_start_date')
        custom_end_date = ctx.get('custom_end_date')

        if ctx.get('search_default_today'):
            date_domain = self._get_date_filter('today')
        elif ctx.get('search_default_this_week'):
            date_domain = self._get_date_filter('this_week')
        elif ctx.get('search_default_this_month'):
            date_domain = self._get_date_filter('this_month')
        elif ctx.get('search_default_this_year'):
            date_domain = self._get_date_filter('this_year')
        elif custom_start_date and custom_end_date:
            date_domain = self._get_date_filter('custom', custom_start_date, custom_end_date)
        else:
            date_domain = []

        args = date_domain + args
        return super(CommissionReport, self).search(args, offset=offset, limit=limit, order=order, count=count)

    def _get_date_filter(self, active_filter, start_date=None, end_date=None):
        today = fields.Date.today()

        if active_filter == 'today':
            return [('invoice_date', '=', today)]
        elif active_filter == 'this_week':
            start_of_week = today - timedelta(days=today.weekday())
            return [('invoice_date', '>=', start_of_week)]
        elif active_filter == 'this_month':
            start_of_month = today.replace(day=1)
            return [('invoice_date', '>=', start_of_month)]
        elif active_filter == 'this_year':
            start_of_year = today.replace(month=1, day=1)
            return [('invoice_date', '>=', start_of_year)]
        elif active_filter == 'custom' and start_date and end_date:
            return [('invoice_date', '>=', start_date), ('invoice_date', '<=', end_date)]
        return []

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        ctx = self.env.context or {}
        custom_start_date = ctx.get('custom_start_date')
        custom_end_date = ctx.get('custom_end_date')

        if ctx.get('search_default_today'):
            domain = self._get_date_filter('today') + domain
        elif ctx.get('search_default_this_week'):
            domain = self._get_date_filter('this_week') + domain
        elif ctx.get('search_default_this_month'):
            domain = self._get_date_filter('this_month') + domain
        elif ctx.get('search_default_this_year'):
            domain = self._get_date_filter('this_year') + domain
        elif custom_start_date and custom_end_date:
            domain = self._get_date_filter('custom', custom_start_date, custom_end_date) + domain

        return super().read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)


class CommissionSystemIndexes(models.Model):
    _name = "commission_system.indexes"
    _auto = False

    @api.model
    def init(self):
        indexes = [
            ("idx_commission_salesperson", "commission_system_records", "salesperson_id"),
            ("idx_commission_agent", "commission_system_records", "agent_id"),
            ("idx_commission_sales_team", "commission_system_records", "sales_team_id"),
            ("idx_commission_rule", "commission_system_records", "rule_id"),
            ("idx_commission_product", "commission_system_records", "product_id"),
            ("idx_invoice_date", "account_move", "invoice_date"),
            ("idx_product_category", "product_template", "categ_id"),
        ]

        for index_name, table, column in indexes:
            try:
                self.env.cr.execute(
                    f"CREATE INDEX IF NOT EXISTS {index_name} ON {table} ({column});"
                )
                _logger.info(f"Index {index_name} created successfully on {table}({column}).")
            except Exception as e:
                _logger.error(f"Failed to create index {index_name} on {table}({column}): {e}")


class UserActivityLog(models.Model):
    _name = 'commission_system.user_activity_log'
    _description = 'User Activity Log'
    _order = 'create_date desc'

    user_id = fields.Many2one('res.users', string="User", required=True, default=lambda self: self.env.user)
    action = fields.Selection([
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('login', 'Login'),
        ('logout', 'Logout'),
    ], string="Action", required=True)
    model_name = fields.Char(string="Model Name")
    record_id = fields.Integer(string="Record ID", default=None)
    description = fields.Text(string="Description")
    ip_address = fields.Char(string="IP Address")
    timestamp = fields.Datetime(string="Timestamp", default=fields.Datetime.now)

    def get_user_ip(self):
        return self.env.context.get('ip_address', 'Unknown')


class ResUsers(models.Model):
    _inherit = 'res.users'

    @classmethod
    def authenticate(cls, db, login, password, user_agent_env):
        """Override authentication to log user login events."""
        uid = super().authenticate(db, login, password, user_agent_env)

        if uid:
            request.env['commission_system.user_activity_log'].sudo().create({
                'user_id': uid,
                'action': 'login',
                'description': _('User logged in'),
                'ip_address': request.httprequest.remote_addr if request else 'Unknown',
            })

        return uid


class CommissionTaxBracket(models.Model):
    _name = 'commission_system.tax_bracket'
    _description = 'Commission Tax Bracket'
    _order = 'lower_bound asc'  # Ensure correct order for calculation

    lower_bound = fields.Float(string='Lower Bound', required=True)
    upper_bound = fields.Float(string='Upper Bound', required=True)
    rate = fields.Float(string='Tax Rate (%)', required=True)
    deduction = fields.Float(string='Deduction Amount', required=True)

    @api.constrains('lower_bound', 'upper_bound')
    def _check_bounds(self):
        for record in self:
            if record.lower_bound >= record.upper_bound:
                raise ValidationError("The lower bound must be less than the upper bound.")


class CommissionBillSummary(models.Model):
    _name = 'commission_system.bill.summary'
    _description = 'Commission Bill Summary'
    _order = 'create_date desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Summary Name', required=True, readonly=True, default=lambda self: _('New'))

    # CHANGE 1: Update date_range field
    date_range = fields.Char(string='Date Range', compute='_compute_date_range', store=True)  # CHANGED LINE
    start_date = fields.Date(string='Start Date', required=True)
    end_date = fields.Date(string='End Date', required=True)
    bill_ids = fields.One2many('commission_system.bill', 'summary_id', string='Bills', readonly=True)

    # REMOVE commission record fields - we don't need them in summary
    total_commission = fields.Float(string='Total Commission', compute='_compute_totals', store=True, digits='Account')
    total_tax = fields.Float(string='Total Tax', compute='_compute_totals', store=True, digits='Account')
    total_net_commission = fields.Float(string='Total Net Commission', compute='_compute_totals', store=True,
                                        digits='Account')
    bill_count = fields.Integer(string='Number of Bills', compute='_compute_totals', store=True)
    generated_by = fields.Many2one('res.users', string='Generated By', readonly=True,
                                   default=lambda self: self.env.user)
    generated_date = fields.Datetime(string='Generated Date', readonly=True, default=fields.Datetime.now)

    # CHANGE 2: Fix the compute method dependencies
    @api.depends('bill_ids', 'bill_ids.total_commission', 'bill_ids.total_tax',
                 'bill_ids.net_commission')  # CHANGED LINE
    def _compute_totals(self):
        """Compute totals from all bills in the summary"""
        for summary in self:
            bills = summary.bill_ids
            summary.total_commission = sum(bills.mapped('total_commission'))
            summary.total_tax = sum(bills.mapped('total_tax'))
            summary.total_net_commission = sum(bills.mapped('net_commission'))
            summary.bill_count = len(bills)  # This should now work correctly

    # CHANGE 3: Add new compute method for date_range
    @api.depends('start_date', 'end_date')  # NEW METHOD
    def _compute_date_range(self):
        for summary in self:
            if summary.start_date and summary.end_date:
                summary.date_range = f"{summary.start_date} to {summary.end_date}"
            else:
                summary.date_range = False

    # CHANGE 4: Add auto-assign bills method
    def _auto_assign_bills(self):
        """Automatically find and assign bills to this summary based on date range AND update their state"""
        for summary in self:
            _logger.info("=== Auto-assigning bills for summary: %s ===", summary.name)

            # Find bills that match the summary date range and are paid
            domain = [
                ('state', '=', 'paid'),  # Only paid bills
                ('summary_id', '=', False),  # Not already assigned to a summary
                ('start_date', '>=', summary.start_date),
                ('start_date', '<=', summary.end_date),
            ]

            bills_to_link = self.env['commission_system.bill'].search(domain)
            _logger.info("Found %d bills to link", len(bills_to_link))

            if bills_to_link:
                # CRITICAL: Update bills - link to summary AND change state in one operation
                bills_to_link.write({
                    'summary_id': summary.id,
                    'state': 'completed'  # This is the key line that's missing
                })

                _logger.info("Auto-assigned %d bills to summary %s and updated state to completed",
                             len(bills_to_link), summary.name)

                # Also update all commission records to 'completed' state
                record_count = 0
                line_count = 0
                for bill in bills_to_link:
                    # Update commission records
                    if bill.commission_records:
                        bill.commission_records.write({
                            'state': 'completed'
                        })
                        record_count += len(bill.commission_records)

                    # Update commission lines
                    if bill.line_ids:
                        bill.line_ids.write({
                            'state': 'completed'
                        })
                        line_count += len(bill.line_ids)

                _logger.info("Updated %d commission records and %d commission lines to completed state",
                             record_count, line_count)

                # Force recompute of totals
                summary._compute_totals()

    @api.model
    def create(self, vals):
        """Override create to generate unique name if not provided"""
        if vals.get('name', _('New')) == _('New'):
            # Generate name based on date range
            if vals.get('start_date') and vals.get('end_date'):
                start_date = fields.Date.from_string(vals.get('start_date'))
                end_date = fields.Date.from_string(vals.get('end_date'))
                date_range = f"{start_date.strftime('%Y-%m-%d')}-{end_date.strftime('%Y-%m-%d')}"
                base_name = f"Bill-Summary-{date_range}"

                # Check for duplicates
                existing_count = self.search_count([('name', '=like', f"{base_name}%")])
                if existing_count:
                    vals['name'] = f"{base_name}-{existing_count + 1}"
                else:
                    vals['name'] = base_name
            else:
                # Fallback name
                vals['name'] = f"Bill-Summary-{fields.Datetime.now().strftime('%Y%m%d-%H%M%S')}"

        summary = super().create(vals)

        # Auto-assign bills after creation AND update their state
        summary._auto_assign_bills()  # This now includes state update

        summary.message_post(body=_(
            "Bill summary created for period %s. Assigned %d bills and updated them to completed state."
        ) % (summary.date_range, len(summary.bill_ids)))
        return summary


    def action_view_bills(self):
        """View all bills included in this summary"""
        self.ensure_one()
        return {
            'name': _('Bills in Summary - %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'commission_system.bill',
            'view_mode': 'tree,form',
            'domain': [('summary_id', '=', self.id)],
            'context': {'create': False},
            'target': 'current',
        }

    # CHANGE 6: Add manual assign action
    def action_assign_bills(self):  # NEW METHOD
        """Manual action to assign bills to this summary"""
        self.ensure_one()
        self._auto_assign_bills()

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Bills Assigned'),
                'message': _('Assigned %d bills to summary %s') % (len(self.bill_ids), self.name),
                'type': 'success',
                'sticky': False,
            }
        }

    # CHANGE 7: Add debug method
    def action_debug_summary(self):  # NEW METHOD
        """Debug method to check summary state"""
        self.ensure_one()
        _logger.info("=== Debug Summary %s ===", self.name)
        _logger.info("Bills count: %d", len(self.bill_ids))
        _logger.info("Bill IDs: %s", self.bill_ids.ids)

        # Check for bills that should be assigned
        domain = [
            ('state', '=', 'completed'),
            ('summary_id', '=', False),
            ('start_date', '>=', self.start_date),
            ('start_date', '<=', self.end_date),
        ]
        available_bills = self.env['commission_system.bill'].search(domain)
        _logger.info("Available bills to assign: %d", len(available_bills))
        _logger.info("Available bill IDs: %s", available_bills.ids)

    def unlink(self):
        """Prevent deletion if bills are linked"""
        for summary in self:
            if summary.bill_ids:
                raise UserError(
                    _("Cannot delete a summary that has bills linked to it. Please unlink the bills first."))
        return super().unlink()

    def action_fix_bill_linking(self):
        """Manual action to fix bill linking for existing summaries"""
        for summary in self:
            # Find all completed bills for this summary's date range and agent
            if summary.bill_ids:
                _logger.info("Summary %s already has %d bills", summary.name, len(summary.bill_ids))
                continue

            # Find bills that should be in this summary
            domain = [
                ('state', '=', 'completed'),
                ('summary_id', '=', False),
                ('start_date', '>=', summary.start_date),
                ('start_date', '<=', summary.end_date),
            ]

            # If we have bills in summary, use the same agent
            if summary.bill_ids:
                agent_id = summary.bill_ids[0].agent_id.id
                domain.append(('agent_id', '=', agent_id))

            bills_to_link = self.env['commission_system.bill'].search(domain)

            if bills_to_link:
                bills_to_link.write({'summary_id': summary.id})
                summary._compute_totals()
                _logger.info("Linked %d bills to summary %s", len(bills_to_link), summary.name)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Bill Linking Fixed'),
                'message': _('Bill linking has been updated for all summaries.'),
                'type': 'success',
                'sticky': False,
            }
        }

    def action_create_test_bill(self):
        """Create a test bill for debugging"""
        self.ensure_one()

        Bill = self.env['commission_system.bill']

        # Create a test bill that should match our criteria
        test_bill = Bill.create({
            'name': f"TEST-BILL-{fields.Datetime.now().strftime('%Y%m%d-%H%M%S')}",
            'start_date': self.start_date,  # Use the same date as summary
            'state': 'completed',
            'total_commission': 100.0,
            'total_tax': 10.0,
            'net_commission': 90.0,
            # Don't set summary_id - let it be auto-assigned
        })

        _logger.info("Created test bill: %s (ID: %s)", test_bill.name, test_bill.id)

        # Now try to auto-assign
        self._auto_assign_bills()

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Test Bill Created'),
                'message': _('Created test bill and attempted auto-assignment. Check logs.'),
                'type': 'info',
                'sticky': True,
            }
        }

    def action_test_connection(self):
        """Simple test method to verify the model works"""
        self.ensure_one()
        _logger.info("=== TEST METHOD CALLED ===")
        _logger.info("Summary: %s (ID: %s)", self.name, self.id)
        _logger.info("Bills count: %d", len(self.bill_ids))

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Test Successful'),
                'message': _('Test method called successfully. Bills count: %d') % len(self.bill_ids),
                'type': 'success',
                'sticky': False,
            }
        }

    def action_manual_assign(self):
        """Manual action to assign bills"""
        self.ensure_one()
        self._auto_assign_bills()

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Bills Assigned'),
                'message': _('Assigned bills to summary. Total bills: %d') % len(self.bill_ids),
                'type': 'success',
                'sticky': False,
            }
        }

    def action_update_bill_states(self):
        """Manually update all bills in this summary to completed state"""
        for summary in self:
            if not summary.bill_ids:
                _logger.info("No bills in summary %s", summary.name)
                continue

            _logger.info("Updating %d bills in summary %s to completed state",
                         len(summary.bill_ids), summary.name)

            # Update bill states to completed
            summary.bill_ids.write({
                'state': 'completed'
            })

            # Update commission records and lines
            record_count = 0
            line_count = 0
            for bill in summary.bill_ids:
                if bill.commission_records:
                    bill.commission_records.write({'state': 'completed'})
                    record_count += len(bill.commission_records)
                if bill.line_ids:
                    bill.line_ids.write({'state': 'completed'})
                    line_count += len(bill.line_ids)

            _logger.info("Updated %d bills, %d records, %d lines to completed state",
                         len(summary.bill_ids), record_count, line_count)

            summary.message_post(body=_(
                "Manually updated %d bills and their commission records (%d records, %d lines) to completed state."
            ) % (len(summary.bill_ids), record_count, line_count))

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('State Update Complete'),
                'message': _('Updated all bills in summary to completed state.'),
                'type': 'success',
                'sticky': False,
            }
        }