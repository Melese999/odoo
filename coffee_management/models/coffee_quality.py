# In coffee.quality.evaluation model
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError, UserError


class CoffeeQualityEvaluation(models.Model):
    _name = 'coffee.quality.evaluation'
    _description = 'Coffee Quality Evaluation'
    _rec_name = 'arrival_id'

    arrival_id = fields.Many2one('coffee.arrival', string='Arrival Record', required=True, ondelete='cascade')
    moisture_content = fields.Float(string='Moisture Content (%)', required=True, default=0.0)
    screen_percentage = fields.Float(string='Screen (%)', required=True, default=0.0)

    # Raw Attributes
    primary_defect = fields.Float(string='Primary Defect (15%)', required=True, default=0.0)
    secondary_defect = fields.Float(string='Secondary Defect (15%)', required=True, default=0.0)
    odour = fields.Selection([
        ('clean', 'Clean'),
        ('light', 'Light'),
        ('moderate', 'Moderate'),
        ('strong', 'Strong'),
    ], string='Odour (10%)', required=True, default='clean')

    # Cup Attributes
    cup_clean = fields.Float(string='Cup Clean (15%)', required=True, default=0.0)
    acidity = fields.Float(string='Acidity (15%)', required=True, default=0.0)
    body = fields.Float(string='Body (15%)', required=True, default=0.0)
    flavor = fields.Float(string='Flavor (15%)', required=True, default=0.0)

    total_score = fields.Float(string='Total Score (%)', compute='_compute_total_score', store=True)
    amg_grade = fields.Selection([
        ('UG', 'UG'),
        ('G5', 'G5'),
        ('G4', 'G4'),
        ('G3', 'G3'),
        ('G2', 'G2'),
        ('G1', 'G1'),
    ], string='AMG Grade', compute='_compute_amg_grade', store=True)

    arrival_date = fields.Date(
        string='Arrival Date',
        related='arrival_id.date',
        store=True,
        readonly=True
    )

    @api.depends('primary_defect', 'secondary_defect', 'odour', 'cup_clean', 'acidity', 'body', 'flavor')
    def _compute_total_score(self):
        odour_defect_mapping = {
            'clean': 0.0,
            'light': 3.0,
            'moderate': 6.0,
            'strong': 10.0,
        }

        for record in self:
            odour_defect_value = odour_defect_mapping.get(record.odour, 0.0)
            record.total_score = (
                    record.primary_defect +
                    record.secondary_defect +
                    (10 - odour_defect_value) +
                    record.cup_clean +
                    record.acidity +
                    record.body +
                    record.flavor
            )

    @api.depends('total_score')
    def _compute_amg_grade(self):
        for record in self:
            if 15 <= record.total_score <= 30:
                record.amg_grade = 'UG'
            elif 31 <= record.total_score <= 46:
                record.amg_grade = 'G5'
            elif 47 <= record.total_score <= 62:
                record.amg_grade = 'G4'
            elif 63 <= record.total_score <= 74:
                record.amg_grade = 'G3'
            elif 75 <= record.total_score <= 84:
                record.amg_grade = 'G2'
            elif record.total_score >= 85:
                record.amg_grade = 'G1'
            else:
                record.amg_grade = False

    def _create_or_update_product(self):
        for record in self:
            if record.arrival_id.coffee_origin_ids and record.arrival_id.coffee_type_ids and record.amg_grade:
                product_name = record.arrival_id._get_product_name(
                    record.arrival_id.coffee_origin_ids,
                    record.arrival_id.coffee_type_ids,
                    record.amg_grade
                )

                if product_name:
                    existing_product = self.env['product.product'].search([('name', '=', product_name)], limit=1)
                    if existing_product:
                        record.arrival_id.product_id = existing_product.id
                    else:
                        new_product = self.env['product.product'].create({
                            'name': product_name,
                            'is_coffee_product': True,
                        })
                        record.arrival_id.product_id = new_product.id

    @api.constrains('amg_grade')
    def _check_amg_grade_for_downstream(self):
        for record in self:
            if record.amg_grade == 'UG':
                record.arrival_id.state = 'ug_grade'
                raise UserError(
                    _("AMG Grade is 'UG'. All downstream steps (Weight, Stock, Contract) are disabled for this coffee arrival."))
            elif record.amg_grade and record.arrival_id.state not in ('done', 'ug_grade'):
                # Call the new method to create/update the product
                record._create_or_update_product()
                record.arrival_id.state = 'quality_evaluated'

    @api.onchange('primary_defect', 'secondary_defect', 'cup_clean', 'acidity', 'body', 'flavor')
    def _check_quality_scores(self):
        """
        Validates that quality scores are within the acceptable range [0, 15].
        """
        for record in self:
            scores = {
                'Primary Defect': record.primary_defect,
                'Secondary Defect': record.secondary_defect,
                'Cup Clean': record.cup_clean,
                'Acidity': record.acidity,
                'Body': record.body,
                'Flavor': record.flavor,
            }
            for name, score in scores.items():
                if not (0 <= score <= 15):
                    raise ValidationError(_(f"{name} score must be greater than or equal to 0 and less than or equal to 15."))

    @api.onchange('moisture_content')
    def _onchange_moisture_content(self):
        if self.moisture_content > 12:
            return {'warning': {
                'title': "Moisture Warning",
                'message': "Moisture content is high. Consider potential quality issues for this coffee."
            }}

