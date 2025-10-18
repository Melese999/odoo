from odoo import fields, models

import logging
_logger = logging.getLogger(__name__)

class KpiHistory(models.Model):
    _name = 'kpi.history'
    _description = 'KPI Activity History Log'
    _order = 'activity_date desc, id desc'
    _rec_name = 'target_id'

    target_id = fields.Many2one(
        'kpi.target',
        string='KPI Target',
        required=True,
        ondelete='cascade'
    )
    # Generic link to the source document using a Reference field
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

    def _get_source_document_models(self):
        # Return a list of tuples with (model, description)
        return [
            ('crm.lead', 'Lead/Opportunity'),
            ('crm.phonecall', 'Phone Call'),
            ('crm.telemarketing.call', 'Telemarketing Call')
        ]

    def _compute_source_document(self):
        for rec in self:
            if rec.source_document_model and rec.source_document_id:
                # Create the reference using the proper format for Reference fields
                model = rec.source_document_model
                record_id = rec.source_document_id
                # Use the env to create the reference properly
                rec.source_document = self.env[model].browse(record_id)
            else:
                rec.source_document = False