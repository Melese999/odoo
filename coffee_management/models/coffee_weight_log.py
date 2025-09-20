from odoo import fields, models, api


class CoffeeWeightHistoryLog(models.Model):
    """Model to track historical weight records for auditing and tracking purposes."""
    _name = 'coffee.weight.history.log'
    _description = 'Coffee Weight History Log'
    _order = 'timestamp desc'

    weight_history_id = fields.Many2one(
        'coffee.weight.history',
        string='Weight Record',
        required=True,
        ondelete='cascade'
    )
    gross_weight = fields.Float(string='Gross Weight (KG)')
    truck_weight = fields.Float(string='Truck Weight (KG)')
    net_weight = fields.Float(string='Net Weight (KG)')
    num_of_bags = fields.Integer(string='Number of Bags')
    damage_percentage = fields.Float(string='Damage Percentage (%)')
    user_id = fields.Many2one(
        'res.users',
        string='Confirmed By',
        required=True
    )
    timestamp = fields.Datetime(string='Timestamp', required=True)
    arrival_id = fields.Many2one(
        related='weight_history_id.arrival_id',
        string='Arrival Record',
        store=True
    )
    coffee_issue_no = fields.Char(
        related='arrival_id.coffee_issue_no',
        string='Coffee Issue No.',
        store=True
    )
