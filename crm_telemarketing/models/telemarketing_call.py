from odoo import models, fields, api

class CrmTelemarketingCall(models.Model):
    _name = "crm.telemarketing.call"
    _inherit = ['mail.thread', 'mail.activity.mixin'] # Keeps chatter functionality
    _description = "Telemarketing Call log"
    _order = "date desc"

    # ... other fields like lead_id, date, etc. ...

    # [FIXED] The state field is now aligned with the crm.phonecall model
    state = fields.Selection(
        [
            ('open', 'Confirmed'),
            ('cancel', 'Cancelled'),
            ('pending', 'Pending'),
            ('done', 'Held'),
        ],
        string="Status",
        default="open",
        required=True,
        tracking=True # This parameter now works correctly
    )

    # ... all other fields and methods remain the same ...
    lead_id = fields.Many2one("crm.lead", string="Lead/Opportunity", ondelete="cascade", required=True)
    date = fields.Datetime(default=fields.Datetime.now, required=True)
    direction = fields.Selection(
        [("inbound", "Inbound"), ("outbound", "Outbound")],
        default="outbound", required=True
    )
    duration = fields.Integer("Duration (seconds)")
    phone = fields.Char("Phone")
    user_id = fields.Many2one("res.users", default=lambda self: self.env.uid, string="Responsible")
    status_id = fields.Many2one("crm.telemarketing.status", string="Detailed Status") # Renamed for clarity
    note = fields.Text()
    call_type = fields.Selection(
        [("sales", "Sales Call"), ("survey", "Satisfaction Survey")],
        string="Call Type", default="sales", required=True
    )
    brand_awareness_created = fields.Boolean(string="Brand Awareness Created")
    quality_rating = fields.Selection(
        [('1', '⭐'), ('2', '⭐⭐'), ('3', '⭐⭐⭐'), ('4', '⭐⭐⭐⭐'), ('5', '⭐⭐⭐⭐⭐')],
        string="Quality of Info Delivered"
    )
    sale_order_ids = fields.Many2many("sale.order", string="Generated Orders")
    detailed_info_provided = fields.Boolean(string="Detailed Info Provided")
    follow_up_scheduled = fields.Boolean(string="Follow-up Scheduled")
    name_confirmed = fields.Boolean(string="Name Confirmed")
    address_confirmed = fields.Boolean(string="Address Confirmed")
    phone_confirmed = fields.Boolean(string="Phone Confirmed")
    service_rating = fields.Selection(
        [('1', 'Poor'), ('2', 'Fair'), ('3', 'Good'), ('4', 'Very Good'), ('5', 'Excellent')],
        string="Service Satisfaction"
    )
    product_rating = fields.Selection(
        [('1', 'Poor'), ('2', 'Fair'), ('3', 'Good'), ('4', 'Very Good'), ('5', 'Excellent')],
        string="Product Satisfaction"
    )

    @api.onchange('status_id')
    def _onchange_status_id(self):
        """
        This onchange is now less critical as the main state is managed separately,
        but can be kept for other automations if needed.
        """
        pass