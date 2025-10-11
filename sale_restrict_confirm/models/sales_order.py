from odoo import models, api
from odoo.exceptions import UserError

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_confirm(self):
        """
        Prevent specific users or groups from confirming quotations.
        """
        # Restrict by group (recommended)
        restricted_group = self.env.ref('sale_restrict_confirm.group_restricted_users')
        if self.env.user in restricted_group.users:
            raise UserError("You are not allowed to confirm quotations.")

        # Otherwise, proceed normally
        return super(SaleOrder, self).action_confirm()

    def action_create_invoice(self):
        """
        Prevent specific users or groups from creating invoices.
        """
        # Restrict by group
        restricted_group = self.env.ref('sale_restrict_confirm.group_restricted_users')
        if self.env.user in restricted_group.users:
            raise UserError("You are not allowed to create invoices for this order.")

        # Otherwise, proceed normally
        return super(SaleOrder, self).action_create_invoice()
