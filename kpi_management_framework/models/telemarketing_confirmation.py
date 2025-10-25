from odoo import fields, models, api
import logging

_logger = logging.getLogger(__name__)


class TelemarketingConfirmation(models.Model):
    _name = 'telemarketing.confirmation'
    _description = 'Telemarketing Data Quality Confirmation'
    _order = 'confirmation_date desc'

    name = fields.Char(required=True, default=lambda self: self._get_default_name())
    lead_id = fields.Many2one('crm.lead', required=True, ondelete='cascade')
    telemarketer_id = fields.Many2one('res.users', required=True)
    confirmation_date = fields.Datetime(default=fields.Datetime.now)
    phonecall_id = fields.Many2one("crm.phonecall", string="Related Phone Call")
    # Data quality fields
    name_confirmed = fields.Boolean()
    address_confirmed = fields.Boolean()
    phone_confirmed = fields.Boolean()
    service_satisfaction_confirmed = fields.Boolean()
    product_information_confirmed = fields.Boolean()

    overall_score = fields.Float(compute='_compute_overall_score', store=True)

    kpi_history_ids = fields.One2many('kpi.history', 'source_document_id',
                                      domain=[('source_document_model', '=', 'telemarketing.confirmation')],
                                      string='Linked KPI Histories')

    @api.depends('name_confirmed', 'address_confirmed', 'phone_confirmed',
                 'service_satisfaction_confirmed', 'product_information_confirmed')
    def _compute_overall_score(self):
        fields_to_check = ['name_confirmed', 'address_confirmed', 'phone_confirmed',
                           'service_satisfaction_confirmed', 'product_information_confirmed']
        for rec in self:
            confirmed_count = sum(1 for f in fields_to_check if getattr(rec, f))
            rec.overall_score = (confirmed_count / len(fields_to_check)) * 100 if fields_to_check else 0

    def _get_default_name(self):
        prefix = self.env['ir.config_parameter'].sudo().get_param(
            'telemarketing.confirmation.prefix', default='CONF'
        )
        seq = self.env['ir.sequence'].next_by_code('telemarketing.confirmation')
        if seq:
            # Include year and month automatically
            current_date = fields.Date.today()
            year = current_date.strftime("%Y")
            month = current_date.strftime("%m")
            return f"{prefix}/{year}/{month}/{seq}"
        return f"{prefix}/0000"

    def action_confirm_all(self):
        """Action to confirm all data quality fields at once"""
        for record in self:
            record.write({
                'name_confirmed': True,
                'address_confirmed': True,
                'phone_confirmed': True,
                'service_satisfaction_confirmed': True,
                'product_information_confirmed': True,
            })
        return True

    @api.onchange('lead_id')
    def _onchange_lead_id(self):
        for record in self:
            if record.lead_id:
                # Set telemarketer to the lead's creator, not current user
                record.telemarketer_id = record.lead_id.create_uid or self.env.user

    @api.model
    def create(self, vals):
        # FIX: Set telemarketer_id BEFORE calling super().create()
        if 'lead_id' in vals and 'telemarketer_id' not in vals:
            lead = self.env['crm.lead'].browse(vals['lead_id'])
            if lead:
                vals['telemarketer_id'] = lead.create_uid.id

        # Create the record with the properly set telemarketer_id
        record = super().create(vals)

        # Update KPI targets after creation
        if record.lead_id and record.lead_id.user_id:
            self.env['kpi.target'].sudo()._update_targets_for_user(record.lead_id.user_id.id,
                                                                   'telemarketing.confirmation')
        return record

    def write(self, vals):
        res = super().write(vals)
        for rec in self:
            if rec.lead_id and rec.lead_id.user_id:
                self.env['kpi.target'].sudo()._update_targets_for_user(rec.lead_id.user_id.id,
                                                                       'telemarketing.confirmation')
        return res