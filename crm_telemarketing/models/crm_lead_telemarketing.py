from odoo import models, fields, api

class CrmLead(models.Model):
    _inherit = 'crm.lead'

    # ... fields and _compute_data_quality_score method remain unchanged ...
    telemarketing_call_ids = fields.One2many(
        "crm.telemarketing.call",
        "lead_id",
        string="Telemarketing Calls"
    )

    data_quality_score = fields.Integer(
        string="Data Quality Score (%)",
        compute="_compute_data_quality_score",
        store=True,
        help="Score based on the latest data confirmation checks from telemarketing_dashboard calls."
    )

    @api.depends(
        'phonecall_ids.name_confirmed', 'phonecall_ids.address_confirmed', 'phonecall_ids.phone_confirmed',
        'telemarketing_call_ids.name_confirmed', 'telemarketing_call_ids.address_confirmed', 'telemarketing_call_ids.phone_confirmed'
    )
    def _compute_data_quality_score(self):
        for lead in self:
            # If the lead is not yet saved, we don't have any calls to compute the score from
            if not lead.id:
                lead.data_quality_score = 0
                continue

                # Get the latest call with confirmations
            latest_custom_call = self.env['crm.telemarketing.call'].search([
                ('lead_id', '=', lead.id),
                '|', '|',
                ('name_confirmed', '=', True),
                ('address_confirmed', '=', True),
                ('phone_confirmed', '=', True),
            ], order='date desc', limit=1)
            latest_standard_call = self.env['crm.phonecall'].search([
                ('opportunity_id', '=', lead.id),
                '|', '|',
                ('name_confirmed', '=', True),
                ('address_confirmed', '=', True),
                ('phone_confirmed', '=', True),
            ], order='date desc', limit=1)
            latest_call = None
            if latest_custom_call and latest_standard_call:
                latest_call = latest_custom_call if latest_custom_call.date > latest_standard_call.date else latest_standard_call
            elif latest_custom_call:
                latest_call = latest_custom_call
            elif latest_standard_call:
                latest_call = latest_standard_call
            if not latest_call:
                lead.data_quality_score = 0
                continue
            score = 0
            if latest_call.name_confirmed:
                score += 1
            if latest_call.address_confirmed:
                score += 1
            if latest_call.phone_confirmed:
                score += 1
            lead.data_quality_score = int((score / 3.0) * 100)


    # [FIXED] This method now opens the unified report view.
    def action_view_data_quality_calls(self):
        self.ensure_one()
        # Note: We can't filter the report view on the boolean fields directly
        # as they don't exist on the report model. The domain on lead_id is sufficient.
        # The user can then see all calls and identify the ones with confirmations.
        return {
            'name': 'Data Quality History',
            'type': 'ir.actions.act_window',
            'res_model': 'report.telemarketing', # Point to the report model
            'view_mode': 'tree', # Only show the tree view
            'target': 'current',
            'domain': [
                ('lead_id', '=', self.id),
            ],
            'context': {
                'create': False, # Disable the create button in this view
            }
        }