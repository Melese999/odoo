# -*- coding: utf-8 -*-
from odoo import models, api


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    def _notify_kpi_target_update(self):
        """Notify kpi.target to recalculate values for the lead's user."""
        users_to_update = self.mapped('user_id')
        for user in users_to_update:
            # We call the target update method in sudo because a sales user might
            # not have write access to kpi.target
            self.env['kpi.target'].sudo()._update_targets_for_user(
                user.id, 'crm.lead'
            )

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        # Trigger update on creation (Lead Registered KPI)
        records._notify_kpi_target_update()
        return records

    def write(self, vals):
        # Notify targets if the owner (user_id) is changed, as this affects the KPI history
        if 'user_id' in vals:
            users_before = self.mapped('user_id')
            res = super().write(vals)
            users_after = self.mapped('user_id')

            # Update targets for all affected users (old and new)
            (users_before | users_after)._notify_kpi_target_update()
            return res

        return super().write(vals)