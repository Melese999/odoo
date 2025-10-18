# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.tools.safe_eval import safe_eval
from datetime import timedelta
import logging

_logger = logging.getLogger(__name__)

class KpiTarget(models.Model):
    _name = 'kpi.target'
    _description = 'KPI Target Assignment'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Name', compute='_compute_name', store=True, readonly=True)
    kpi_id = fields.Many2one(
        'kpi.definition',
        string='KPI',
        required=True,
        ondelete='cascade',
        #inverse_name='target_ids'  # Ensure this matches the field name in kpi.definition
    )
    user_id = fields.Many2one('res.users', string='Assigned To', required=True, tracking=True)

    date_start = fields.Date(string='Start Date', required=True)
    date_end = fields.Date(string='End Date', required=True)

    target_value = fields.Float(string='Target Value', required=True, tracking=True)

    holiday_schedule_id = fields.Many2one(
        'holiday.schedule',
        string='Holiday Schedule',
        help="Select a holiday calendar to calculate the number of working days for this target period."
    )
    working_days = fields.Integer(
        string='Working Days',
        compute='_compute_working_days',
        store=True,
        help="Calculated number of working days in the period, excluding weekends and selected holidays."
    )

    actual_value = fields.Float(string='Actual Value', readonly=True, help="The latest automatically calculated value.")
    achievement_percentage = fields.Float(
        string='Achievement (%)',
        compute='_compute_achievement',
        store=True,
        readonly=True
    )
    last_computed_date = fields.Datetime(string='Last Computed On', readonly=True)

    history_ids = fields.One2many('kpi.history', 'target_id', string='Activity History')
    activity_count = fields.Integer(string="Activity Count", compute='_compute_activity_count')

    @api.depends('kpi_id.name', 'user_id.name', 'date_start', 'date_end')
    def _compute_name(self):
        for record in self:
            if record.kpi_id and record.user_id and record.date_start and record.date_end:
                record.name = f"{record.kpi_id.name} for {record.user_id.name} ({record.date_start.strftime('%b %Y')})"
            else:
                record.name = "New KPI Target"

    @api.depends('actual_value', 'target_value')
    def _compute_achievement(self):
        for record in self:
            if record.target_value > 0:
                record.achievement_percentage = (record.actual_value / record.target_value) * 100
            else:
                record.achievement_percentage = 0.0

    @api.depends('date_start', 'date_end', 'holiday_schedule_id.line_ids.date')
    def _compute_working_days(self):
        for target in self:
            if not target.date_start or not target.date_end:
                target.working_days = 0
                continue
            holiday_dates = set(target.holiday_schedule_id.line_ids.mapped('date')) if target.holiday_schedule_id else set()
            working_days_count = 0
            current_date = target.date_start
            while current_date <= target.date_end:
                if current_date.weekday() < 5 and current_date not in holiday_dates:
                    working_days_count += 1
                current_date += timedelta(days=1)
            target.working_days = working_days_count

    @api.depends('history_ids')
    def _compute_activity_count(self):
        for target in self:
            target.activity_count = len(target.history_ids)

    def action_view_activities(self):
        self.ensure_one()
        source_models = self.history_ids.mapped('source_document_model')
        if not source_models:
            return {}

        res_model = source_models[0]
        source_ids = self.history_ids.mapped('source_document_id')

        return {
            'name': _('Tracked Activities for %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': res_model,
            'view_mode': 'tree,form',
            'domain': [('id', 'in', source_ids)],
            'target': 'current',
        }

    def _recalculate_values(self):
        for target in self:
            kpi = target.kpi_id
            if not all([kpi.target_model_id, kpi.user_field_id, kpi.date_field_id]):
                _logger.warning(f"KPI Definition '{kpi.name}' is incomplete. Skipping target ID {target.id}.")
                continue

            primary_model_name = kpi.target_model_id.model
            user_field_name = kpi.user_field_id.name
            date_field_name = kpi.date_field_id.name
            date_field_type = kpi.date_field_id.ttype

            date_from = fields.Datetime.start_of(target.date_start, 'day') if date_field_type == 'datetime' else target.date_start
            date_to = fields.Datetime.end_of(target.date_end, 'day') if date_field_type == 'datetime' else target.date_end

            primary_domain = [
                (user_field_name, '=', target.user_id.id),
                (date_field_name, '>=', date_from),
                (date_field_name, '<=', date_to),
            ]

            found_records = self.env[primary_model_name].browse()
            activity_date_field = date_field_name

            try:
                primary_records = self.env[primary_model_name].search(primary_domain)

                if kpi.computation_method == 'count_records':
                    found_records = primary_records

                elif kpi.computation_method == 'sum_field':
                    if kpi.sum_field_id and primary_records:
                        sum_field_name = kpi.sum_field_id.name
                        calculated_value = sum(primary_records.mapped(sum_field_name))
                        target.write({'actual_value': calculated_value, 'last_computed_date': fields.Datetime.now()})
                        continue  # Skip history creation for sum

                elif kpi.computation_method == 'count_related_records':
                    if kpi.related_model_id and kpi.relation_field_id and primary_records:
                        related_model_name = kpi.related_model_id.model
                        relation_field_name = kpi.relation_field_id.name
                        filter_domain = safe_eval(kpi.filter_domain or '[]')

                        related_domain = [(relation_field_name, 'in', primary_records.ids)] + filter_domain

                        found_records = self.env[related_model_name].search(related_domain)
                        # FIX: Properly check if the 'date' field exists in the related model
                        if 'date' in self.env[related_model_name]._fields:
                            activity_date_field = 'date'
                        else:
                            activity_date_field = 'create_date'

                target.history_ids.unlink()
                history_vals_list = []
                for rec in found_records:
                    rec_date = rec[activity_date_field] if activity_date_field in rec and rec[activity_date_field] else fields.Datetime.now()
                    history_vals_list.append({
                        'target_id': target.id,
                        'source_document_model': rec._name,
                        'source_document_id': rec.id,
                        'activity_date': rec_date,
                        'description': f"Matched: {rec.display_name}"
                    })
                self.env['kpi.history'].create(history_vals_list)

                calculated_value = len(history_vals_list)
                target.write({'actual_value': calculated_value, 'last_computed_date': fields.Datetime.now()})
                _logger.info(f"Recalculated KPI Target '{target.name}': Found {calculated_value} activities.")

            except Exception as e:
                _logger.error(f"Error during KPI recalculation for target '{target.name}': {e}", exc_info=True)

    @api.model
    def _cron_update_actual_values(self):
        _logger.info("Starting nightly KPI Actual Value update cron job...")
        active_targets = self.search([('date_end', '>=', fields.Date.today())])
        active_targets._recalculate_values()
        _logger.info("Finished nightly KPI Actual Value update cron job.")
        return True

    @api.model
    def _update_targets_for_user(self, user_id, model_name):
        if not user_id or not model_name:
            return
        _logger.info(f"Triggering real-time KPI update for user ID: {user_id} on model: {model_name}")
        model_ir = self.env['ir.model'].sudo().search([('model', '=', model_name)], limit=1)
        if not model_ir:
            return

        targets_to_update = self.search([
            ('user_id', '=', user_id),
            ('date_end', '>=', fields.Date.today()),
            ('date_start', '<=', fields.Date.today()),
            '|',
            ('kpi_id.target_model_id', '=', model_ir.id),
            ('kpi_id.related_model_id', '=', model_ir.id),
        ])

        if targets_to_update:
            _logger.info(f"Found {len(targets_to_update)} potentially affected target(s) to update.")
            targets_to_update._recalculate_values()
        return True


# ... end of the KpiTarget class ...

# === NEW FUNCTION FOR POST-INIT SETUP ===
def _link_automation_triggers(env):
    """
    This function is called after the module's data is loaded.
    It programmatically links the server actions to their triggers.
    This is more robust than using ref() in XML for triggers.
    """
    _logger.info("Linking KPI automation triggers...")
    try:
        # Find the trigger record
        trigger = env.ref('base.automation_on_create_or_write')

        # Find the server actions
        lead_action = env.ref('kpi_management_framework.action_server_update_kpi_on_lead_change',
                              raise_if_not_found=False)
        phonecall_action = env.ref('kpi_management_framework.action_server_update_kpi_on_phonecall_change',
                                   raise_if_not_found=False)

        # Link them
        if lead_action and not lead_action.trigger_id:
            lead_action.write({'trigger_id': trigger.id})
            _logger.info(f"Successfully linked trigger to '{lead_action.name}'.")

        if phonecall_action and not phonecall_action.trigger_id:
            phonecall_action.write({'trigger_id': trigger.id})
            _logger.info(f"Successfully linked trigger to '{phonecall_action.name}'.")

    except Exception as e:
        _logger.error(f"Could not link KPI automation triggers. Real-time updates may not work. Error: {e}")



