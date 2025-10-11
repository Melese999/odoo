{
    "name": "CRM Telemarketing",
    "summary": "Telemarketing calls (inbound/outbound), reporting, and dashboards",
    "version": "17.0.1.2.0", # Incremented version
    "author": "Custom",
    "license": "AGPL-3",
    "category": "Sales/CRM",
    "depends": [
        "crm",
        "crm_phonecall",
        # 'spreadsheet' and 'spreadsheet_dashboard' are now removed
        "sale_management",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/crm_telemarketing_status_views.xml",
        "views/crm_lead_views.xml",
        "views/crm_leads_views.xml",
        "views/telemarketing_report_views.xml",
        "views/telemarketing_dashboard_views.xml",
        "views/crm_phonecall_views.xml",
        # The two spreadsheet files have been removed from this list
    ],
    "assets": {
        "web.assets_backend": [
            # Using a reliable CDN for Chart.js
            "crm_telemarketing/static/src/js/chart.min.js",
            "crm_telemarketing/static/src/js/telemarketing_dashboard.js",
            "crm_telemarketing/static/src/xml/telemarketing_dashboard_templates.xml",
        ],
    },
    "installable": True,
    "application": False,
}