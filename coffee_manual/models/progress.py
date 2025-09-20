from odoo import api, fields, models
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class CoffeeManualProgress(models.Model):
    _name = "coffee.manual.progress"
    _description = "Coffee Manual Progress"
    _rec_name = "user_id"
    _sql_constraints = [
        ("coffee_manual_progress_unique", "unique(user_id, section_id)", "Progress per section per user must be unique."),
    ]

    user_id = fields.Many2one("res.users", required=True, ondelete="cascade")
    section_id = fields.Many2one("coffee.manual.section", required=True, ondelete="cascade")
    status = fields.Selection(
        [
            ("not_started", "Not started"),
            ("in_progress", "In progress"),
            ("done", "Done"),
        ],
        default="not_started",
        required=True,
    )
    completed_at = fields.Datetime()

    def mark_done(self):
        for rec in self:
            rec.status = "done"
            rec.completed_at = fields.Datetime.now()

    @api.model
    def set_status(self, section_key: str, status: str):
        section = self.env["coffee.manual.section"].search([("key", "=", section_key)], limit=1)
        if not section:
            return False
        rec = self.search([("user_id", "=", self.env.user.id), ("section_id", "=", section.id)], limit=1)
        if not rec:
            rec = self.create({"user_id": self.env.user.id, "section_id": section.id})
        rec.status = status
        if status == "done" and not rec.completed_at:
            rec.completed_at = fields.Datetime.now()
        return True
