from odoo import api, fields, models

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    is_credit = fields.Boolean(string="Is Credit Order")
    credit_approver_id = fields.Many2one(
        'res.partner',
        string="Credit For",
        help="Credit Order Belongs to"
    )

    def _create_invoices(self, grouped=False, final=False):
        for order in self:
            if order.is_credit and order.state in ['sale', 'done']:
                for line in order.order_line.filtered(lambda l: not l.display_type):
                    line.qty_to_invoice = line.product_uom_qty - line.qty_invoiced

        invoices = super()._create_invoices(grouped=grouped, final=final)

        for order in self.filtered(lambda o: o.is_credit and o.state in ['sale', 'done']):
            for line in order.order_line:
                if line.product_uom_qty <= line.qty_invoiced:
                    line.qty_to_invoice = 0

        self._compute_invoice_status()
        return invoices

    def _compute_invoice_status(self):
        for order in self:
            if order.is_credit and order.state in ['sale', 'done']:
                all_invoiced = all(
                    line.qty_invoiced >= line.product_uom_qty
                    for line in order.order_line
                    if not line.display_type
                )
                order.invoice_status = 'invoiced' if all_invoiced else 'to invoice'
            else:
                super(SaleOrder, order)._compute_invoice_status()


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def _prepare_invoice_line(self, **optional_values):
        if self.display_type:
            return super()._prepare_invoice_line(**optional_values)

        vals = super()._prepare_invoice_line(**optional_values)
        if self.order_id.is_credit and self.order_id.state in ['sale', 'done'] and vals:
            vals['quantity'] = self.product_uom_qty
        return vals
