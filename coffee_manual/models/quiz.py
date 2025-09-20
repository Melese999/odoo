from odoo import api, fields, models
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class CoffeeManualQuiz(models.Model):
    _name = "coffee.manual.quiz"
    _description = "Coffee Manual Quiz"
    _order = "sequence, id"

    name = fields.Char(required=True)
    section_id = fields.Many2one("coffee.manual.section", required=True, ondelete="cascade")
    sequence = fields.Integer(default=10)
    question_ids = fields.One2many("coffee.manual.quiz.question", "quiz_id")


class CoffeeManualQuizQuestion(models.Model):
    _name = "coffee.manual.quiz.question"
    _description = "Coffee Manual Quiz Question"
    _order = "sequence, id"

    quiz_id = fields.Many2one("coffee.manual.quiz", required=True, ondelete="cascade")
    name = fields.Char(required=True, help="The question text")
    sequence = fields.Integer(default=10)
    option_a = fields.Char(required=True)
    option_b = fields.Char(required=True)
    option_c = fields.Char(required=True)
    option_d = fields.Char(required=True)
    correct = fields.Selection([
        ("a", "A"), ("b", "B"), ("c", "C"), ("d", "D"),
    ], required=True)


class CoffeeManualQuizAnswer(models.Model):
    _name = "coffee.manual.quiz.answer"
    _description = "Coffee Manual Quiz Answer"
    _order = "create_date desc"

    user_id = fields.Many2one("res.users", required=True, ondelete="cascade")
    quiz_id = fields.Many2one("coffee.manual.quiz", required=True, ondelete="cascade")
    question_id = fields.Many2one("coffee.manual.quiz.question", required=True, ondelete="cascade")
    selected = fields.Selection([
        ("a", "A"), ("b", "B"), ("c", "C"), ("d", "D"),
    ], required=True)
    is_correct = fields.Boolean(compute="_compute_is_correct", store=True)

    @api.depends("selected", "question_id.correct")
    def _compute_is_correct(self):
        for rec in self:
            rec.is_correct = bool(rec.selected and rec.question_id and rec.selected == rec.question_id.correct)
