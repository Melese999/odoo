from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


# KPI History
class KpiHistory(models.Model):
    _name = 'kpi.history'
    _description = 'KPI Activity History Log'
    _order = 'activity_date desc, id desc'

    target_id = fields.Many2one('kpi.target', string='KPI Target', required=True, ondelete='cascade')
    target_line_id = fields.Many2one('kpi.target.line', string='KPI Target Line', readonly=True)
    kpi_definition_id = fields.Many2one('kpi.definition', string='KPI Definition', readonly=True)

    source_document_model = fields.Char(string='Source Model', readonly=True)
    source_document_id = fields.Integer(string='Source ID', readonly=True)
    source_document = fields.Reference(
        selection='_get_source_document_models',
        string='Source Document',
        compute='_compute_source_document',
        readonly=True
    )

    activity_date = fields.Datetime(string='Activity Date', readonly=True)
    description = fields.Text(string='Description', readonly=True)

    data_quality_score = fields.Float(string='Data Quality Score', digits=(5, 2), readonly=True)
    data_quality_type = fields.Selection([
        ('name_confirmed', 'Name Confirmed'),
        ('address_confirmed', 'Address Confirmed'),
        ('phone_confirmed', 'Phone Confirmed'),
        ('service_satisfaction_confirmed', 'Service Satisfaction'),
        ('product_information_confirmed', 'Product Information'),
        ('all_confirmations', 'All'),
    ], string='Data Quality Type', readonly=True)

    # Add display field for data quality type
    display_data_quality_type = fields.Char(
        string='Quality Type',
        compute='_compute_display_data_quality_type'
    )

    def _get_source_document_models(self):
        return [
            ('crm.lead', 'Lead/Opportunity'),
            ('telemarketing.confirmation', 'Telemarketing Confirmation'),
        ]

    def _compute_source_document(self):
        for rec in self:
            if rec.source_document_model and rec.source_document_id:
                rec.source_document = self.env[rec.source_document_model].browse(rec.source_document_id)
            else:
                rec.source_document = False

    @api.depends('data_quality_type')
    def _compute_display_data_quality_type(self):
        """Convert selection value to display-friendly format"""
        type_mapping = {
            'name_confirmed': 'Name',
            'address_confirmed': 'Address',
            'phone_confirmed': 'Phone',
            'service_satisfaction_confirmed': 'Service',
            'product_information_confirmed': 'Product',
            'all_confirmations': 'All',
        }
        for rec in self:
            if rec.data_quality_type:
                rec.display_data_quality_type = type_mapping.get(rec.data_quality_type, rec.data_quality_type)
            else:
                rec.display_data_quality_type = ''