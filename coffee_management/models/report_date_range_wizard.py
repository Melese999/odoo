# -*- coding: utf-8 -*-
from odoo import fields, models


class ReportDateRangeWizard(models.TransientModel):
    _name = 'report.date.range.wizard'
    _description = 'Report Date Range Wizard'

    date_from = fields.Date(string='Start Date', required=True)
    date_to = fields.Date(string='End Date', required=True)

    def check_report(self):
        """
        Method to open the corresponding report based on the context.
        The context is passed from the menu item action.
        """
        # Get the report model name from the action's context
        report_model = self.env.context.get('report_model')
        if not report_model:
            return

        data = {
            'date_from': self.date_from,
            'date_to': self.date_to,
        }

        # Return the report action, which will generate the report using the QWeb template
        # Make sure to replace 'your_module_name' with your actual module's technical name.
        return self.env.ref(f'coffee_management.{report_model}_document').report_action(self, data=data)



