/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, onWillStart, onMounted, onPatched, onWillUnmount, useState, useRef } from "@odoo/owl";

const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));

export class TelemarketingDashboard extends Component {
    setup() {
        this.rpc = useService("rpc");
        this.state = useState({
            kpis: {},
            bar_chart: { labels: [], datasets: {} },
            pivot_table: { headers: [], rows: {} },
        });

        this.barChartRef = useRef("bar_chart");
        this.charts = {};
        this.isPolling = true;

        onWillStart(() => this.loadDashboardData());
        onMounted(() => {
            this.renderCharts();
            this.pollData();
        });
        onPatched(() => this.renderCharts());
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
        const data = await this.rpc("/telemarketing/dashboard/data", {});
        if (!this.isPolling) return;
        this.state.kpis = data.kpis;
        this.state.bar_chart = data.bar_chart;
        this.state.pivot_table = data.pivot_table;
    }

    renderCharts() {
        if (this.barChartRef.el) {
            this.renderBarChart('barChart', this.barChartRef.el, this.state.bar_chart);
        }
    }

    renderBarChart(chartKey, canvas, chartData) {
        if (this.charts[chartKey]) {
            this.charts[chartKey].destroy();
        }
        if (!canvas || !chartData.labels.length) return;

        const datasets = Object.entries(chartData.datasets).map(([label, data], index) => {
            const color = index === 0 ? 'rgba(54, 162, 235, 0.6)' : 'rgba(255, 99, 132, 0.6)';
            const borderColor = index === 0 ? 'rgb(54, 162, 235)' : 'rgb(255, 99, 132)';
            return {
                label: label.charAt(0).toUpperCase() + label.slice(1), // Capitalize
                data: chartData.labels.map(day => data[day] || 0),
                backgroundColor: color,
                borderColor: borderColor,
                borderWidth: 1,
            };
        });

        this.charts[chartKey] = new Chart(canvas, {
            type: 'bar',
            data: {
                labels: chartData.labels,
                datasets: datasets,
            },
            options: {
                responsive: true,
                plugins: { legend: { position: 'top' } },
                scales: {
                    x: { stacked: true },
                    y: { stacked: true, beginAtZero: true }
                }
            },
        });
    }
}

TelemarketingDashboard.template = "crm_telemarketing.TelemarketingDashboard";
registry.category("actions").add("telemarketing_dashboard", TelemarketingDashboard);