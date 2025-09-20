# models/coffee_weight.py
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class CoffeeWeightHistory(models.Model):
    _name = 'coffee.weight.history'
    _description = 'Coffee Weight History'
    _rec_name = 'arrival_id'

    arrival_id = fields.Many2one(
        'coffee.arrival', 
        string='Arrival Record', 
        required=True, 
        ondelete='cascade',
        help="Reference to the coffee arrival record"
    )
    num_of_bags = fields.Integer(
        string='Number of Bags', 
        required=True,
        help="Total number of coffee bags received"
    )
    damage_percentage = fields.Float(
        string='Damage Percentage (%)', 
        default=0.0,
        help="Percentage of damaged bags in the shipment"
    )
    damage_bag_count = fields.Integer(
        string='Damage Bag Count', 
        compute='_compute_damage_bag_count', 
        store=True,
        help="Calculated number of damaged bags based on percentage"
    )
    gross_weight = fields.Float(
        string='Gross Weight (KG)', 
        required=True,
        help="Total weight including truck and coffee"
    )
    truck_weight = fields.Float(
        string='Truck Weight (KG)', 
        required=True,
        help="Weight of the empty truck"
    )
    net_weight = fields.Float(
        string='Net Weight (KG)', 
        compute='_compute_weights', 
        store=True,
        help="Gross weight minus truck weight"
    )
    empty_jute_bag_weight = fields.Float(
        string='Empty Jute Bag Weight (KG)', 
        default=0.0,
        help="Total weight of empty jute bags"
    )
    moisture_loss_adjustment = fields.Float(
        string='Moisture Loss Adjustment (KG)', 
        default=0.0,
        help="Weight adjustment for moisture loss"
    )
    grand_net_weight = fields.Float(
        string='Grand Net Weight (KG)', 
        compute='_compute_weights', 
        store=True,
        help="Final weight after all adjustments"
    )
    coffee_tea_weight = fields.Float(
        string='Coffee & Tea Weight (KG)',
        help="Exact weight of coffee & tea after avoiding other overhead",
        compute='_compute_coffee_tea_weight', 
        store=True
    )

    supplier_id = fields.Many2one(
        'res.partner',
        string='Supplier',
        related='arrival_id.supplier_id',
        store=True,
        readonly=True
    )

    arrival_date = fields.Date(
        string='Arrival Date',
        related='arrival_id.date',
        store=True,
        readonly=True
    )

    @api.depends('num_of_bags', 'damage_percentage')
    def _compute_damage_bag_count(self):
        for record in self:
            record.damage_bag_count = int(record.num_of_bags * (record.damage_percentage / 100.0))

    @api.depends('gross_weight', 'truck_weight', 'empty_jute_bag_weight', 'moisture_loss_adjustment')
    def _compute_weights(self):
        for record in self:
            record.net_weight = record.gross_weight - record.truck_weight
            if record.net_weight < 0:
                raise ValidationError(_(
                    "Net Weight cannot be negative (Gross: %s KG - Truck: %s KG = %s KG). "
                    "Please verify your weight measurements."
                ) % (record.gross_weight, record.truck_weight, record.net_weight))
            record.grand_net_weight = record.net_weight - record.moisture_loss_adjustment - record.empty_jute_bag_weight

    @api.depends('grand_net_weight')
    def _compute_coffee_tea_weight(self):
        for record in self:
            record.coffee_tea_weight = record.grand_net_weight

    def action_confirm_weight(self):
        self.ensure_one()

        # Validation checks
        if self.gross_weight <= 0:
            raise ValidationError(_("Gross Weight must be greater than zero. Current value: %s KG") % self.gross_weight)
        if self.truck_weight < 0:
            raise ValidationError(_("Truck Weight cannot be negative. Current value: %s KG") % self.truck_weight)
        if self.num_of_bags <= 0:
            raise ValidationError(_("Number of bags must be greater than zero. Current value: %s") % self.num_of_bags)
        if self.damage_percentage < 0 or self.damage_percentage > 100:
            raise ValidationError(_(
                "Damage percentage must be between 0% and 100%. Current value: %s%%"
            ) % self.damage_percentage)

        try:
            _logger.info(
                "Confirming weight for arrival %s:\n"
                "Gross: %s KG, Truck: %s KG, Net: %s KG\n"
                "Bags: %s, Damage: %s%% (%s bags)\n"
                "Final Coffee Weight: %s KG",
                self.arrival_id.coffee_issue_no,
                self.gross_weight, self.truck_weight, self.net_weight,
                self.num_of_bags, self.damage_percentage, self.damage_bag_count,
                self.coffee_tea_weight
            )

            self.env['coffee.weight.history.log'].create({
                'weight_history_id': self.id,
                'gross_weight': self.gross_weight,
                'truck_weight': self.truck_weight,
                'net_weight': self.net_weight,
                'num_of_bags': self.num_of_bags,
                'damage_percentage': self.damage_percentage,
                'user_id': self.env.user.id,
                'timestamp': fields.Datetime.now(),
            })

            # Remove the state change here. A separate action should be used to
            # move from 'weight_recorded' to 'done' after a user confirms.
            # self.arrival_id.state = 'done' # <-- REMOVE THIS LINE

            _logger.info("Weight confirmed for arrival %s", self.arrival_id.coffee_issue_no)

        except Exception as e:
            _logger.error(
                "Failed to confirm weight for arrival %s: %s",
                self.arrival_id.coffee_issue_no,
                str(e)
            )
            raise


    @api.model_create_multi
    def create(self, vals_list):
        # Call the original create method to create the weight history records
        records = super().create(vals_list)

        # Iterate over the newly created records and update the arrival state
        for record in records:
            if record.arrival_id:
                # Check the current state to prevent overwriting 'done' or 'ug_grade'
                if record.arrival_id.state not in ('done', 'ug_grade'):
                    record.arrival_id.state = 'weight_recorded'
                    _logger.info("Arrival %s state updated to 'weight_recorded' after creation of weight record.",
                                 record.arrival_id.coffee_issue_no)
        return records