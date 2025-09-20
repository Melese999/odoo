# -*- coding: utf-8 -*-
from odoo import fields, models, api
from odoo.exceptions import UserError
from datetime import datetime, timedelta


class ReportDateRangeWizard(models.TransientModel):
    _name = 'report.date.range.wizard'
    _description = 'Report Date Range Wizard'

    date_from = fields.Date(string='Start Date', required=True, default=fields.Date.context_today)
    date_to = fields.Date(string='End Date', required=True, default=fields.Date.context_today)
    report_model = fields.Char(string='Report Model')

    @api.model
    def default_get(self, fields_list):
        res = super(ReportDateRangeWizard, self).default_get(fields_list)
        # Get the report model from context if passed from menu
        if self._context.get('default_report_model'):
            res['report_model'] = self._context.get('default_report_model')
        return res

    def check_report(self):
        self.ensure_one()

        # Validate date range
        if self.date_from > self.date_to:
            raise UserError("From Date must be before To Date.")

        # Determine which report to generate based on the report_model field
        if not self.report_model:
            # Try to get from context if not set in the wizard
            self.report_model = self._context.get('report_model', '')

        if not self.report_model:
            raise UserError("No report type specified.")

        # Map report models to their corresponding actions
        report_actions = {
            'report.coffee.arrival_quality': {
                'type': 'ir.actions.report',
                'report_name': 'coffee_management.report_coffee_arrival_quality_document',
                'report_type': 'qweb-pdf',
            },
            'report.coffee.stock_movement': {
                'type': 'ir.actions.report',
                'report_name': 'coffee_management.report_coffee_stock_movement_document',
                'report_type': 'qweb-pdf',
            },
            'report.coffee.contract_fulfillment': {
                'type': 'ir.actions.report',
                'report_name': 'coffee_management.report_coffee_contract_fulfillment_document',
                'report_type': 'qweb-pdf',
            },
            'report.coffee.manufacturing_production': {
                'type': 'ir.actions.report',
                'report_name': 'coffee_management.report_coffee_manufacturing_production_document',
                'report_type': 'qweb-pdf',
            }
        }

        if self.report_model not in report_actions:
            raise UserError(f"Unknown report type: {self.report_model}")

        # Return the appropriate report action
        action = report_actions[self.report_model].copy()
        action['context'] = {'active_ids': [self.id], 'active_model': self._name}
        return action

    def get_report_data(self, date_from, date_to, report_type):
        """
        Central method to get report data based on type.
        This method will be called from the QWeb templates.
        """
        report_methods = {
            'arrival_quality': self.env['report.coffee.arrival_quality']._get_report_data,
            'stock_movement': self.env['report.coffee.stock_movement']._get_report_data,
            'contract_fulfillment': self.env['report.coffee.contract_fulfillment']._get_report_data,
            'manufacturing_production': self.env['report.coffee.manufacturing_production']._get_report_data,
        }

        if report_type not in report_methods:
            return {}

        return report_methods[report_type](date_from, date_to)


