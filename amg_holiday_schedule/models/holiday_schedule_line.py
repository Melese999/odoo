from odoo import fields, models, api
import logging
_logger = logging.getLogger(__name__)


class HolidayScheduleLine(models.Model):
    _name = 'holiday.schedule.line'
    _description = 'Holiday Schedule Line'
    _order = 'holiday_date desc'

    schedule_id = fields.Many2one(
        'holiday.schedule',
        string='Holiday Schedule',
        required=True,
        ondelete='cascade',
        index=True
    )
    holiday_date = fields.Date(string='Holiday Date', required=True, index=True)
    name = fields.Char(string='Description', required=True)

    _sql_constraints = [
        ('unique_holiday_date_per_schedule',
         'UNIQUE(schedule_id, holiday_date)',
         'A holiday date must be unique per schedule.'),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        # Clear cache for KPI working days computation
        self.env.cache.invalidate()
        return records

    def write(self, vals):
        res = super().write(vals)
        # Clear cache for KPI working days computation
        self.env.cache.invalidate()
        return res

    def unlink(self):
        # Clear cache for KPI working days computation
        self.env.cache.invalidate()
        return super().unlink()