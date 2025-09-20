from odoo import fields, models, api
# from odoo.exceptions import ValidationError, UserError


class CoffeeArrival(models.Model):
    _name = 'coffee.arrival'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Coffee Arrival Details'
    _rec_name = 'coffee_issue_no'

    date = fields.Date(string='Date', default=fields.Date.today(), required=True)
    coffee_issue_no = fields.Char(string='Coffee & Tea Issue No.', required=True, copy=False, readonly=True,
                                  default='New')
    vehicle_plate_no = fields.Char(string='Vehicle Plate No.', required=True)
    supplier_id = fields.Many2one('res.partner', string='Supplier Name', domain=[('supplier_rank', '>', 0)],
                                  required=True)
    product_id = fields.Many2one(
        'product.product',
        string='Coffee Product',
        domain="[('is_coffee_product', '=', True)]",
        help="Select the specific coffee product that is arriving."
    )
    coffee_grade_id = fields.Many2one(related='product_id.coffee_grade_id', string='Coffee Grade', readonly=True,
                                      store=True)

    amg_grade = fields.Selection(
        related='quality_evaluation_id.amg_grade',
        string='AMG Coffee Grade',
        store=True,
        readonly=True,
    )
    ecx_coffee_name_id = fields.Many2one(
        'ecx.coffee',
        string='ECX Coffee Product',
        required=True,
        help="Select the specific coffee product defined by the ECX classification system."
    )

    woreda_id = fields.Many2one(
        'coffee.woreda',
        string='Woreda/ District',
        required=True,
        help="The specific Woreda where the coffee originated."
    )
    zone_id = fields.Many2one(
        related='woreda_id.zone_id',
        string='Zone/ Province',
        readonly=True,
        store=True,
        help="The Zone of the selected Woreda."
    )

    quality_evaluation_id = fields.Many2one('coffee.quality.evaluation', string='Quality Evaluation', copy=False,
                                            readonly=True)
    weight_history_id = fields.Many2one('coffee.weight.history', string='Weight History', copy=False, readonly=True)

    coffee_origin_ids = fields.Many2one(
        'coffee.origin',
        string='Coffee Origin',
        required=True,
        help="The origin of the coffee."
    )
    coffee_type_ids = fields.Many2one(
        'coffee.type',
        string='Coffee Types',
        help="The types of coffee associated with this arrival."
    )

    state = fields.Selection([
        ('draft', 'Draft'),
        ('quality_evaluated', 'Quality Evaluated'),
        ('weight_recorded', 'Weight Recorded'),
        ('ug_grade', 'UG Grade - Rejected'),
        ('done', 'Done'),
    ], string='Status', default='draft', tracking=True)

    def _get_product_name(self, coffee_origin, coffee_type, amg_grade):
        if not all([coffee_origin, coffee_type, amg_grade]):
            return False

        return "Raw-{}-{}-{}-Coffee".format(
            coffee_origin.name,
            coffee_type.name,
            amg_grade,
        )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('coffee_issue_no', 'New') == 'New':
                vals['coffee_issue_no'] = self.env['ir.sequence'].next_by_code('coffee.arrival') or 'New'
        return super().create(vals_list)

    def action_evaluate_quality(self):
        self.ensure_one()
        if not self.quality_evaluation_id:
            quality_evaluation = self.env['coffee.quality.evaluation'].create({
                'arrival_id': self.id,
                'moisture_content': 0.0,
                'screen_percentage': 0.0,
                'primary_defect': 0.0,
                'secondary_defect': 0.0,
                'odour': 'clean',
                'cup_clean': 0.0,
                'acidity': 0.0,
                'body': 0.0,
                'flavor': 0.0,
            })
            self.quality_evaluation_id = quality_evaluation.id
            if self.state not in ('ug_grade', 'done'):
                self.state = 'quality_evaluated'

        return {
            'type': 'ir.actions.act_window',
            'name': 'Quality Evaluation',
            'res_model': 'coffee.quality.evaluation',
            'res_id': self.quality_evaluation_id.id,
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_arrival_id': self.id,
                'reload_parent': True,
                'form_view_ref': 'coffee_system.coffee_quality_evaluation_view_form',
            },
        }

    def action_record_weight(self):
        self.ensure_one()
        if not self.weight_history_id:
            weight_history = self.env['coffee.weight.history'].create({
                'arrival_id': self.id,
                'num_of_bags': 0,
                'gross_weight': 0.0,
                'truck_weight': 0.0,
                'damage_percentage': 0.0,
                'empty_jute_bag_weight': 0.0,
                'moisture_loss_adjustment': 0.0,
            })
            self.weight_history_id = weight_history.id
        return {
            'type': 'ir.actions.act_window',
            'name': 'Weight History',
            'res_model': 'coffee.weight.history',
            'res_id': self.weight_history_id.id,
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_arrival_id': self.id,
                'reload_parent': True,
                'form_view_ref': 'coffee_system.coffee_weight_history_view_form',
            },
        }