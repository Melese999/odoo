from odoo import models, fields, api


class CommissionSketchWizard(models.TransientModel):
    _name = 'commission.sketch.wizard'
    _description = 'Commission System Sketch Wizard'

    sketch_image = fields.Binary(string="Sketch", attachment=False)
    order_line_id = fields.Many2one('sale.order.line', string="Order Line", required=True)
    description = fields.Char(string="Description", help="Brief description of the sketch")

    @api.model
    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)
        if self._context.get('default_order_line_id'):
            defaults['order_line_id'] = self._context['default_order_line_id']
        return defaults

    def action_save_sketch(self):
        self.ensure_one()
        if self.sketch_image:
            # Create an attachment linked to the sale order line
            attachment = self.env['ir.attachment'].create({
                'name': f"Design Sketch: {self.description or self.order_line_id.product_id.name}",
                'datas': self.sketch_image,
                'res_model': 'sale.order.line',
                'res_id': self.order_line_id.id,
                'description': f"Design sketch for {self.order_line_id.product_id.name} in order {self.order_line_id.order_id.name}",
            })

            # Add a message to the sales order chatter
            self.order_line_id.order_id.message_post(
                body=f"Design sketch added for product: {self.order_line_id.product_id.name}",
                attachment_ids=[attachment.id]
            )

        return {'type': 'ir.actions.act_window_close'}

    def action_clear_sketch(self):
        self.write({'sketch_image': False})
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }