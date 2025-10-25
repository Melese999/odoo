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
    kpi_type = fields.Selection(
        related='kpi_definition_id.kpi_type',
        string='KPI Type',
        readonly=True,
        store=True,  # Recommended for fields used in view logic/domain filters
    )
    date_start = fields.Date(
        string='Start Date',
        related='target_id.date_start',
        store=True,
        readonly=True
    )
    date_end = fields.Date(
        string='End Date',
        related='target_id.date_end',
        store=True,
        readonly=True
    )

    user_id = fields.Many2one(related='target_id.user_id', store=True, string='Assigned User')

    target_value = fields.Float(string='Target Value', required=True, default=0.0)
    actual_value = fields.Float(string='Actual Value', readonly=True, default=0.0) # Set by kpi.target's _recalculate_values
    target_value_percentage = fields.Float(
        string='Target (%)',
        compute='_compute_target_value_percentage',
        inverse='_inverse_target_value_percentage',
        store=True,  # Store the computed value for use in views/search
        digits=(5, 2),
        help="Target value. For Data Quality KPIs, this is a percentage (e.g., 95.0)."
    )

    achievement_percentage = fields.Float(
        string='Achievement (%)',
        compute='_compute_achievement_percentage',
        store=True,
        digits=(5, 2)
    )

    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('done', 'Done'),
    ], related='target_id.state', store=True, readonly=True)

    target_value_percentage = fields.Float(
        string='Target Value (%)',
        compute='_compute_target_value_percentage',
        inverse='_inverse_target_value_percentage',
        help="Target value displayed as percentage for Data Quality KPIs"
    )

    @api.depends('actual_value', 'target_value')
    def _compute_achievement_percentage(self):
        """Calculates the percentage of the target achieved."""
        for rec in self:
            if rec.target_value > 0.0:
                percentage = (rec.actual_value / rec.target_value) * 100
                rec.achievement_percentage = percentage
            else:
                rec.achievement_percentage = 0.0

    @api.depends('target_value', 'kpi_type')
    def _compute_target_value_percentage(self):
        """Compute percentage display value for data quality KPIs."""
        for rec in self:
            if rec.kpi_type == 'data_quality':
                # For data quality, show the stored target_value as percentage
                rec.target_value_percentage = rec.target_value
            else:
                # For all other types (e.g., leads_registered), show the raw target value
                rec.target_value_percentage = rec.target_value

    def _inverse_target_value_percentage(self):
        """Inverse method to update the actual target_value from the percentage input."""
        for rec in self:
            # We always write the displayed value back to the stored target_value
            rec.target_value = rec.target_value_percentage

    @api.model
    def create(self, vals):
        # Set a default target value during creation if none is provided
        if 'target_value' not in vals or vals.get('target_value') == 0.0:
            kpi_def_id = vals.get('kpi_definition_id')
            if kpi_def_id:
                kpi_def = self.env['kpi.definition'].browse(kpi_def_id)
                if kpi_def.kpi_type == 'data_quality':
                    # Set a default target of 100% for Data Quality KPIs
                    vals['target_value'] = 100.0
        return super().create(vals)