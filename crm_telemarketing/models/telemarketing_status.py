from odoo import models, fields

class CrmTelemarketingStatus(models.Model):
    _name = 'crm.telemarketing.status'
    _description = 'Telemarketing Call Status'
    _order = 'sequence'

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    sequence = fields.Integer(default=10)
    status_type = fields.Selection([
        ('open', 'In Progress'),
        ('done', 'Done'),
        ('pending', 'Pending'),
    ], string="Type", required=True, default='open',
        help="Categorize this status for reporting and automation.\n"
             "- In Progress: The call is open and needs action.\n"
             "- Done: The call is successfully completed.\n"
             "- Pending: The call is waiting for something (e.g., redial).")