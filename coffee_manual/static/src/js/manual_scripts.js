/** @odoo-module **/

import { jsonrpc } from "@web/core/network/rpc_service";
import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.CoffeeManualWidget = publicWidget.Widget.extend({
    selector: '.o_container', // Attach to the main container of your page
    events: {
        'click .js-mark-done': '_onMarkDoneClick',
        'click .js-submit-quiz': '_onSubmitQuizClick',
    },

    /**
     * @override
     */
    start: function () {
        console.log("Coffee Manual JS has been loaded and is running!");
        return this._super.apply(this, arguments);
    },

    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    /**
     * Serializes the answers from a quiz form.
     * @private
     * @param {jQuery} $quizRoot The root element of the quiz section.
     * @returns {Object} A dictionary of question IDs and selected answers.
     */
    _serializeQuiz: function ($quizRoot) {
        const answers = {};
        $quizRoot.find('.cm-question').each(function() {
            const $question = $(this);
            const qid = $question.find('input[type=radio]').attr('name').replace('q_', '');
            const val = $question.find('input[type=radio]:checked').val();
            if (val) {
                answers[qid] = val;
            }
        });
        return answers;
    },

    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------

    /**
     * Handles the click event for the "Mark as done" button.
     * @private
     * @param {Event} ev
     */
    _onMarkDoneClick: function (ev) {
        const $button = $(ev.currentTarget);
        const sectionKey = $button.data('section');

        jsonrpc('/coffee/manual/progress', {
            section_key: sectionKey,
            status: 'done',
        }).then(() => {
            $button.removeClass('btn-primary').addClass('btn-success').prop('disabled', true);
            $button.html('<i class="fa fa-check-circle mr-1"/> Completed');
            // --- START OF NEW CODE ---
            // Find the badge associated with this section and reveal it.
            // We traverse up to the parent section, then find the badge within it.
            const $section = $button.closest('.cm-section');
            const $badge = $section.find('.js-badge-award');
            if ($badge.length) {
                $badge.removeClass('d-none');
            }
            // --- END OF NEW CODE ---
        });
    },

    /**
     * Handles the click event for the "Submit quiz" button.
     * @private
     * @param {Event} ev
     */
    _onSubmitQuizClick: function (ev) {
        const $quiz = $(ev.currentTarget).closest('.cm-quiz');
        const quizId = $quiz.data('quiz-id');
        const answers = this._serializeQuiz($quiz);

        jsonrpc('/coffee/manual/quiz/submit', {
            quiz_id: quizId,
            answers: answers,
        }).then((res) => {
            if (res && res.ok) {
                const $result = $quiz.find('.cm-quiz-result');
                $result.text(`Score: ${res.score}% (${res.correct}/${res.total})`).removeClass('d-none');
            }
        });
    },
});

export default publicWidget.registry.CoffeeManualWidget;