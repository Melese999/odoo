from odoo import models, fields, api
from odoo.exceptions import ValidationError
import ast
import logging

_logger = logging.getLogger(__name__)


class CrmLeadScoringRule(models.Model):
    _name = 'crm.lead.scoring.rule'
    _description = 'Lead Scoring Rule'
    _order = 'sequence, id'

    name = fields.Char(string='Rule Name', required=True)
    sequence = fields.Integer(default=10, help='Rules are evaluated in sequence')
    active = fields.Boolean(default=True)

    # User-friendly fields instead of raw domain
    country_id = fields.Many2one('res.country', string='Country')
    state_id = fields.Many2one('res.country.state', string='State', domain="[('country_id', '=?', country_id)]")

    # Industry fields
    main_industry_id = fields.Many2one(
        'res.partner.industry',
        string='Main Industry',
        help="Score leads with this main industry"
    )
    secondary_industry_ids = fields.Many2many(
        'res.partner.industry',
        string='Secondary Industries',
        help="Score leads with any of these secondary industries"
    )

    # Revenue-based scoring
    min_expected_revenue = fields.Float(string='Minimum Expected Revenue')
    max_expected_revenue = fields.Float(string='Maximum Expected Revenue')

    # Tag-based scoring - Enhanced with specific tag options
    tag_ids = fields.Many2many(
        'crm.tag',
        string='Tags',
        help="Score leads that have ANY of these tags"
    )

    # Tag matching type
    tag_matching_type = fields.Selection([
        ('Product', 'Product'),
        ('Software', 'Software'),
        ('Services', 'Services'),
        ('Information', 'Information'),
        ('Design', 'Design'),
        ('Training', 'Training'),
        ('Consulting', 'Consulting'),
        ('Other', 'Other')
    ], string='Tags', default='Product', help="How to match the selected tags")

    # Source-based scoring
    source_id = fields.Many2one('utm.source', string='Source')

    # Priority-based scoring
    priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'Medium'),
        ('2', 'High'),
        ('3', 'Very High')
    ], string='Priority')

    # Custom domain for advanced users
    custom_domain = fields.Char(
        string='Advanced Domain',
        help="Advanced: Use Odoo domain syntax for complex rules"
    )

    score_value = fields.Integer(
        string='Score Value',
        required=True,
        help="Score to add (positive) or subtract (negative) if the rule matches."
    )

    application_count = fields.Integer(
        string='Times Applied',
        compute='_compute_application_count',
        help='Number of times this rule has been applied to leads'
    )

    @api.depends('country_id', 'state_id', 'main_industry_id', 'secondary_industry_ids',
                 'min_expected_revenue', 'max_expected_revenue', 'tag_ids', 'tag_matching_type',
                 'source_id', 'priority', 'custom_domain')
    def _compute_application_count(self):
        """Compute how many times this rule would apply"""
        for rule in self:
            try:
                domain = rule._get_domain()
                rule.application_count = self.env['crm.lead'].search_count(domain)
            except Exception as e:
                _logger.warning("Error computing application count for rule %s: %s", rule.name, str(e))
                rule.application_count = 0

    def _get_domain(self):
        """Generate domain from user-friendly fields"""
        domain = []

        # Country and State
        if self.country_id:
            domain.append(('country_id', '=', self.country_id.id))
        if self.state_id:
            domain.append(('state_id', '=', self.state_id.id))

        # Industry fields (check if they exist in the model)
        lead_model = self.env['crm.lead']
        if 'main_industry_id' in lead_model._fields and self.main_industry_id:
            domain.append(('main_industry_id', '=', self.main_industry_id.id))

        if 'secondary_industry_ids' in lead_model._fields and self.secondary_industry_ids:
            domain.append(('secondary_industry_ids', 'in', self.secondary_industry_ids.ids))

        # Revenue range
        if self.min_expected_revenue > 0:
            domain.append(('expected_revenue', '>=', self.min_expected_revenue))
        if self.max_expected_revenue > 0:
            domain.append(('expected_revenue', '<=', self.max_expected_revenue))

        # Tags with different matching types
        if self.tag_ids:
            if self.tag_matching_type == 'Product':
                domain.append(('tag_ids', 'in', self.tag_ids.ids))
            elif self.tag_matching_type == 'Software':
                domain.append(('tag_ids', 'in', self.tag_ids.ids))
            elif self.tag_matching_type == 'Services':
                domain.append(('tag_ids', 'in', self.tag_ids.ids))
            elif self.tag_matching_type == 'Information':
                domain.append(('tag_ids', 'in', self.tag_ids.ids))
            elif self.tag_matching_type == 'Design':
                domain.append(('tag_ids', 'in', self.tag_ids.ids))
            elif self.tag_matching_type == 'Training':
                domain.append(('tag_ids', 'in', self.tag_ids.ids))

            elif self.tag_matching_type == 'Consulting':
                domain.append(('tag_ids', 'in', self.tag_ids.ids))
            elif self.tag_matching_type == 'Other':
                domain.append(('tag_ids', 'not in', self.tag_ids.ids))

        # Source
        if self.source_id:
            domain.append(('source_id', '=', self.source_id.id))

        # Priority
        if self.priority:
            domain.append(('priority', '=', self.priority))

        # Custom domain for advanced users
        if self.custom_domain and self.custom_domain.strip():
            try:
                custom_domain = ast.literal_eval(self.custom_domain.strip())
                if custom_domain:
                    # Combine with existing domain using AND
                    if domain:
                        domain = ['&'] + domain + custom_domain
                    else:
                        domain = custom_domain
            except Exception as e:
                _logger.warning("Invalid custom domain in rule %s: %s", self.name, str(e))

        return domain

    @api.constrains('min_expected_revenue', 'max_expected_revenue')
    def _check_revenue_range(self):
        """Validate revenue range"""
        for rule in self:
            if (rule.min_expected_revenue > 0 and rule.max_expected_revenue > 0 and
                    rule.min_expected_revenue > rule.max_expected_revenue):
                raise ValidationError("Minimum revenue cannot be greater than maximum revenue")

    def test_rule_domain(self):
        """Action to test the rule domain and see which leads match"""
        self.ensure_one()
        try:
            domain = self._get_domain()
            return {
                'type': 'ir.actions.act_window',
                'name': f'Leads Matching: {self.name}',
                'res_model': 'crm.lead',
                'view_mode': 'tree,form',
                'domain': domain,
                'context': {'create': False},
            }
        except Exception as e:
            raise ValidationError(f"Cannot test rule: {str(e)}")

    def action_update_application_count(self):
        """Manual action to update application counts"""
        self._compute_application_count()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Application Counts Updated',
                'message': f'Application counts updated for {len(self)} rule(s)',
                'type': 'success',
                'sticky': False,
            }
        }