from odoo import models, fields

class ResPartner(models.Model):
    _inherit = "res.partner"

    encounter_visit_ids = fields.One2many("encounter.encounter_visit", "partner_id", string="Encounter Visits")
    encounter_visit_count = fields.Integer(compute="_compute_encounter_visit_count")

    def _compute_encounter_visit_count(self):
        for partner in self:
            partner.encounter_visit_count = len(partner.encounter_visit_ids)

    def action_view_encounter_visits(self):
        return {
            "name": "Encounter Visits",
            "type": "ir.actions.act_window",
            "res_model": "encounter.encounter_visit",
            "view_mode": "tree,form",
            "domain": [("partner_id", "=", self.id)],
            "context": {"default_partner_id": self.id},
        }
