from odoo import models, fields, api
from odoo.exceptions import ValidationError

class EncounterVisit(models.Model):
    _name = "encounter.encounter_visit"
    _description = "Encounter Visit"
    _order = "date desc"
    _inherit = ["mail.thread", "mail.activity.mixin"]
   
    code = fields.Char(required=True, copy=False, readonly=True,
                       index=True, default="New", tracking=True)
    name = fields.Char(string="Title", required=True)
    date = fields.Datetime(string="Visit Date", default=fields.Datetime.now, required=True)

    lead_id = fields.Many2one("crm.lead", string="Lead/Opportunity", ondelete="cascade")
    partner_id = fields.Many2one("res.partner", string="Customer", ondelete="cascade")
    company_ids = fields.Many2many(
        comodel_name="res.company",
        string="Companys",
        index=True,
        readonly=True,
        help="Company's to which Encounter belongs to.",
    )
    team_id = fields.Many2one(
        comodel_name="crm.team",
        string="Sales Team",
        index=True,
        readonly=True,
        help="Sales team to which encounter belongs to.",
    )
    user_id = fields.Many2one(
        comodel_name="res.users",
        string="Responsible",
        readonly=True,
        default=lambda self: self.env.user,
    )
    latitude = fields.Float("Latitude", required=True)
    longitude = fields.Float("Longitude", required=True)
    notes = fields.Text("Notes")

    @api.constrains("latitude", "longitude")
    def _check_location(self):
        for rec in self:
            if not rec.latitude or not rec.longitude:
                raise ValidationError("Location (Latitude & Longitude) is required for Encounter Visit.")
    
    @api.onchange("lead_id")
    def _onchange_opportunity_id(self):
        """Based on Leads, change contact, partner, team."""
        if self.lead_id:
            self.partner_id = False
            self.team_id = self.lead_id.team_id.id
            self.user_id = self.lead_id.user_id.id
            self.company_ids = self.lead_id.company_ids.ids
    
    @api.onchange("partner_id")
    def _onchange_partner_id(self):
        if self.partner_id:
            self.lead_id = False   # clear lead if partner is selected
            self.team_id = self.partner_id.team_id.id
            self.user_id = self.partner_id.user_id.id
            self.company_ids = self.partner_id.company_id.id


    @api.model
    def create(self, vals):
        vals["code"] = self.env["ir.sequence"].sudo().next_by_code("encounter.encounter_visit") or "New"
        return super(EncounterVisit, self).create(vals)
