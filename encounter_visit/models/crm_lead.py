from odoo import models, fields

class CrmLead(models.Model):
    _inherit = "crm.lead"

    encounter_visit_ids = fields.One2many("encounter.encounter_visit", "lead_id", string="Encounter Visits")
    encounter_visit_count = fields.Integer(compute="_compute_encounter_visit_count")

    def _compute_encounter_visit_count(self):
        for lead in self:
            lead.encounter_visit_count = len(lead.encounter_visit_ids)

    def action_view_encounter_visits(self):
        return {
            "name": "Encounter Visits",
            "type": "ir.actions.act_window",
            "res_model": "encounter.encounter_visit",
            "view_mode": "tree,form",
            "domain": [("lead_id", "=", self.id)],
            "context": {"default_lead_id": self.id, "default_partner_id": self.partner_id.id},
        }
