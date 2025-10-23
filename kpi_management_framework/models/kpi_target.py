from odoo import fields, models, api, _
from odoo.tools.safe_eval import safe_eval
from datetime import timedelta
import logging

_logger = logging.getLogger(__name__)


class KpiTarget(models.Model):
    _name = 'kpi.target'
    _description = 'KPI Target Assignment'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # ADD THIS MISSING FIELD
    kpi_id = fields.Many2one(
        'kpi.definition',
        string='Primary KPI',
        required=True,
        ondelete='cascade',
    )

    name = fields.Char(string='Name', compute='_compute_name', store=True, readonly=True)
    user_id = fields.Many2one('res.users', string='Assigned To', required=True, tracking=True)
    date_start = fields.Date(string='Start Date', required=True)
    date_end = fields.Date(string='End Date', required=True)

    holiday_schedule_id = fields.Many2one('holiday.schedule', string='Holiday Schedule')
    working_days = fields.Integer(compute='_compute_working_days', store=True)

    target_line_ids = fields.One2many('kpi.target.line', 'target_id', string='KPI Lines')

    # This now computes the average achievement across all lines
    overall_achievement = fields.Float(
        string='Overall Achievement (%)',
        compute='_compute_overall_achievement',
        store=True
    )

    history_ids = fields.One2many('kpi.history', 'target_id', string='Activity History')
    activity_count = fields.Integer(string="Activity Count", compute='_compute_activity_count')

    last_computed_date = fields.Datetime(string='Last Computed On', readonly=True)
    # ADD DATA QUALITY COUNT FIELD
    data_quality_count = fields.Integer(
        string="Data Quality Activities",
        compute='_compute_data_quality_count',
        store=True
    )

    @api.depends('history_ids.data_quality_type')
    def _compute_data_quality_count(self):
        """Compute number of data quality activities"""
        for target in self:
            target.data_quality_count = len(target.history_ids.filtered(
                lambda h: h.data_quality_type
            ))

    def action_view_data_quality(self):
        """Action to view data quality activities"""
        self.ensure_one()
        return {
            'name': _('Data Quality Activities'),
            'type': 'ir.actions.act_window',
            'res_model': 'kpi.history',
            'view_mode': 'tree,form',
            'domain': [('target_id', '=', self.id), ('data_quality_type', '!=', False)],
            'context': {'create': False},
        }

    @api.depends('user_id.name', 'date_start', 'date_end')
    def _compute_name(self):
        for record in self:
            if record.user_id and record.date_start and record.date_end:
                record.name = f"KPIs for {record.user_id.name} ({record.date_start.strftime('%b %Y')})"
            else:
                record.name = "New KPI Assignment"

    @api.depends('target_line_ids.achievement_percentage')
    def _compute_overall_achievement(self):
        for record in self:
            if record.target_line_ids:
                record.overall_achievement = sum(record.target_line_ids.mapped('achievement_percentage')) / len(
                    record.target_line_ids)
            else:
                record.overall_achievement = 0.0

    @api.depends('date_start', 'date_end', 'holiday_schedule_id.line_ids.holiday_date')
    def _compute_working_days(self):
        for target in self:
            if not target.date_start or not target.date_end:
                target.working_days = 0
                continue

            # Get holiday dates from the schedule
            holiday_dates = set()
            if target.holiday_schedule_id:
                holiday_dates = set(target.holiday_schedule_id.line_ids.mapped('holiday_date'))

            # Calculate working days (excluding weekends and holidays)
            working_days_count = 0
            current_date = target.date_start
            while current_date <= target.date_end:
                # Monday=0, Sunday=6 - exclude Saturday (5) and Sunday (6)
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
        return {
            'name': _('Tracked Activities for %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'kpi.history',
            'view_mode': 'tree,form',
            'domain': [('target_id', '=', self.id)],
        }

    def action_recalculate_values(self):
        """Button to manually trigger recalculation for all lines."""
        self._recalculate_values()

    def _recalculate_values(self):
        """
        Recalculate all KPI values for the target document.
        """
        KpiHistory = self.env['kpi.history']

        for target in self:
            _logger.info(f"Recalculating KPI Target: {target.name} for user {target.user_id.name}")

            # Clear all old history for this entire target document
            target.history_ids.unlink()

            history_vals_list = []

            for line in target.target_line_ids:
                kpi = line.kpi_definition_id
                _logger.info(f"Processing KPI line: {kpi.name} with method: {kpi.computation_method}")

                calculated_value = 0.0

                # Handle different computation methods
                if kpi.computation_method == 'count_records':
                    calculated_value = self._calculate_count_records(target, kpi, history_vals_list)

                elif kpi.computation_method == 'count_related_records':
                    calculated_value = self._calculate_related_records(target, kpi, history_vals_list)

                elif kpi.computation_method == 'sum_field':
                    calculated_value = self._calculate_sum_field(target, kpi, history_vals_list)

                elif kpi.computation_method == 'data_quality_confirmations':
                    calculated_value = self._calculate_data_quality(target, kpi, history_vals_list)

                # Update the line with calculated value
                line.actual_value = calculated_value
                _logger.info(f"KPI '{kpi.name}' calculated value: {calculated_value}")

            # Create all history records in one batch
            if history_vals_list:
                KpiHistory.create(history_vals_list)
                _logger.info(f"Created {len(history_vals_list)} history records")

            # Update the master record's timestamp
            target.last_computed_date = fields.Datetime.now()
            _logger.info(f"Completed recalculation for KPI Target '{target.name}'.")

    def _calculate_count_records(self, target, kpi, history_vals_list):
        """Calculate count of primary model records"""
        if not all([kpi.target_model_id, kpi.user_field_id, kpi.date_field_id]):
            return 0

        primary_model_name = kpi.target_model_id.model
        user_field_name = kpi.user_field_id.name
        date_field_name = kpi.date_field_id.name
        date_field_type = kpi.date_field_id.ttype

        # Prepare date range based on field type
        if date_field_type == 'datetime':
            date_from = fields.Datetime.to_datetime(target.date_start)
            date_to = fields.Datetime.to_datetime(target.date_end) + timedelta(days=1) - timedelta(seconds=1)
        else:
            date_from = target.date_start
            date_to = target.date_end

        domain = [
            (user_field_name, '=', target.user_id.id),
            (date_field_name, '>=', date_from),
            (date_field_name, '<=', date_to),
        ]

        try:
            records = self.env[primary_model_name].search(domain)

            # Create history records
            for rec in records:
                history_vals_list.append({
                    'target_id': target.id,
                    'source_document_model': rec._name,
                    'source_document_id': rec.id,
                    'activity_date': rec[date_field_name] if date_field_name in rec._fields and rec[
                        date_field_name] else fields.Datetime.now(),
                    'description': f"Record: {rec.display_name}"
                })

            return len(records)

        except Exception as e:
            _logger.error(f"Error counting records for KPI '{kpi.name}': {e}")
            return 0

    def _calculate_data_quality(self, target, kpi, history_vals_list):
        """Calculate data quality confirmations - FIXED VERSION"""
        calculated_value = 0

        # Prepare date range
        date_from = fields.Datetime.to_datetime(target.date_start)
        date_to = fields.Datetime.to_datetime(target.date_end) + timedelta(days=1) - timedelta(seconds=1)

        base_domain = [
            ('user_id', '=', target.user_id.id),
            ('date', '>=', date_from),
            ('date', '<=', date_to),
        ]

        # Track phone calls
        if kpi.call_model_type in ['phonecall', 'both']:
            phonecall_domain = base_domain.copy()

            # Add confirmation filters
            if kpi.confirmation_type == 'name_confirmed':
                phonecall_domain.append(('name_confirmed', '=', True))
            elif kpi.confirmation_type == 'address_confirmed':
                phonecall_domain.append(('address_confirmed', '=', True))
            elif kpi.confirmation_type == 'phone_confirmed':
                phonecall_domain.append(('phone_confirmed', '=', True))
            elif kpi.confirmation_type == 'all_confirmations':
                # For "all confirmations", we need to count calls where ALL three are True
                phonecall_domain.append(('name_confirmed', '=', True))
                phonecall_domain.append(('address_confirmed', '=', True))
                phonecall_domain.append(('phone_confirmed', '=', True))

            try:
                phonecalls = self.env['crm.phonecall'].search(phonecall_domain)
                calculated_value += len(phonecalls)

                # Create history records
                for call in phonecalls:
                    history_vals_list.append({
                        'target_id': target.id,
                        'source_document_model': 'crm.phonecall',
                        'source_document_id': call.id,
                        'activity_date': call.date or fields.Datetime.now(),
                        'description': f"Data Quality: {call.name} - Name: {'✓' if call.name_confirmed else '✗'}, Address: {'✓' if call.address_confirmed else '✗'}, Phone: {'✓' if call.phone_confirmed else '✗'}",
                        'data_quality_type': kpi.confirmation_type,
                        'name_confirmed': call.name_confirmed,
                        'address_confirmed': call.address_confirmed,
                        'phone_confirmed': call.phone_confirmed,
                    })
            except Exception as e:
                _logger.error(f"Error processing phone calls: {e}")

        # Track telemarketing calls
        if kpi.call_model_type in ['telemarketing', 'both']:
            telemarketing_domain = base_domain.copy()

            # Add confirmation filters
            if kpi.confirmation_type == 'name_confirmed':
                telemarketing_domain.append(('name_confirmed', '=', True))
            elif kpi.confirmation_type == 'address_confirmed':
                telemarketing_domain.append(('address_confirmed', '=', True))
            elif kpi.confirmation_type == 'phone_confirmed':
                telemarketing_domain.append(('phone_confirmed', '=', True))
            elif kpi.confirmation_type == 'all_confirmations':
                telemarketing_domain.append(('name_confirmed', '=', True))
                telemarketing_domain.append(('address_confirmed', '=', True))
                telemarketing_domain.append(('phone_confirmed', '=', True))

            try:
                telemarketing_calls = self.env['crm.telemarketing.call'].search(telemarketing_domain)
                calculated_value += len(telemarketing_calls)

                # Create history records
                for call in telemarketing_calls:
                    history_vals_list.append({
                        'target_id': target.id,
                        'source_document_model': 'crm.telemarketing.call',
                        'source_document_id': call.id,
                        'activity_date': call.date or fields.Datetime.now(),
                        'description': f"Data Quality: {call.name} - Name: {'✓' if call.name_confirmed else '✗'}, Address: {'✓' if call.address_confirmed else '✗'}, Phone: {'✓' if call.phone_confirmed else '✗'}",
                        'data_quality_type': kpi.confirmation_type,
                        'name_confirmed': call.name_confirmed,
                        'address_confirmed': call.address_confirmed,
                        'phone_confirmed': call.phone_confirmed,
                    })
            except Exception as e:
                _logger.error(f"Error processing telemarketing calls: {e}")

        return calculated_value

    def _calculate_related_records(self, target, kpi, history_vals_list):
        """Calculate count of related records - SIMPLIFIED FOR NOW"""
        # This would need proper implementation based on your related model logic
        return 0

    def _calculate_sum_field(self, target, kpi, history_vals_list):
        """Calculate sum of a field - SIMPLIFIED FOR NOW"""
        # This would need proper implementation based on your sum field logic
        return 0

    @api.model
    def _cron_update_actual_values(self):
        _logger.info("Starting nightly KPI update cron job...")
        active_targets = self.search([('date_end', '>=', fields.Date.today())])
        active_targets._recalculate_values()
        _logger.info("Finished nightly KPI update cron job.")

    @api.model
    def _update_targets_for_user(self, user_id, model_name):
        """Update KPI targets for a user when related records change"""
        if not user_id or not model_name:
            return

        _logger.info(f"Updating KPI targets for user {user_id} due to {model_name} change")

        # Find active targets for this user
        active_targets = self.search([
            ('user_id', '=', user_id),
            ('date_end', '>=', fields.Date.today()),
            ('date_start', '<=', fields.Date.today()),
        ])

        if active_targets:
            _logger.info(f"Found {len(active_targets)} active targets to update")
            active_targets._recalculate_values()
        else:
            _logger.info("No active targets found to update")