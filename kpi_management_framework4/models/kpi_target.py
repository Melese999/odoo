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
    user_id = fields.Many2one('res.users', string='Assigned To', required=True, tracking=True)
    date_start = fields.Date(string='Start Date', required=True)
    date_end = fields.Date(string='End Date', required=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('done', 'Done'),
    ], string='Status', required=True, default='draft', tracking=True)

    # Note: holiday_schedule_id field removed as it was causing conflicts in previous steps
    working_days = fields.Integer(
        string='Working Days (Calculated)',
        compute='_compute_working_days',
        store=True
    )

    last_computed_date = fields.Datetime(
        string='Last Computed On',
        readonly=True,
        help="Date and time of the last target value recalculation."
    )

    # NEW: Field for accessing all related history records (used by _recalculate_values)
    history_ids = fields.One2many(
        'kpi.history',
        'target_id',
        string='History Log',
        readonly=True
    )

    # Fields required by the view stat buttons
    activity_count = fields.Integer(
        string='Activities Count',
        compute='_compute_counts'
    )
    data_quality_count = fields.Integer(
        string='Data Quality Count',
        compute='_compute_counts'
    )

    target_line_ids = fields.One2many('kpi.target.line', 'target_id', string='KPI Lines')

    overall_achievement = fields.Float(
        string='Overall Achievement (%)',
        compute='_compute_overall_achievement',
        store=True,
        digits=(5, 2)
    )
    overall_achievement_leads = fields.Float(
        string='Leads Achievement (%)',
        compute='_compute_overall_achievement',
        store=True,
        digits=(5, 2)
    )
    overall_achievement_data_quality = fields.Float(
        string='Data Quality Achievement (%)',
        compute='_compute_overall_achievement',
        store=True,
        digits=(5, 2)
    )

    # =========================================================================
    # KPI CALCULATION LOGIC
    # =========================================================================

    def _calculate_leads_registered(self, target, kpi, history_vals_list):
        """Calculates the count of Leads Registered and prepares history records."""
        date_start = target.date_start
        date_end = target.date_end
        user = target.user_id

        # Search for all leads created by the user within the target period
        leads = self.env['crm.lead'].search([
            ('user_id', '=', user.id),
            ('create_date', '>=', fields.Datetime.to_datetime(date_start)),
            ('create_date', '<=', fields.Datetime.to_datetime(date_end) + timedelta(days=1)),
        ])

        calculated_value = len(leads)

        # Prepare history records for batch creation
        for lead in leads:
            history_vals_list.append({
                'target_id': target.id,
                'target_line_id': kpi.target_line_id.id,  # Assumes 1:1 line for the KPI
                'kpi_definition_id': kpi.id,
                'source_document_model': 'crm.lead',
                'source_document_id': lead.id,
                'activity_date': lead.create_date,
                'description': f"Lead registered: {lead.name}",
                'data_quality_score': 0.0,
            })

        return calculated_value

    def _calculate_data_quality(self, target, kpi, history_vals_list):
        """Calculates the average Data Quality score from crm.phonecall and prepares history records."""
        date_start = target.date_start
        date_end = target.date_end
        user = target.user_id

        # Search for all phonecalls created by the user within the target period
        phonecalls = self.env['crm.phonecall'].search([
            ('user_id', '=', user.id),
            ('create_date', '>=', fields.Datetime.to_datetime(date_start)),
            ('create_date', '<=', fields.Datetime.to_datetime(date_end) + timedelta(days=1)),
        ])

        calculated_value = 0.0

        if phonecalls:
            # The actual_value is the average of the overall_score from crm.phonecall
            total_score = sum(phonecall.overall_score for phonecall in phonecalls)
            calculated_value = total_score / len(phonecalls)

            # Prepare history records for batch creation
            for phonecall in phonecalls:
                history_vals_list.append({
                    'target_id': target.id,
                    'target_line_id': kpi.target_line_id.id,
                    'kpi_definition_id': kpi.id,
                    'source_document_model': 'crm.phonecall',
                    'source_document_id': phonecall.id,
                    'activity_date': phonecall.create_date,
                    'description': f"Data Quality Score for Phone Call: {phonecall.name}",
                    'data_quality_score': phonecall.overall_score,
                    'data_quality_type': 'all_confirmations',
                    # FIX: Use 'all_confirmations' as the type for overall score
                })

        return calculated_value

    def _recalculate_values(self):
        """Recalculate all KPI values for the target document (can be called on multiple records)."""
        # self.ensure_one() # REMOVED: Allows calling on a record set (e.g., from cron or auto-update)
        KpiHistory = self.env['kpi.history']

        for target in self:
            _logger.info(f"Recalculating KPI Target: {target.name} for user {target.user_id.name}")

            # Clear all old history for this entire target document
            target.history_ids.unlink()
            history_vals_list = []

            for line in target.target_line_ids:
                kpi = line.kpi_definition_id
                _logger.info(f"Processing KPI line: {kpi.name} with type: {kpi.kpi_type}")

                kpi.target_line_id = line

                calculated_value = 0.0

                if kpi.kpi_type == 'leads_registered':
                    calculated_value = self._calculate_leads_registered(target, kpi, history_vals_list)
                elif kpi.kpi_type == 'data_quality':
                    calculated_value = self._calculate_data_quality(target, kpi, history_vals_list)

                # Update the line with calculated value
                line.actual_value = calculated_value
                _logger.info(f"KPI '{kpi.name}' calculated value: {calculated_value}")

                kpi.target_line_id = False


            # Create all history records in one batch
            if history_vals_list:
                KpiHistory.create(history_vals_list)
                _logger.info(f"Created {len(history_vals_list)} history records")

            # Trigger overall achievement computation
            target._compute_overall_achievement()

            # Update the master record's timestamp
            target.last_computed_date = fields.Datetime.now()
            _logger.info(f"Completed recalculation for KPI Target '{target.name}'.")

    # Public action for the button (calls the private calculation method)
    # def action_recalculate_values(self):
    #     """Manually trigger recalculation of all associated lines for the selected record(s)."""
    #     for record in self:
    #         record._recalculate_values()
    #     return True

    # =========================================================================
    # COMPUTED FIELDS & UTILITIES
    # =========================================================================

    def _compute_counts(self):
        """Compute the count fields used in the oe_button_box."""
        for record in self:
            # activity_count comes from mail.activity.mixin
            record.activity_count = len(record.activity_ids)

            # data_quality_count: Counts only history records related to data quality
            record.data_quality_count = self.env['kpi.history'].search_count([
                ('target_id', '=', record.id),
                ('data_quality_type', '!=', False)
            ])

    # @api.depends('user_id', 'date_start', 'date_end')
    # def _compute_working_days(self):
    #     """Compute the number of working days between date_start and date_end
    #     using the user's resource calendar (Odoo 17 compatible).
    #     """
    #     # A common standard is 8 working hours per day.
    #     HOURS_PER_WORKING_DAY = 8.0
    #
    #     for record in self:
    #         if record.user_id and record.date_start and record.date_end:
    #             calendar = record.user_id.resource_calendar_id or record.user_id.company_id.resource_calendar_id
    #
    #             if not calendar:
    #                 record.working_days = 0
    #                 continue
    #
    #             # --- FIX: Convert Date objects to Datetime objects ---
    #
    #             # Convert date_start (Date) to a timezone-aware Datetime object (00:00:00)
    #             date_start_dt = fields.Datetime.to_datetime(record.date_start)
    #
    #             # Convert date_end (Date) to a timezone-aware Datetime object (23:59:59)
    #             # We add one day and use the 'at_end_of' context to ensure the entire last day is included in the calculation.
    #             date_end_dt = fields.Datetime.to_datetime(record.date_end + timedelta(days=1))
    #
    #             # The calendar object handles timezones automatically if given a datetime
    #             total_work_hours = calendar.get_work_hours_count(
    #                 date_start_dt,  # Pass datetime
    #                 date_end_dt,  # Pass datetime
    #             )
    #
    #             # Convert total hours to working days
    #             if total_work_hours > 0 and HOURS_PER_WORKING_DAY > 0:
    #                 work_days = total_work_hours / HOURS_PER_WORKING_DAY
    #             else:
    #                 work_days = 0.0
    #
    #             # Round to the nearest whole day
    #             record.working_days = round(work_days+4.0)
    #         else:
    #             record.working_days = 0
    working_days = fields.Integer(compute='_compute_working_days', store=True)

    @api.depends('date_start', 'date_end', 'user_id.resource_calendar_id')
    def _compute_working_days(self):
        for rec in self:
            calendar = rec.user_id.resource_calendar_id

            # Check for all required fields
            if rec.date_start and rec.date_end and calendar:

                # Convert Date fields to Datetime in UTC for calendar methods
                start_dt = fields.Datetime.to_datetime(rec.date_start)
                # To include the entire end day, add a full day to end_dt
                end_dt = fields.Datetime.to_datetime(rec.date_end) + timedelta(days=1)

                # Use the standard Odoo resource.calendar method
                # to get the duration data (including days and hours)
                duration_data = calendar.get_work_duration_data(
                    start_dt,
                    end_dt,
                    compute_leaves=True
                )

                # 'days' is a float representing the working time.
                # We round it to the nearest integer for 'working_days'
                rec.working_days = round(duration_data.get('days', 0.0))
            else:
                rec.working_days = 0
    @api.depends('user_id', 'date_start', 'date_end')
    def _compute_name(self):
        for record in self:
            if record.user_id and record.date_start and record.date_end:
                start_str = fields.Date.to_string(record.date_start)
                end_str = fields.Date.to_string(record.date_end)
                record.name = f"{record.user_id.name} KPI Target ({start_str} to {end_str})"
            else:
                record.name = _("New KPI Target")

    @api.depends('target_line_ids.achievement_percentage')
    def _compute_overall_achievement(self):
        for record in self:
            all_lines = record.target_line_ids

            # Overall (Average of all lines)
            if all_lines:
                total_percentage = sum(line.achievement_percentage for line in all_lines)
                record.overall_achievement = total_percentage / len(all_lines)
            else:
                record.overall_achievement = 0.0

            # Leads Achievement
            leads_lines = all_lines.filtered(lambda l: l.kpi_definition_id.kpi_type == 'leads_registered')
            if leads_lines:
                total_percentage = sum(line.achievement_percentage for line in leads_lines)
                record.overall_achievement_leads = total_percentage / len(leads_lines)
            else:
                record.overall_achievement_leads = 0.0

            # Data Quality Achievement
            dq_lines = all_lines.filtered(lambda l: l.kpi_definition_id.kpi_type == 'data_quality')
            if dq_lines:
                total_percentage = sum(line.achievement_percentage for line in dq_lines)
                record.overall_achievement_data_quality = total_percentage / len(dq_lines)
            else:
                record.overall_achievement_data_quality = 0.0

    # ... (action_view_activities and action_view_data_quality methods remain the same)
    def action_view_activities(self):
        self.ensure_one()
        return {
            'name': f"Activity History for {self.name}",
            'type': 'ir.actions.act_window',
            'res_model': 'kpi.history',
            'view_mode': 'tree,form',
            'domain': [
                ('target_id', '=', self.id),
                ('data_quality_type', '=', False),
            ],
            'context': {'default_target_id': self.id},
        }

    def action_view_data_quality(self):
        self.ensure_one()
        return {
            'name': f"Data Quality for {self.name}",
            'type': 'ir.actions.act_window',
            'res_model': 'kpi.history',
            'view_mode': 'tree,form',
            'domain': [
                ('target_id', '=', self.id),
                ('data_quality_type', '!=', False),
            ],
            'context': {'default_target_id': self.id},
        }

    @api.model
    def _run_nightly_kpi_update(self):
        """Called by cron job to update all active targets."""
        _logger.info("Starting nightly KPI update cron job...")
        # Find active targets
        active_targets = self.search([('date_end', '>=', fields.Date.today()), ('state', '=', 'active')])
        # Call the private calculation method on all active targets
        for target in active_targets:
            target._recalculate_values()
        _logger.info("Finished nightly KPI update cron job.")

    @api.model
    def _update_targets_for_user(self, user_id, model_name):
        """Update KPI targets for a user when related records change"""
        if not user_id or not model_name:
            return

        active_targets = self.search([
            ('user_id', '=', user_id),
            ('date_end', '>=', fields.Date.today()),
            ('date_start', '<=', fields.Date.today()),
            ('state', '=', 'active'),
        ])

        if active_targets:
            for target in active_targets:
                target._recalculate_values()


# =============================================================================
# TEMPORARY FIELD ON KPI DEFINITION TO PASS TARGET LINE ID
# =============================================================================

# This allows the helper functions in kpi.target to access the target_line_id
# without changing the function signature across multiple calls.
# This should be implemented in kpi_definition.py
class KpiDefinition(models.Model):
    _inherit = 'kpi.definition'

    # Temporary field to hold the target line record for calculation history
    target_line_id = fields.Many2one('kpi.target.line', string='Current Target Line', store=False)