class CoffeeArrivalQualityReport(models.AbstractModel):
    _name = 'report.coffee.arrival_quality'
    _description = 'Coffee Arrival and Quality Evaluation Report'

    def _get_report_data(self, date_from, date_to):
        """
        Fetches and processes data for the Arrival and Quality Report.

        :param date_from: The start date for the report.
        :param date_to: The end date for the report.
        :return: A dictionary containing a list of arrival records and summary data.
        """
        # Use the correct field name 'date' instead of 'arrival_date'
        arrivals = self.env['coffee.arrival'].search([
            ('date', '>=', date_from),
            ('date', '<=', date_to),
            ('state', 'in', ['done', 'quality_evaluated'])  # Filter for completed and evaluated arrivals
        ])

        report_data = {
            'arrivals': [],
            'summary': {
                'total_arrivals': len(arrivals),
                'total_kg': 0.0,
                'avg_moisture': 0.0,
                'avg_score': 0.0,
                'low_grade_count': 0,
            }
        }

        if not arrivals:
            return report_data

        total_moisture = 0.0
        total_score = 0.0
        arrivals_with_quality = 0  # Count of arrivals that actually have quality evaluation

        for arrival in arrivals:
            # Get weight data
            net_weight = arrival.weight_history_id.net_weight if arrival.weight_history_id else 0.0

            # Get quality evaluation data
            moisture_content = 0.0
            total_score_val = 0.0
            amg_grade = ''

            if arrival.quality_evaluation_id:
                moisture_content = arrival.quality_evaluation_id.moisture_content or 0.0
                total_score_val = arrival.quality_evaluation_id.total_score or 0.0
                amg_grade = arrival.quality_evaluation_id.amg_grade or ''
                arrivals_with_quality += 1

            report_data['arrivals'].append({
                'issue_no': arrival.coffee_issue_no or '',
                'supplier_name': arrival.supplier_id.name or '',
                'arrival_date': arrival.date or '',
                'moisture_content': moisture_content,
                'total_score': total_score_val,
                'amg_grade': amg_grade,
                'net_weight_kg': net_weight,
            })

            report_data['summary']['total_kg'] += net_weight
            total_moisture += moisture_content
            total_score += total_score_val

            if amg_grade in ['UG', 'G5']:
                report_data['summary']['low_grade_count'] += 1

        # Calculate averages only for arrivals that have quality evaluation data
        if arrivals_with_quality > 0:
            report_data['summary']['avg_moisture'] = total_moisture / arrivals_with_quality
            report_data['summary']['avg_score'] = total_score / arrivals_with_quality
        else:
            report_data['summary']['avg_moisture'] = 0.0
            report_data['summary']['avg_score'] = 0.0

        return report_data


class CoffeeStockMovementReport(models.AbstractModel):
    _name = 'report.coffee.stock_movement'
    _description = 'Warehouse Stock and Movements Report'

    def _get_report_data(self, date_from, date_to):
        """
        Fetches and processes data for the Warehouse Stock and Movements Report.
        This report tracks stock balance and movements (receipts and issues)
        over a specified period.

        :param date_from: The start date of the period.
        :param date_to: The end date of the period.
        :return: A dictionary with a list of products and their stock movements.
        """
        # Get coffee products
        products = self.env['product.product'].search([('is_coffee_product', '=', True)])
        report_data = []

        for product in products:
            # Get beginning balance from stock quants before the period start
            beginning_balance_kg = 0.0
            try:
                # Try to get historical quantity if the method exists
                if hasattr(self.env['stock.quant'], '_get_historical_quantity'):
                    beginning_balance_kg = sum(
                        self.env['stock.quant']._get_historical_quantity(
                            product,
                            product.uom_id,
                            self.env['stock.location'].search([('usage', '=', 'internal')]),
                            to_date=date_from - timedelta(days=1)
                        )[0]
                    )
                else:
                    # Fallback to current quantity if historical method doesn't exist
                    beginning_balance_kg = product.qty_available
            except:
                beginning_balance_kg = product.qty_available

            # Sum receipts within the period
            received_kg = 0.0
            if hasattr(self.env, 'coffee_stock_receiving'):
                received_kg = sum(
                    self.env['coffee.stock.receiving'].search([
                        ('product_id', '=', product.id),
                        ('state', '=', 'done'),
                        ('create_date', '>=', date_from),
                        ('create_date', '<=', date_to)
                    ]).mapped('received_kg')
                )

            # Sum issues within the period
            issued_kg = 0.0
            if hasattr(self.env, 'coffee_stock_issue'):
                issued_kg = sum(
                    self.env['coffee.stock.issue'].search([
                        ('product_id', '=', product.id),
                        ('state', '=', 'done'),
                        ('create_date', '>=', date_from),
                        ('create_date', '<=', date_to)
                    ]).mapped('issued_kg')
                )

            ending_balance_kg = beginning_balance_kg + received_kg - issued_kg

            report_data.append({
                'product_name': product.name or '',
                'beginning_balance_kg': beginning_balance_kg,
                'received_kg': received_kg,
                'issued_kg': issued_kg,
                'ending_balance_kg': ending_balance_kg,
            })

        return {'stock_summary': report_data}


