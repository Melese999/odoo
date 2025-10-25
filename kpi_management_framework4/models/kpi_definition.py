from odoo import fields, models, api
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class KpiDefinition(models.Model):
    _name = 'kpi.definition'
    _description = 'KPI Definition (KPI Library)'
    _order = 'name'

    name = fields.Char(string='KPI Name', required=True)
    description = fields.Text(string='Description')

    assigned_target_count = fields.Integer(
        string="Assigned Targets",
        compute="_compute_assigned_target_count",
        store=False
    )

    kpi_type = fields.Selection([
        ('leads_registered', 'Leads Registered'),
        ('data_quality', 'Data Quality'),
    ], string='KPI Type', required=True, default='leads_registered')

    # Use fields.Text to store the comma-separated values of the multi-selection widget

    confirmation_fields = fields.Selection([
        ('name_confirmed', 'Name Confirmation'),
        ('address_confirmed', 'Address Confirmation'),
        ('phone', 'Phone Confirmation'),
        ('service_satisfaction', 'Service Satisfaction'),
        ('product_information', 'Product Information'),
        ('all_confirmations', 'All'),
    ], string='Confirmation Type', help="Which data quality metric to track")

    # All possible values for the multi-selection widget on kpi.definition
    _CONFIRMATION_FIELDS = [
        ('name_confirmed', 'Name Confirmation'),
        ('address_confirmed', 'Address Confirmation'),
        ('phone_confirmed', 'Phone Confirmation'),
        ('service_satisfaction_confirmed', 'Service Satisfaction'),
        ('product_information_confirmed', 'Product Information'),
        ('all_confirmations', 'All'),
    ]

    # Inject the selection values into the field definition for the UI widget to use
    @api.model
    def fields_get(self, allfields=None, attributes=None):
        res = super().fields_get(allfields, attributes)
        # 💡 FIX: Ensure the correct field name 'confirmation_fields' is used here.
        if 'confirmation_fields' in res:
            res['confirmation_fields']['selection'] = self._CONFIRMATION_FIELDS
        return res

    @api.depends()
    def _compute_assigned_target_count(self):
        """Compute the number of KPI Target Lines assigned to this KPI Definition"""
        targetLine = self.env['kpi.target.line']
        for rec in self:
            rec.assigned_target_count = targetLine.search_count([('kpi_definition_id', '=', rec.id)])

    def action_view_assigned_targets(self):
        """Open all KPI Target Lines related to this KPI Definition."""
        self.ensure_one()
        return {
            'name': f"KPI Targets for {self.name}",
            'type': 'ir.actions.act_window',
            'res_model': 'kpi.target.line',
            'view_mode': 'tree,form',
            'domain': [('kpi_definition_id', '=', self.id)],
            'context': {'default_kpi_definition_id': self.id},
        }

    # 💡 FIX: The @api.constrains decorator must be present (uncommented) to enforce the validation.
    @api.constrains('kpi_type', 'confirmation_fields')
    def _check_confirmation_fields(self):
        """Ensure confirmation fields are set for data quality KPIs"""
        for record in self:
            if record.kpi_type == 'data_quality' and not record.confirmation_fields:
                raise ValidationError("Confirmation Type is required for Data Quality KPIs.")