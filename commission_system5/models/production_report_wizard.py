# commission_system/models/wizard/production_report_wizard.py
from odoo import models, fields


class ProductionReportWizard(models.TransientModel):
    _name = 'production.report.wizard'
    _description = 'Production Order Report Wizard'

    sale_order_id = fields.Many2one(
        'sale.order',
        string="Sales Order",
        required=True,
        help="Select the sales order to generate the production report for."
    )

    def action_generate_report(self):
        """
        Action to generate the production order report.
        """
        # Find all manufacturing orders associated with the selected sales order
        mrp_productions = self.env['mrp.production'].search([
            ('origin', '=', self.sale_order_id.name)
        ])

        if not mrp_productions:
            raise models.ValidationError("No manufacturing orders found for this sales order.")

        # Return the report action. The report will be generated for the found MOs.
        return self.env.ref(
            'commission_system.action_report_production_order'
        ).report_action(mrp_productions)

