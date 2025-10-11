# models/report_telemarketing_dashboard.py
from odoo import api, fields, models

class ReportTelemarketingDashboard(models.TransientModel):
    _name = "report.telemarketing_dashboard.dashboard"
    _description = "Telemarketing Dashboard (Transient)"

    total_calls = fields.Integer("Total Calls", compute="_compute_dashboard_data", readonly=True)
    done_calls = fields.Integer("Completed Calls", compute="_compute_dashboard_data", readonly=True)
    pending_calls = fields.Integer("Pending Calls", compute="_compute_dashboard_data", readonly=True)
    avg_duration = fields.Float("Average Duration (min)", compute="_compute_dashboard_data", readonly=True)
    completion_rate = fields.Float("Completion Rate (%)", compute="_compute_dashboard_data", readonly=True)

    @api.depends()
    def _compute_dashboard_data(self):
        # Fetch data once for all records in the recordset
        dashboard_data = self.get_dashboard_data()
        for record in self:
            record.total_calls = dashboard_data["total_calls"]
            record.done_calls = dashboard_data["done_calls"]
            record.pending_calls = dashboard_data["pending_calls"]
            record.avg_duration = dashboard_data["avg_duration"]
            record.completion_rate = dashboard_data["completion_rate"]


    @api.model
    def get_dashboard_data(self):
        # Using self.env.cr.execute is okay, but it's generally better to use the ORM
        # even for reports when possible to benefit from security rules, though for _auto_false views it's common.
        # For simplicity and consistency with the original code, I'll keep the direct SQL here.
        self.env.cr.execute("""
                            SELECT
                                SUM(total_calls) as total,
                                SUM(done_calls) as done,
                                SUM(pending_calls) as pending,
                                AVG(duration) as avg_duration
                            FROM report_telemarketing
                            """)
        row = self.env.cr.dictfetchone()
        total = row["total"] or 0
        done = row["done"] or 0
        pending = row["pending"] or 0
        avg_duration = row["avg_duration"] or 0.0
        completion_rate = (done / total * 100.0) if total > 0 else 0.0

        return {
            "total_calls": total,
            "done_calls": done,
            "pending_calls": pending,
            "avg_duration": avg_duration,
            "completion_rate": completion_rate,
        }