class CoffeeContractFulfillmentReport(models.AbstractModel):
    _name = 'report.coffee.contract_fulfillment'
    _description = 'Contract Fulfillment and Profitability Report'

    def _get_report_data(self, date_from, date_to):
        """
        Fetches and processes data for the Contract Fulfillment Report.

        :param date_from: The start date for the report.
        :param date_to: The end date for the report.
        :return: A dictionary containing a list of contracts and their fulfillment data.
        """
        contracts = self.env['coffee.contract'].search([
            ('contract_date', '>=', date_from),
            ('contract_date', '<=', date_to),
            ('state', 'in', ['confirmed', 'done'])
        ])

        report_data = {
            'contracts': [],
            'summary': {
                'total_contracts': len(contracts),
                'total_ordered_kg': 0.0,
                'total_delivered_kg': 0.0,
            }
        }

        if not contracts:
            return report_data

        for contract in contracts:
            total_ordered_kg = sum(
                line.quantity_kg for line in contract.contract_line_ids) if contract.contract_line_ids else 0.0
            delivered_kg = contract.delivered_kg or 0.0
            fulfillment_percentage = contract.fulfillment_percentage or 0.0
            total_contract_value = sum(
                line.subtotal_usd for line in contract.contract_line_ids) if contract.contract_line_ids else 0.0

            report_data['contracts'].append({
                'contract_number': contract.contract_number or '',
                'buyer_name': contract.buyer_id.name or '',
                'contract_date': contract.contract_date or '',
                 # === ADD THESE TWO LINES ===
                'shipment_period_month': contract.shipment_period_month,
                'shipment_period_year': contract.shipment_period_year,
                # === END OF ADDED LINES ===
                'state': contract.state or '',
                'total_ordered_kg': total_ordered_kg,
                'delivered_kg': delivered_kg,
                'fulfillment_percentage': fulfillment_percentage,
                'total_contract_value': total_contract_value
            })

            report_data['summary']['total_ordered_kg'] += total_ordered_kg
            report_data['summary']['total_delivered_kg'] += delivered_kg

        return report_data


class CoffeeManufacturingProductionReport(models.AbstractModel):
    _name = 'report.coffee.manufacturing_production'
    _description = 'Manufacturing and Production Report'

    def _get_report_data(self, date_from, date_to):
        """
        Fetches and processes data for the Manufacturing and Production Report.

        :param date_from: The start date for the report.
        :param date_to: The end date for the report.
        :return: A dictionary containing a list of MOs and a summary by state.
        """
        domain = [
            ('create_date', '>=', date_from),
            ('create_date', '<=', date_to)
        ]

        # Only add coffee_contract_id filter if the field exists
        if hasattr(self.env['mrp.production'], 'coffee_contract_id'):
            domain.append(('coffee_contract_id', '!=', False))

        mo_records = self.env['mrp.production'].search(domain)

        report_data = {
            'manufacturing_orders': [],
            'summary_by_state': {},
        }

        if not mo_records:
            return report_data

        for mo in mo_records:
            contract_number = mo.coffee_contract_id.contract_number if hasattr(mo,
                                                                               'coffee_contract_id') and mo.coffee_contract_id else ''

            # Safely get date fields with fallbacks for different Odoo versions
            start_date = ''
            end_date = ''

            # Try different possible field names for start date
            for field_name in ['date_planned_start', 'date_start', 'create_date']:
                if hasattr(mo, field_name):
                    start_date = getattr(mo, field_name) or ''
                    break

            # Try different possible field names for end date
            for field_name in ['date_finished', 'date_done', 'write_date']:
                if hasattr(mo, field_name):
                    end_date = getattr(mo, field_name) or ''
                    break

            report_data['manufacturing_orders'].append({
                'name': mo.name or '',
                'product_name': mo.product_id.name or '',
                'quantity_produced': mo.product_qty or 0.0,
                'state': mo.state or '',
                'contract_number': contract_number,
                'start_date': start_date,
                'end_date': end_date,
            })

            # Count MOs by state for the summary
            state = mo.state or 'unknown'
            report_data['summary_by_state'].setdefault(state, 0)
            report_data['summary_by_state'][state] += 1

        return report_data