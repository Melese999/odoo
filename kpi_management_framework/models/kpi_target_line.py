# -*- coding: utf-8 -*-
from odoo import fields, models, api

import logging

_logger = logging.getLogger(__name__)


class KpiTargetLine(models.Model):
    _name = 'kpi.target.line'
    _description = 'KPI Target Line'
    _order = 'sequence, id'

    target_id = fields.Many2one('kpi.target', string='KPI Target', required=True, ondelete='cascade')
    sequence = fields.Integer(string='Sequence', default=10)

    kpi_definition_id  = fields.Many2one('kpi.definition', string='KPI', required=True, ondelete='cascade')

    target_value = fields.Float(string='Target Value', required=True)
    actual_value = fields.Float(string='Actual Value', readonly=True, default=0.0)
    achievement_percentage = fields.Float(
        string='Achievement (%)',
        compute='_compute_achievement_percentage',
        store=True
    )

    # Related fields from parent for context
    user_id = fields.Many2one(related='target_id.user_id', store=True)
    date_start = fields.Date(related='target_id.date_start', store=True)
    date_end = fields.Date(related='target_id.date_end', store=True)

    @api.depends('actual_value', 'target_value')
    def _compute_achievement_percentage(self):
        for line in self:
            if line.target_value > 0:
                line.achievement_percentage = (line.actual_value / line.target_value) * 100
            else:
                line.achievement_percentage = 0.0

