from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError


class ECXCoffee(models.Model):
    _name = 'ecx.coffee'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'ECX Coffee Record'
    _rec_name = 'ecx_coffee_name'

    coffee_origin_id = fields.Many2one(
        'coffee.origin',
        string='Coffee Origin',
        required=True,
        help="The geographical origin of the coffee."
    )

    coffee_type_id = fields.Many2one(
        'coffee.type',
        string='Coffee Type',
        required=True,
        help="The type of coffee (e.g., Washed, Unwashed)."
    )

    coffee_grade_id = fields.Many2one(
        'coffee.grade',
        string='ECX Coffee Grade',
        required=True,
        help="The AMG grade assigned to the coffee."
    )

    ecx_coffee_name = fields.Char(
        string='ECX Coffee Name',
        compute='_compute_coffee_name',
        store=True,
        readonly=True,
        help="The dynamically generated name of the coffee."
    )

    @api.depends('coffee_origin_id', 'coffee_type_id', 'coffee_grade_id')
    def _compute_coffee_name(self):
        """
        Generates the coffee name based on the selected origin, type, and grade.
        The name is formatted as 'Raw-Origin-Type-Grade-Coffee'.
        """
        for record in self:
            if all([record.coffee_origin_id, record.coffee_type_id, record.coffee_grade_id]):
                record.ecx_coffee_name = "ECX_Raw-{}-{}-{}-Coffee".format(
                    record.coffee_origin_id.name,
                    record.coffee_type_id.name,
                    record.coffee_grade_id.name
                )
            else:
                record.ecx_coffee_name = False

    @api.constrains('ecx_coffee_name')
    def _check_unique_ecx_coffee_name(self):
        for record in self:
            if record.ecx_coffee_name:
                existing_record = self.env['ecx.coffee'].search([
                    ('ecx_coffee_name', '=', record.ecx_coffee_name),
                    ('id', '!=', record.id),
                ], limit=1)
                if existing_record:
                    raise ValidationError(_("The combination of Coffee Origin, Type, and Grade already exists."))