from odoo import http
from odoo.http import request
from collections import defaultdict

class TelemarketingDashboardController(http.Controller):

    @http.route('/telemarketing/dashboard/data', type='json', auth='user')
    def get_dashboard_data(self, start_date=None, end_date=None):
        """
        Return KPIs and pivot table data for OWL dashboard, including total leads.
        """
        # Date filter
        domain = []
        if start_date:
            domain.append(('create_date', '>=', start_date))
        if end_date:
            domain.append(('create_date', '<=', end_date))

        # --- 1. Leads Data ---
        total_leads = request.env['crm.lead'].search_count(domain)
        total_competitors = request.env['competitor.competitor'].search_count(domain)
        converted_domain = domain + [('type', '=', 'opportunity')]
        converted_leads = request.env['crm.lead'].search_count(converted_domain)
        conversion_rate = 0
        if total_leads > 0:
            conversion_rate = (converted_leads / total_leads) * 100

        # --- 2. Call KPIs from report.telemarketing ---
        Report = request.env['report.telemarketing']
        call_data = Report.read_group(
            domain=[],
            fields=['total_calls', 'duration'],
            groupby=[]
        )
        if call_data:
            kpi_calls = call_data[0]
            total_calls = kpi_calls.get('total_calls', 0)
            avg_duration = kpi_calls.get('duration', 0)
        else:
            total_calls, done_calls, completion_rate, avg_duration = 0, 0, 0, 0

        # 2. Bar Chart Data: "Inbound vs Outbound by Day"
        chart_data_raw = Report.read_group(
            domain=[],
            fields=['total_calls'],
            groupby=['date:day', 'direction'],
            lazy=False
        )
        bar_chart_data = {'labels': [], 'datasets': {}}
        labels_set = set()
        for rec in chart_data_raw:
            day = rec['date:day']
            direction = rec['direction']
            count = rec['total_calls']
            labels_set.add(day)
            if direction not in bar_chart_data['datasets']:
                bar_chart_data['datasets'][direction] = {}
            bar_chart_data['datasets'][direction][day] = count
        bar_chart_data['labels'] = sorted(list(labels_set))


        # 3. Pivot Table Data: "Calls by User - Direction"
        pivot_data_raw = Report.read_group(
            domain=[],
            fields=['total_calls', 'done_calls', 'pending_calls'],
            groupby=['user_id', 'direction'],
            lazy=False
        )
        pivot_data = defaultdict(lambda: defaultdict(int))
        for rec in pivot_data_raw:
            user_name = rec['user_id'][1] if rec['user_id'] else 'Unassigned'
            direction = rec['direction']
            pivot_data[user_name][f"{direction}_total"] = rec['total_calls']
            pivot_data[user_name][f"{direction}_done"] = rec['done_calls']
            pivot_data[user_name][f"{direction}_pending"] = rec['pending_calls']

        salesperson_data = defaultdict(lambda: {
            'target': 0,
            'total_leads': 0,
            'converted_leads': 0,
            'conversion_rate': 0.0,
            'leads_registered_target': 0,
            'leads_registered_actual': 0,
            'leads_registered_percent': 0.0,
            'data_quality_target': 0,
            'data_quality_actual': 0,
            'data_quality_percent': 0.0,
        })

        Lead = request.env['crm.lead']
        leads = Lead.search(domain)

        # --- 1. Compute Leads and Conversion ---
        for lead in leads:
            if lead.user_id:
                sp = lead.user_id.name
                salesperson_data[sp]['total_leads'] += 1
                if lead.type == 'opportunity':
                    salesperson_data[sp]['converted_leads'] += 1

        for sp, data in salesperson_data.items():
            total = data['total_leads']
            converted = data['converted_leads']
            data['conversion_rate'] = round((converted / total) * 100, 2) if total else 0

        # --- 2. Fetch KPI Target Lines ---
        KpiLine = request.env['kpi.target.line']
        kpi_domain = []
        if start_date:
            kpi_domain.append(('date_start', '>=', start_date))
        if end_date:
            kpi_domain.append(('date_end', '<=', end_date))

        kpi_lines = KpiLine.search(kpi_domain)
        for line in kpi_lines:
            if line.user_id:
                sp = line.user_id.name
                if line.kpi_definition_id.kpi_type == 'leads_registered':
                    salesperson_data[sp]['leads_registered_target'] += line.target_value
                    salesperson_data[sp]['leads_registered_actual'] += line.actual_value
                    salesperson_data[sp]['leads_registered_percent'] = line.achievement_percentage or 0.0
                elif line.kpi_definition_id.kpi_type == 'data_quality':
                    salesperson_data[sp]['data_quality_target'] += line.target_value
                    salesperson_data[sp]['data_quality_actual'] += line.actual_value
                    salesperson_data[sp]['data_quality_percent'] = line.achievement_percentage or 0.0

        # --- 3. Prepare clean data for frontend ---
        result = []
        for sp, data in salesperson_data.items():
            result.append({
                'salesperson': sp,
                **data
            })


        
        return {
            'kpis': {
                'total_leads': total_leads,
                'converted_leads': converted_leads,
                'conversion_rate': conversion_rate,
                'total_calls': total_calls,
                'avg_duration': round(avg_duration, 2),
                'total_competitors':total_competitors
            },
            'bar_chart': bar_chart_data,
            'pivot_table': {
                'headers': ['Inbound', 'Outbound'],  # For dynamic column generation
                'rows': pivot_data,
            },
            'salesperson_data': result,

        }
