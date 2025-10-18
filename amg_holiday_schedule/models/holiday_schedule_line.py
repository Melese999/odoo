from odoo import fields, models
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class HolidayScheduleLine(models.Model):
    _name = 'holiday.schedule.line'
    _description = 'Holiday Schedule Line'
    _order = 'date'
    schedule_id = fields.Many2one(
        'holiday.schedule',
        string='Schedule',
        required=True,
        ondelete='cascade'
    )

    name = fields.Char(required=True)
    date = fields.Date(required=True)