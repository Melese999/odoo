
from odoo import http
from odoo.http import request
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class CoffeeManualController(http.Controller):
    @http.route("/coffee/manual", type="http", auth="user", website=True)
    def manual(self, **kwargs):
        sections = request.env["coffee.manual.section"].sudo().search([], order="sequence, id")
        progress = {
            s.key: request.env["coffee.manual.progress"].sudo().search([
                ("user_id", "=", request.env.user.id), ("section_id", "=", s.id)
            ], limit=1)
            for s in sections
        }
        values = {
            "sections": sections,
            "progress": progress,
        }
        return request.render("coffee_manual.manual_page", values)

    @http.route("/coffee/manual/progress", type="json", auth="user")
    def mark_progress(self, section_key, status):
        ok = request.env["coffee.manual.progress"].sudo().set_status(section_key, status)
        return {"ok": ok}

    @http.route("/coffee/manual/quiz/submit", type="json", auth="user")
    def submit_quiz(self, quiz_id: int, answers: dict):
        quiz = request.env["coffee.manual.quiz"].sudo().browse(int(quiz_id))
        if not quiz.exists():
            return {"ok": False, "message": "Quiz not found"}
        total = len(quiz.question_ids)
        correct = 0
        Answer = request.env["coffee.manual.quiz.answer"].sudo()
        # remove previous answers from this user for this quiz
        prev = Answer.search([("user_id", "=", request.env.user.id), ("quiz_id", "=", quiz.id)])
        if prev:
            prev.unlink()
        for q in quiz.question_ids:
            sel = answers.get(str(q.id))
            if sel not in {"a", "b", "c", "d"}:
                continue
            ans = Answer.create({
                "user_id": request.env.user.id,
                "quiz_id": quiz.id,
                "question_id": q.id,
                "selected": sel,
            })
            if ans.is_correct:
                correct += 1
        score = int((correct / total) * 100) if total else 0
        return {"ok": True, "score": score, "correct": correct, "total": total}

    @http.route("/coffee/manual/search", type="json", auth="user")
    def search(self, q: str):
        # basic keyword search over static content snippets
        if not q:
            return {"results": []}
        corpus = request.env["ir.ui.view"].sudo().read_template("coffee_manual.manual_content_index")
        results = []
        for line in corpus.splitlines():
            if q.lower() in line.lower():
                results.append(line.strip())
                if len(results) >= 10:
                    break
        return {"results": results}
