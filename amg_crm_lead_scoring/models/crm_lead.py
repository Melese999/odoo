from odoo import models, fields, api
import ast
import logging

_logger = logging.getLogger(__name__)


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    lead_score = fields.Integer(
        string='Lead Score',
        compute='_compute_lead_score',
        store=True,
        help='Automatically calculated score based on active scoring rules'
    )

    def _get_scoring_depends_fields(self):
        """Get the list of fields that scoring depends on"""
        base_fields = [
            'partner_id', 'stage_id', 'country_id', 'state_id', 'source_id',
            'tag_ids', 'expected_revenue', 'priority', 'partner_name',
            'email_from', 'phone', 'type'
        ]

        # Check if industry fields exist
        industry_fields = ['main_industry_id', 'secondary_industry_ids']
        for field in industry_fields:
            if field in self._fields:
                base_fields.append(field)
            else:
                _logger.debug("Field %s not found in crm.lead model", field)

        return base_fields

    @api.depends(lambda self: self._get_scoring_depends_fields())
    def _compute_lead_score(self):
        """Compute lead score based on active scoring rules"""
        active_rules = self.env['crm.lead.scoring.rule'].search([('active', '=', True)])

        if not active_rules:
            for lead in self:
                lead.lead_score = 0
            return

        for lead in self:
            if not lead.id:  # New record not saved yet
                lead.lead_score = 0
                continue

            score = 0
            for rule in active_rules:
                try:
                    domain = rule._get_domain()
                    if domain:  # Only check if domain is not empty
                        lead_domain = [('id', '=', lead.id)] + domain
                        if self.env['crm.lead'].search_count(lead_domain):
                            score += rule.score_value
                except Exception as e:
                    _logger.warning("Error in scoring rule %s: %s", rule.name, str(e))
                    continue

            lead.lead_score = score

    def action_recompute_scores(self):
        """Manual action to recompute scores for selected leads"""
        self._compute_lead_score()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Lead Scores Updated',
                'message': f'Scores recomputed for {len(self)} lead(s)',
                'type': 'success',
                'sticky': False,
            }
        }