# models/crm_lead_extension.py

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import re

class LeadExtension(models.Model):
    _inherit = 'crm.lead'

    # 1. Add Industry / Company Type field
    # We use a selection field for consistency. You can change these values.
    company_type = fields.Selection([
        ('manufacturing', 'Manufacturing'),
        ('service', 'Service'),
        ('retail', 'Retail'),
        ('agriculture', 'Agriculture'),
        ('construction', 'Construction'),
        ('other', 'Other'),
    ], string="Industry / Company Type")

    # 2. Add TIN Number field
    tin_number = fields.Char(string="TIN Number")

    # 3. Add validations for Phone Number and Email
    @api.constrains('phone', 'mobile')
    def _check_phone_number(self):
        """ Validates phone and mobile numbers for Ethiopian format. """
        for lead in self:
            # This regex checks for formats like 09..., +2519..., 2519...
            # and allows for optional spaces or hyphens.
            phone_pattern = re.compile(r'^(?:\+251|251|0)?9[ -]?\d{2}[ -]?\d{3}[ -]?\d{3}$')
            
            if lead.phone and not phone_pattern.match(lead.phone):
                raise ValidationError(_(
                    "Invalid Phone Number format for '%s'. Please use a valid Ethiopian format (e.g., 0929046827 or +251939665679 or +25171234567)."
                ) % lead.phone)
            
            if lead.mobile and not phone_pattern.match(lead.mobile):
                raise ValidationError(_(
                    "Invalid Mobile Number format for '%s'. Please use a valid Ethiopian format (e.g., 0929046827 or +251939665679 or +25171234567)."
                ) % lead.mobile)

    @api.constrains('email_from')
    def _check_email_format(self):
        """ A simple email validation. Odoo has some built-in checks,
            but a constraint ensures it's always enforced on save. """
        for lead in self:
            if lead.email_from and '@' not in lead.email_from:
                raise ValidationError(_("'%s' is not a valid email address.") % lead.email_from)