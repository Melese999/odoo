
{
    "name": "Sequential Code for Leads / Opportunities",
    "version": "17.0.1.1.1",
    "category": "CRM",
    "author": "Tecnativa, AvanzOSC, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/crm",
    "license": "AGPL-3",
    "depends": ["crm"],
    "data": [
        "data/lead_sequence.xml",
        "views/crm_lead_view.xml"],
    "installable": True,
    "pre_init_hook": "create_code_equal_to_id",
    "post_init_hook": "assign_old_sequences",
}
