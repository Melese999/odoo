from odoo import api, fields, models
import logging
_logger = logging.getLogger(__name__)


class HolidaySchedule(models.Model):
    _name = 'holiday.schedule'
    _description = 'Holiday Schedule'

    name = fields.Char(string='Schedule Name', required=True)
    active = fields.Boolean(default=True)
    line_ids = fields.One2many('holiday.schedule.line', 'schedule_id', string='Holiday Lines')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)

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