from odoo import fields, models, tools


class ReportTelemarketing(models.Model):
    _name = "report.telemarketing"
    _description = "Telemarketing Report"
    _auto = False
    _rec_name = "date"

    date = fields.Datetime("Date", readonly=True)
    user_id = fields.Many2one("res.users", "Responsible", readonly=True)
    lead_id = fields.Many2one("crm.lead", "Lead/Opportunity", readonly=True)
    call_type = fields.Selection([("sales", "Sales Call"), ("survey", "Satisfaction Survey")], string="Call Type",
                                 readonly=True)
    call_status_display = fields.Char("Status", readonly=True)

    # [FIXED] The 'direction' field has been added back to the model definition
    direction = fields.Selection(
        [("inbound", "Inbound"), ("outbound", "Outbound")],
        string="Direction", readonly=True
    )

    duration = fields.Float("Duration (min)", readonly=True)
    total_calls = fields.Integer("Total Calls", readonly=True)
    done_calls = fields.Integer("Completed Calls", readonly=True)
    brand_awareness_created = fields.Integer(string="# Brand Awareness", readonly=True)
    orders_generated = fields.Integer(string="# Orders Generated", readonly=True)
    quality_rating = fields.Selection([('1', '⭐'), ('2', '⭐⭐'), ('3', '⭐⭐⭐'), ('4', '⭐⭐⭐⭐'), ('5', '⭐⭐⭐⭐⭐')],
                                      string="Quality Rating", readonly=True)
    avg_service_rating = fields.Float(string="Avg Service Rating", readonly=True, group_operator='avg')
    avg_product_rating = fields.Float(string="Avg Product Rating", readonly=True, group_operator='avg')
    status_id = fields.Many2one("crm.telemarketing.status", "Status Ref", readonly=True)
    source_model = fields.Selection([("telemarketing", "Telemarketing"), ("phonecall", "Phone Call")], string="Source",
                                    readonly=True)
    pending_calls = fields.Integer("Pending Calls", readonly=True)

    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute("""
                         CREATE or REPLACE VIEW report_telemarketing AS
                         (
                         -- Telemarketing Calls from this module
                         SELECT c.id,
                                c.date,
                                c.user_id,
                                c.lead_id,
                                c.call_type,
                                CASE c.state
                                    WHEN 'open' THEN 'Confirmed'
                                    WHEN 'cancel' THEN 'Cancelled'
                                    WHEN 'pending' THEN 'Pending'
                                    WHEN 'done' THEN 'Held'
                                    ELSE c.state
                                    END                                               as call_status_display,
                                c.direction, -- This SELECT is correct
                                (c.duration / 60.0)                                   as duration,
                                1                                                     as total_calls,
                                CASE WHEN c.state = 'done' THEN 1 ELSE 0 END          as done_calls,
                                CASE WHEN c.brand_awareness_created THEN 1 ELSE 0 END as brand_awareness_created,
                                (SELECT COUNT(*)
                                 FROM crm_telemarketing_call_sale_order_rel so_rel
                                 WHERE so_rel.crm_telemarketing_call_id = c.id)       as orders_generated,
                                c.quality_rating,
                                CAST(c.service_rating AS FLOAT)                       as avg_service_rating,
                                CAST(c.product_rating AS FLOAT)                       as avg_product_rating,
                                c.status_id,
                                'telemarketing_dashboard'                                       as source_model,
                                CASE WHEN c.state = 'pending' THEN 1 ELSE 0 END       as pending_calls
                         FROM crm_telemarketing_call c

                         UNION ALL

                         -- Standard Odoo Phonecalls (Logged Calls)
                         SELECT p.id + 2000000                                                  as id,
                                p.date,
                                p.user_id,
                                p.opportunity_id                                                as lead_id,
                                'sales'                                                         as call_type,
                                CASE p.state
                                    WHEN 'open' THEN 'Confirmed'
                                    WHEN 'cancel' THEN 'Cancelled'
                                    WHEN 'pending' THEN 'Pending'
                                    WHEN 'done' THEN 'Held'
                                    ELSE p.state
                                    END                                                         as call_status_display,
                                CASE WHEN p.direction = 'in' THEN 'inbound' ELSE 'outbound' END as direction, -- This SELECT is also correct
                                p.duration,
                                1                                                               as total_calls,
                                CASE WHEN p.state = 'done' THEN 1 ELSE 0 END                    as done_calls,
                                0                                                               as brand_awareness_created,
                                0                                                               as orders_generated,
                                NULL                                                            as quality_rating,
                                CAST(p.service_rating AS FLOAT)                                 as avg_service_rating,
                                CAST(p.product_rating AS FLOAT)                                 as avg_product_rating,
                                NULL                                                            as status_id,
                                'phonecall'                                                     as source_model,
                                CASE WHEN p.state = 'pending' THEN 1 ELSE 0 END                 as pending_calls
                         FROM crm_phonecall p
                             )
                         """)