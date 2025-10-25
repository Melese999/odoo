# -*- coding: utf-8 -*-
from odoo import fields, models, api


class CrmPhonecall(models.Model):
    _inherit = 'crm.phonecall'

    # 2. Add the Data Quality fields directly to crm.phonecall
    name_confirmed = fields.Boolean(string="Name Confirmed?", default=False)
    address_confirmed = fields.Boolean(string="Address Confirmed?", default=False)
    phone_confirmed = fields.Boolean(string="Phone Confirmed?", default=False)
    service_satisfaction_confirmed = fields.Boolean(string="Service Satisfaction Confirmed?", default=False)
    product_information_confirmed = fields.Boolean(string="Product Information Confirmed?", default=False)

    # 3. Add the Overall Score field (now computed directly on phonecall)
    overall_score = fields.Float(
        string='Overall Score (%)',
        compute='_compute_overall_score',
        store=True,
        digits=(5, 2)
    )

    # 4. Computation logic is moved here
    @api.depends('name_confirmed', 'address_confirmed', 'phone_confirmed',
                 'service_satisfaction_confirmed', 'product_information_confirmed')
    def _compute_overall_score(self):
        """Compute overall score immediately on phonecall record."""
        confirmation_fields = [
            'name_confirmed', 'address_confirmed', 'phone_confirmed',
            'service_satisfaction_confirmed', 'product_information_confirmed'
        ]
        total_fields = len(confirmation_fields)
        for record in self:
            confirmed_count = sum(record[field] for field in confirmation_fields)
            score = (confirmed_count / total_fields) * 100 if total_fields else 0.0
            record.overall_score = score

    def action_confirm_all_fields(self):
        """Sets all data quality confirmation fields to True on the phonecall record."""
        self.ensure_one()
        self.write({
            'name_confirmed': True,
            'address_confirmed': True,
            'phone_confirmed': True,
            'service_satisfaction_confirmed': True,
            'product_information_confirmed': True,
        })
        return True

    # Add the KPI trigger logic
    def _notify_kpi_target_update(self):
        """Notify kpi.target to recalculate values for the phonecall's user."""
        users_to_update = self.mapped('user_id')
        for user in users_to_update:
            self.env['kpi.target'].sudo()._update_targets_for_user(
                user.id, 'crm.phonecall'
            )

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        # 💡 FIX: Filter for 'open' records before notifying KPI.
        records.filtered(lambda r: r.state == 'open')._notify_kpi_target_update()
        return records

    def write(self, vals):
        # ... (rest of the write method logic which was not provided but is assumed to be correct)

        # Logic to notify KPI updates on state change or confirmation field change
        sync_needed = any(field in vals for field in
                          ['user_id', 'state', 'name_confirmed', 'address_confirmed', 'phone_confirmed',
                           'service_satisfaction_confirmed', 'product_information_confirmed'])

        # Pre-fetch records that will need an update
        records_to_notify = self.filtered(lambda r: r.state == 'open') if sync_needed else self.env['crm.phonecall']

        # Call super
        result = super().write(vals)

        # Notify targets if a relevant change occurred and the record is in 'open' state
        if sync_needed:
            # Check the state again after write, in case the state was changed to 'open'
            (records_to_notify | self.filtered(lambda r: r.state == 'open'))._notify_kpi_target_update()

        return result