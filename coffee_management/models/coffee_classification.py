from odoo import fields, models, api
from odoo.exceptions import ValidationError


class CoffeeType(models.Model):
    _name = 'coffee.type'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Coffee Type (Washed/Unwashed)'

    name = fields.Char(string='Coffee Type', required=True)
    description = fields.Text(string='Description')
    is_default = fields.Boolean(string='Is Default Type')

    _sql_constraints = [
        ('unique_coffee_type_name', 'unique(name)', 'Coffee Type name must be unique!'),
    ]

    @api.constrains('is_default')
    def _check_unique_default(self):
        if self.is_default:
            others = self.search([('is_default', '=', True), ('id', '!=', self.id)])
            if others:
                raise ValidationError("Only one default coffee type is allowed.")


class CoffeeOrigin(models.Model):
    _name = 'coffee.origin'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Coffee Origin (Guji, Sidamo, etc.)'

    name = fields.Char(string='Origin', required=True)
    country_id = fields.Many2one('res.country', string='Country', default=lambda self: self.env.ref('base.et'),
                                 readonly=True)
    region_id = fields.Many2one('res.country.state', string='Region', required=True,
                                domain="[('country_id', '=', country_id)]",
                                help="The region belongs to Ethiopia, Nigeria, and Kenya.")
    altitude = fields.Integer(string='Altitude (meters)')
    coffee_type_ids = fields.Many2many('coffee.type', string='Coffee Types')

    @api.constrains('name')
    def _check_unique_origin_name(self):
        for record in self:
            existing = self.search([
                ('name', '=', record.name),
                ('id', '!=', record.id)
            ], limit=1)
            if existing:
                raise ValidationError("Coffee Origin names must be unique across all regions.")


class CoffeeGrade(models.Model):
    _name = 'coffee.grade'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Coffee Grade'

    name = fields.Char(string='Coffee Grade', required=True)
    # coffee_origin_id = fields.Many2one('coffee.origin', string='Origin', required=True)
    description = fields.Text(string='Description')
    grade_code = fields.Char(string='ECX Grade Code', help='Unique code for the grade')


