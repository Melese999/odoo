# -*- coding: utf-8 -*-
from odoo import fields, models

class HolidaySchedule(models.Model):
    _name = 'holiday.schedule'
    _description = 'Holiday Schedule'

    name = fields.Char(string='Schedule Name', required=True, help="e.g., Ethiopian Holidays 2025")
    active = fields.Boolean(default=True)
    line_ids = fields.One2many('holiday.schedule.line', 'schedule_id', string='Holidays')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)