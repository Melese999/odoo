/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, onWillStart, onMounted, onWillUnmount, useState, useRef } from "@odoo/owl";

const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));

export class TelemarketingDashboard extends Component {
    setup() {
        this.rpc = useService("rpc");

        this.state = useState({
            filter: { start_date: null, end_date: null },
            kpis: {
                total_leads: 0,
                converted_leads: 0,
                conversion_rate: 0,
                total_calls: 0,
                avg_duration: 0,
                total_competitors:0
            },
            bar_chart: { labels: [], datasets: {} },
            pivot_table: { headers: [], rows: {} },
            salesperson_data: {}, 
        });

        this.barChartRef = useRef("bar_chart");
        this.charts = {};
        this.isPolling = true;

        onWillStart(() => this.loadDashboardData());

        onMounted(async () => {
            await this.loadDashboardData();
            this.renderCharts();
            this.pollData();
        });

        onWillUnmount(() => {
            this.isPolling = false;
            Object.values(this.charts).forEach(chart => chart.destroy());
        });
    }

    async pollData() {
        while (this.isPolling) {
            await sleep(60000);
            if (!this.isPolling) break;
            await this.loadDashboardData();
        }
    }

    async loadDashboardData() {
        const data = await this.rpc("/telemarketing/dashboard/data", {
            start_date: this.state.filter.start_date || '',
            end_date: this.state.filter.end_date || '',
        });
        if (!this.isPolling) return;

        this.state.kpis = data.kpis || this.state.kpis;
        this.state.bar_chart = data.bar_chart || { labels: [], datasets: {} };
        this.state.pivot_table = data.pivot_table || { headers: [], rows: {} };
        this.state.salesperson_data = data.salesperson_data || this.state.salesperson_data;
        // Render chart after data loaded
        this.renderCharts();
    }

    renderCharts() {
        const canvas = this.barChartRef.el;
        const chartData = this.state.bar_chart;
        if (!canvas || !chartData || !chartData.labels || chartData.labels.length === 0) return;

        if (this.charts.barChart) this.charts.barChart.destroy();

        const datasets = Object.entries(chartData.datasets).map(([label, data], i) => ({
            label: label.charAt(0).toUpperCase() + label.slice(1),
            data: chartData.labels.map(day => data[day] || 0),
            backgroundColor: i === 0 ? 'rgba(54, 162, 235, 0.6)' : 'rgba(255, 99, 132, 0.6)',
            borderColor: i === 0 ? 'rgb(54, 162, 235)' : 'rgb(255, 99, 132)',
            borderWidth: 1,
        }));

        this.charts.barChart = new Chart(canvas, {
            type: 'line',
            data: { labels: chartData.labels, datasets: datasets },
            options: {
                responsive: true,
                plugins: { legend: { position: 'top' } },
                scales: { x: { stacked: true }, y: { stacked: true, beginAtZero: true } },
            },
        });
    }

    applyFilter() {
        this.loadDashboardData();
    }
}

TelemarketingDashboard.template = "crm_telemarketing.TelemarketingDashboard";
registry.category("actions").add("telemarketing_dashboard", TelemarketingDashboard);
