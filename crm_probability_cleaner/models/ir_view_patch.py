from odoo import SUPERUSER_ID

import logging, re
from lxml import etree

_logger = logging.getLogger(__name__)

def remove_probability_from_views(env):
    """Post-init hook for Odoo 17: remove <field name='probability'> from views."""
    # Use env directly, no need for cr/registry
    views = env['ir.ui.view'].sudo().search([('arch_db', 'ilike', 'probability')])
    _logger.info("crm_probability_cleaner: scanning %d view(s) for 'probability'", len(views))

    for view in views:
        arch = view.arch_db or ''
        new_arch = arch
        try:
            doc = etree.fromstring(arch.encode('utf-8'))
            changed = False

            # Remove probability fields
            for node in doc.xpath("//field[@name='probability']"):
                node.getparent().remove(node)
                changed = True

            # Remove labels for probability
            for lab in doc.xpath("//label[@for='probability']"):
                lab.getparent().remove(lab)
                changed = True

            if changed:
                new_arch = etree.tostring(doc, encoding='utf-8').decode('utf-8')

        except Exception:
            # fallback regex removal
            new_arch = re.sub(
                r"<field\b[^>]*\bname\s*=\s*['\"]probability['\"][^>]*\/?>",
                "",
                arch,
                flags=re.IGNORECASE
            )
            new_arch = re.sub(
                r"<label\b[^>]*\bfor\s*=\s*['\"]probability['\"][^>]*\/?>",
                "",
                new_arch,
                flags=re.IGNORECASE
            )

        if new_arch != arch:
            view.write({'arch_db': new_arch})
            _logger.info("crm_probability_cleaner: cleaned probability from view %s", view.xml_id or view.id)
