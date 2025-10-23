from odoo import fields, models, api
from odoo.exceptions import UserError, ValidationError
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
        # Remove required=True and handle via constraints
    )
    target_model_name = fields.Char(
        related='target_model_id.model',
        string="Target Model Name",
        readonly=True,
        store=False
    )
    user_field_id = fields.Many2one(
        'ir.model.fields',
        string='Responsible User Field',
        # Remove required=True and handle via constraints
        domain="[('model_id', '=', target_model_id), ('ttype', '=', 'many2one'), ('relation', '=', 'res.users')]",
        ondelete='cascade',
    )
    date_field_id = fields.Many2one(
        'ir.model.fields',
        string='Date Field',
        # Remove required=True and handle via constraints
        domain="[('model_id', '=', target_model_id), ('ttype', 'in', ('date', 'datetime'))]",
        ondelete='cascade',
    )
    computation_method = fields.Selection([
        ('count_records', 'Count Records of Primary Model'),
        ('sum_field', 'Sum a Field on Primary Model'),
        ('count_related_records', 'Count Related Records with Filter'),
        ('data_quality_confirmations', 'Data Quality Confirmations'),
        ('composite_kpi', 'Composite KPI (Leads + Data Quality)'),  # NEW METHOD
    ], string='Computation Method', required=True, default='count_records')

    sum_field_id = fields.Many2one('ir.model.fields', string='Field to Sum',
                                   domain="[('model_id', '=', target_model_id), ('ttype', 'in', ('float', 'integer', 'monetary'))]",
                                   ondelete='cascade')
    related_model_id = fields.Many2one('ir.model', string='Related Model to Count', ondelete='set null')
    relation_field_id = fields.Many2one(
        'ir.model.fields',
        string='Field Linking to Primary Model',
        domain="[('model_id', '=', related_model_id), ('ttype', '=', 'many2one'), ('relation', '=', target_model_name)]",
        ondelete='cascade'
    )
    filter_domain = fields.Char(string='Filter Condition', default='[]')

    # NEW FIELDS FOR DATA QUALITY TRACKING
    confirmation_type = fields.Selection([
        ('name_confirmed', 'Name Confirmed'),
        ('address_confirmed', 'Address Confirmed'),
        ('phone_confirmed', 'Phone Confirmed'),
        ('all_confirmations', 'All Confirmations'),
    ], string='Confirmation Type', help="Type of data quality confirmation to track")

    call_model_type = fields.Selection([
        ('phonecall', 'Phone Calls'),
        ('telemarketing', 'Telemarketing Calls'),
        ('both', 'Both Call Types'),
    ], string='Call Model Type', default='both', help="Which call models to track for confirmations")

    # NEW FIELDS FOR COMPOSITE KPI
    kpi_type = fields.Selection([
        ('single', 'Single KPI'),
        ('composite', 'Composite KPI (Leads + Data Quality)'),
    ], string='KPI Type', default='single', required=True)

    lead_kpi_definition_id = fields.Many2one(
        'kpi.definition',
        string='Lead KPI Definition',
        domain="[('computation_method', 'in', ('count_records', 'sum_field', 'count_related_records'))]",
        help="Select the KPI definition for lead counting"
    )

    data_quality_kpi_definition_id = fields.Many2one(
        'kpi.definition',
        string='Data Quality KPI Definition',
        domain="[('computation_method', '=', 'data_quality_confirmations')]",
        help="Select the KPI definition for data quality tracking"
    )

    @api.constrains('kpi_type', 'target_model_id', 'user_field_id', 'date_field_id',
                    'lead_kpi_definition_id', 'data_quality_kpi_definition_id')
    def _check_required_fields(self):
        """Ensure required fields are set based on KPI type"""
        for record in self:
            if record.kpi_type == 'single':
                if not record.target_model_id:
                    raise ValidationError("Primary Model to Track is required for single KPIs.")
                if not record.user_field_id:
                    raise ValidationError("Responsible User Field is required for single KPIs.")
                if not record.date_field_id:
                    raise ValidationError("Date Field is required for single KPIs.")
            elif record.kpi_type == 'composite':
                if not record.lead_kpi_definition_id:
                    raise ValidationError("Lead KPI Definition is required for composite KPIs.")
                if not record.data_quality_kpi_definition_id:
                    raise ValidationError("Data Quality KPI Definition is required for composite KPIs.")

    @api.constrains('computation_method', 'kpi_type')
    def _check_computation_method(self):
        """Ensure computation method matches KPI type"""
        for record in self:
            if record.kpi_type == 'composite' and record.computation_method != 'composite_kpi':
                raise ValidationError("Composite KPIs must use 'Composite KPI' computation method.")
            if record.kpi_type == 'single' and record.computation_method == 'composite_kpi':
                raise ValidationError("Single KPIs cannot use 'Composite KPI' computation method.")

    @api.onchange('target_model_id')
    def _onchange_target_model_id(self):
        self.user_field_id = False
        self.date_field_id = False
        self.sum_field_id = False
        self.related_model_id = False
        self.relation_field_id = False
        self.confirmation_type = False
        self.call_model_type = 'both'

    @api.onchange('computation_method')
    def _onchange_computation_method(self):
        if self.computation_method != 'sum_field':
            self.sum_field_id = False
        if self.computation_method != 'data_quality_confirmations':
            self.confirmation_type = False
            self.call_model_type = 'both'
        if self.computation_method != 'composite_kpi':
            self.lead_kpi_definition_id = False
            self.data_quality_kpi_definition_id = False

    @api.onchange('kpi_type')
    def _onchange_kpi_type(self):
        if self.kpi_type == 'composite':
            self.computation_method = 'composite_kpi'
            # Clear single KPI fields
            self.target_model_id = False
            self.user_field_id = False
            self.date_field_id = False
            self.sum_field_id = False
            self.related_model_id = False
            self.relation_field_id = False
            self.filter_domain = '[]'
            self.confirmation_type = False
            self.call_model_type = 'both'
        else:
            self.computation_method = 'count_records'
            # Clear composite KPI fields
            self.lead_kpi_definition_id = False
            self.data_quality_kpi_definition_id = False