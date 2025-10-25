from odoo import fields, models
import logging
_logger = logging.getLogger(__name__)

class KpiConfirmationType(models.Model):
    _name = 'kpi.confirmation.type'
    _description = 'KPI Data Quality Confirmation Type'

    name = fields.Char(string='Confirmation Type', required=True)
    field_key = fields.Char(string='Field Key', required=True, help="The field name on the source document (e.g., crm.phonecall)")
    _sql_constraints = [
        ('field_key_unique', 'unique(field_key)', 'The field key must be unique!'),
    ]

# You would populate this model using an XML data file (kpi_data.xml or new_data.xml):
# <record id="conf_name" model="kpi.confirmation.type">
#     <field name="name">Name Confirmation</field>
#     <field name="field_key">name_confirmed</field>
# </record>
# ... and so on for all 5 fields.