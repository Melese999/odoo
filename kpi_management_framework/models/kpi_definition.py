from odoo import fields, models, api
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)

class KpiDefinition(models.Model):
    _name = 'kpi.definition'
    _description = 'KPI Definition (KPI Library)'
    _order = 'name'

    name = fields.Char(string='KPI Name', required=True, help="e.g., Leads Generated, Calls Made, Revenue Won")
    description = fields.Text(string='Description')

    target_ids = fields.One2many('kpi.target', 'kpi_id', string='KPI Targets')

    target_model_id = fields.Many2one(
        'ir.model',
        string='Primary Model to Track',
        ondelete='set null',
    )
    target_model_name = fields.Char(
        related='target_model_id.model',
        string="Target Model Name",
        readonly=True,
        store=False  # Safer as non-stored for this use case
    )
    user_field_id = fields.Many2one(
        'ir.model.fields',
        string='Responsible User Field',
        required=True,
        domain="[('model_id', '=', target_model_id), ('ttype', '=', 'many2one'), ('relation', '=', 'res.users')]",
        ondelete='cascade',
    )
    date_field_id = fields.Many2one(
        'ir.model.fields',
        string='Date Field',
        required=True,
        domain="[('model_id', '=', target_model_id), ('ttype', 'in', ('date', 'datetime'))]",
        ondelete='cascade',
    )
    computation_method = fields.Selection([
        ('count_records', 'Count Records of Primary Model'),
        ('sum_field', 'Sum a Field on Primary Model'),
        ('count_related_records', 'Count Related Records with Filter'),
    ], string='Computation Method', required=True, default='count_records')

    sum_field_id = fields.Many2one('ir.model.fields', string='Field to Sum', domain="[('model_id', '=', target_model_id), ('ttype', 'in', ('float', 'integer', 'monetary'))]", ondelete='cascade')
    related_model_id = fields.Many2one('ir.model', string='Related Model to Count', ondelete='set null')
    relation_field_id = fields.Many2one(
        'ir.model.fields',
        string='Field Linking to Primary Model',
        domain="[('model_id', '=', related_model_id), ('ttype', '=', 'many2one'), ('relation', '=', target_model_name)]",
        ondelete='cascade'
    )
    filter_domain = fields.Char(string='Filter Condition', default='[]')

    @api.onchange('target_model_id')
    def _onchange_target_model_id(self):
        self.user_field_id = False
        self.date_field_id = False
        self.sum_field_id = False
        self.related_model_id = False
        self.relation_field_id = False

    @api.onchange('computation_method')
    def _onchange_computation_method(self):
        if self.computation_method != 'sum_field':
            self.sum_field_id = False

    @api.onchange('related_model_id')
    def _onchange_related_model_id(self):
        self.relation_field_id = False