from odoo import http
from odoo.http import request
from collections import defaultdict

class TelemarketingDashboardController(http.Controller):

    @http.route('/telemarketing/dashboard/data', type='json', auth='user')
    def get_dashboard_data(self):
        """
        A single endpoint to fetch all data required for the OWL dashboard.
        """
        Report = request.env['report.telemarketing']

        # 1. KPI Data
        kpi_data = Report.read_group(
            domain=[],
            fields=['total_calls', 'done_calls', 'pending_calls', 'duration'],
            groupby=[]
        )
        if kpi_data:
            kpis = kpi_data[0]
            total = kpis.get('total_calls', 0)
            done = kpis.get('done_calls', 0)
            completion_rate = (done / total * 100.0) if total > 0 else 0.0
            avg_duration = kpis.get('duration', 0)
        else:
            kpis, total, done, completion_rate, avg_duration = {}, 0, 0, 0, 0

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
            user_name = rec['user_id'][1] if rec['user_id'] else "Unassigned"
            direction = rec['direction']
            pivot_data[user_name][f"{direction}_total"] = rec['total_calls']
            pivot_data[user_name][f"{direction}_done"] = rec['done_calls']
            pivot_data[user_name][f"{direction}_pending"] = rec['pending_calls']

        return {
            'kpis': {
                'total_calls': total,
                'done_calls': done,
                'pending_calls': kpis.get('pending_calls', 0),
                'avg_duration': round(avg_duration, 2),
                'completion_rate': round(completion_rate, 2),
            },
            'bar_chart': bar_chart_data,
            'pivot_table': {
                'headers': ['Inbound', 'Outbound'], # For dynamic column generation
                'rows': pivot_data
            },
        }