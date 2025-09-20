from odoo import api, fields, models
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class CoffeeManualSection(models.Model):
    _name = "coffee.manual.section"
    _description = "Coffee Manual Section"
    _order = "sequence, id"

    name = fields.Char(required=True)
    key = fields.Selection(
        selection=[
            ("introduction", "Introduction"),
            ("level_1", "Level 1"),
            ("level_2", "Level 2"),
            ("level_3", "Level 3"),
            ("level_4", "Level 4"),
            ("level_5", "Level 5"),
            ("glossary", "Glossary"),
        ],
        required=True,
    )
    sequence = fields.Integer(default=10)
    anchor = fields.Char(help="Anchor id used in the QWeb template")
    badge_name = fields.Char(
            string="Badge Name", 
            help="The name of the badge earned for completing this section (e.g., 'Base Camp Builder!')."
        )
    badge_description = fields.Char(
        string="Badge Description", 
        help="The description of the badge earned for completing this section (e.g., 'Earned for completing the Introduction section of the Coffee Manual.')."
    )
    badge_icon = fields.Char(
        string="Badge Icon", 
        help="The icon of the badge earned for completing this section (e.g., 'fa-star')."
    )
    badge_color = fields.Char(
        string="Badge Color", 
        help="The color of the badge earned for completing this section (e.g., 'green')."
    )
    badge_criteria = fields.Char(
        string="Badge Criteria", 
        help="The criteria for earning the badge (e.g., 'Complete all levels of the Coffee Manual.')."
    )
    badge_model = fields.Char(
        string="Badge Model", 
        help="The model for which the badge is earned (e.g., 'coffee.manual.user')."
    )
    badge_domain = fields.Char(
        string="Badge Domain", 
        help="The domain for which the badge is earned (e.g., [('user_id', '=', user.id)])."
    )
    badge_message = fields.Char(
        string="Badge Message", 
        help="The message to display when the user earns the badge (e.g., 'Congratulations, you have earned the Base Camp Builder! badge!')."
    )
    badge_user_field = fields.Char(
        string="Badge User Field", 
        help="The user field to check for the badge (e.g., 'badge_name')."
    )
    badge_user_domain = fields.Char(
        string="Badge User Domain", 
        help="The domain for checking the user field (e.g., [('badge_name', '!=', False)])."
    )
    badge_user_message = fields.Char(
        string="Badge User Message", 
        help="The message to display when the user earns the badge (e.g., 'Congratulations, you have earned the Base Camp Builder! badge!')."
    )
    badge_user_badge_name = fields.Char(
        string="Badge User Badge Name", 
        help="The name of the badge earned for completing this section (e.g., 'Base Camp Builder!')."
    )
    badge_user_badge_description = fields.Char(
        string="Badge User Badge Description", 
        help="The description of the badge earned for completing this section (e.g., 'Earned for completing the Introduction section of the Coffee Manual.')."
    )
    badge_user_badge_icon = fields.Char(
        string="Badge User Badge Icon", 
        help="The icon of the badge earned for completing this section (e.g., 'fa-star')."
    )
    badge_user_badge_color = fields.Char(
        string="Badge User Badge Color", 
        help="The color of the badge earned for completing this section (e.g., 'green')."
    )
    badge_user_badge_criteria = fields.Char(
        string="Badge User Badge Criteria", 
        help="The criteria for earning the badge (e.g., 'Complete all levels of the Coffee Manual.')."
    )
    badge_user_badge_model = fields.Char(
        string="Badge User Badge Model", 
        help="The model for which the badge is earned (e.g., 'coffee.manual.user')."
    )
    badge_user_badge_domain = fields.Char(
        string="Badge User Badge Domain", 
        help="The domain for which the badge is earned (e.g., [('user_id', '=', user.id)])."
    )
    badge_user_badge_message = fields.Char(
        string="Badge User Badge Message", 
        help="The message to display when the user earns the badge (e.g., 'Congratulations, you have earned the Base Camp Builder! badge!')."
    )

    _sql_constraints = [
        ("coffee_manual_section_key_unique", "unique(key)", "Section key must be unique."),
    ]
