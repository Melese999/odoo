from odoo import fields, models, api, _

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

    # Add to KpiHistory class
    data_quality_type = fields.Selection([
        ('name_confirmed', 'Name Confirmed'),
        ('address_confirmed', 'Address Confirmed'),
        ('phone_confirmed', 'Phone Confirmed'),
        ('all_confirmations', 'All Confirmations'),
    ], string='Data Quality Type', readonly=True)

    name_confirmed = fields.Boolean(string='Name Confirmed', readonly=True)
    address_confirmed = fields.Boolean(string='Address Confirmed', readonly=True)
    phone_confirmed = fields.Boolean(string='Phone Confirmed', readonly=True)

    confirmation_status = fields.Char(
        string='Confirmation Status',
        compute='_compute_confirmation_status',
        store=True
    )

    confirmation_status_badge = fields.Selection([
        ('success', 'Success'),
        ('warning', 'Warning'),
        ('danger', 'Danger'),
    ], compute='_compute_confirmation_status', store=True)

    @api.depends('name_confirmed', 'address_confirmed', 'phone_confirmed', 'data_quality_type')
    def _compute_confirmation_status(self):
        for record in self:
            if record.data_quality_type:
                if record.data_quality_type == 'all_confirmations':
                    if all([record.name_confirmed, record.address_confirmed, record.phone_confirmed]):
                        record.confirmation_status = 'Complete'
                        record.confirmation_status_badge = 'success'
                    else:
                        record.confirmation_status = 'Partial'
                        record.confirmation_status_badge = 'warning'
                else:
                    confirmed = getattr(record, f"{record.data_quality_type}", False)
                    record.confirmation_status = 'Confirmed' if confirmed else 'Pending'
                    record.confirmation_status_badge = 'success' if confirmed else 'danger'
            else:
                record.confirmation_status = 'N/A'
                record.confirmation_status_badge = False

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