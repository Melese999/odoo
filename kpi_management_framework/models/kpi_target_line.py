from odoo import api, fields, models
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class KpiTargetLine(models.Model):
    _name = 'kpi.target.line'
    _description = 'KPI Target Line'
    _order = 'sequence, id'

    target_id = fields.Many2one('kpi.target', string='KPI Target', required=True, ondelete='cascade')
    sequence = fields.Integer(string='Sequence', default=10)

    kpi_definition_id = fields.Many2one(
        'kpi.definition',
        string='KPI Definition',
        required=True,
        ondelete='cascade',
    )

    # Use user_id instead of employee_id to match your security rules
    user_id = fields.Many2one(related='target_id.user_id', store=True, string='Assigned User')

    # Target value with default
    target_value = fields.Float(string='Target Value', required=True, default=0.0)
    actual_value = fields.Float(string='Actual Value', readonly=True, default=0.0)

    # Add fields for conditional display in views
    target_value_percentage = fields.Float(
        string='Target Value (%)',
        compute='_compute_target_value_percentage',
        inverse='_inverse_target_value_percentage',
        help="Target value displayed as percentage for data quality KPIs"
    )

    # Fix field name to match the one used in views
    achievement_percentage = fields.Float(
        string='Achievement (%)', digits=(5,2),
        compute='_compute_achievement_percentage',
        store=True
    )

    # Remove state field if not needed, or keep it simple
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('done', 'Done')
    ], string='Status', default='draft')

    # Related fields for reporting
    date_start = fields.Date(related='target_id.date_start', store=True)
    date_end = fields.Date(related='target_id.date_end', store=True)

    @api.depends('actual_value', 'target_value', 'kpi_definition_id.kpi_type')
    def _compute_achievement_percentage(self):
        for record in self:
            if record.target_value and record.target_value != 0:
                # If target_value is stored as percentage (75.00), divide by 100 for calculation
                if record.kpi_definition_id.kpi_type == 'data_quality':
                    # For data quality: both actual_value and target_value are percentages
                    # Example: actual_value=80.0, target_value=75.0
                    # Achievement = (80.0 / 75.0) * 100 = 106.67%
                    record.achievement_percentage = (record.actual_value / record.target_value) * 100
                    #target = record.target_value / 100.0
                else:
                    # For leads: direct comparison
                    # Example: actual_value=21.0, target_value=25.0
                    # Achievement = (21.0 / 25.0) * 100 = 84.0%
                    record.achievement_percentage = (record.actual_value / record.target_value) * 100
                # target = record.target_value
                #record.achievement_percentage = (record.actual_value / target) * 100
            else:
                record.achievement_percentage = 0.0

    @api.constrains('target_value')
    def _check_target_value(self):
        for rec in self:
            if rec.kpi_definition_id.kpi_type == 'data_quality':
                if not (0 <= rec.target_value <= 100):
                    raise ValidationError("Target value for Data Quality KPI must be between 0% and 100%.")
            elif rec.kpi_definition_id.kpi_type == 'leads_registered':
                if rec.target_value < 0:
                    raise ValidationError("Target value for Leads Registered KPI cannot be negative.")

    @api.onchange('kpi_definition_id')
    def _onchange_kpi_definition_id(self):
        for rec in self:
            if rec.kpi_definition_id.kpi_type == 'data_quality':
                # Set reasonable default for data quality KPIs
                if rec.target_value == 0.0:  # Only set if not already set
                    rec.target_value = 75.0
            elif rec.kpi_definition_id.kpi_type == 'leads_registered':
                if rec.target_value == 0.0:  # Only set if not already set
                    rec.target_value = 10.0

    @api.depends('target_value', 'kpi_definition_id.kpi_type')
    def _compute_target_value_percentage(self):
        """Compute percentage display value"""
        for rec in self:
            if rec.kpi_definition_id.kpi_type == 'data_quality':
                # For data quality, show the same value (it's already stored as percentage)
                rec.target_value_percentage = rec.target_value
            else:
                # For leads, show as is
                rec.target_value_percentage = rec.target_value

    def _inverse_target_value_percentage(self):
        """Inverse method to update the actual target_value"""
        for rec in self:
            rec.target_value = rec.target_value_percentage

    @api.model
    def create(self, vals):
        # Ensure target_value has a default if not provided
        if 'target_value' not in vals or vals.get('target_value') == 0.0:
            # Set default based on KPI type if we can determine it
            kpi_def_id = vals.get('kpi_definition_id')
            if kpi_def_id:
                kpi_def = self.env['kpi.definition'].browse(kpi_def_id)
                if kpi_def.kpi_type == 'data_quality':
                    vals['target_value'] = 75.0
                else:
                    vals['target_value'] = 10.0
            else:
                vals['target_value'] = 0.0

        return super().create(vals)