from odoo import models, fields, api
from datetime import datetime
import logging
import threading

_logger = logging.getLogger(__name__)


class DailyCounter(models.Model):
    _name = 'unique.code.generator'
    _description = 'Daily Counter for Unique Code Generation'

    date = fields.Char('Date', size=8, required=True, unique=True)
    counter = fields.Integer('Counter', default=1, required=True)
    model_name = fields.Char('Model Name', required=True)

    @api.model
    def _get_current_date(self):
        """ Get the current date in YYYYMMDD format """
        return datetime.now().strftime("%Y%m%d")

    @api.model
    def generate_unique_code(self, model_name):
        """ Generate a unique code using the current date, a counter, and model name """
        current_date = self._get_current_date()
        lock = threading.Lock()  # Using lock for thread-safety

        # Acquire lock to ensure thread safety
        with lock:
            # Try to find the record for the current date and model_name
            record = self.search([('date', '=', current_date), ('model_name', '=', model_name)], limit=1)

            if not record:
                # If record does not exist, create a new one
                record = self.create({'date': current_date, 'counter': 1, 'model_name': model_name})
            else:
                # Increment the counter
                if record.counter >= 9999:
                    # Handle overflow error
                    _logger.error(f"Counter for the model '{model_name}' has exceeded the limit!")
                    raise ValueError(f"The counter has exceeded the maximum limit for model '{model_name}'.")
                record.write({'counter': record.counter + 1})

            # Format the counter as a 4-digit number (padded with leading zeros)
            four_digit_counter = f"{record.counter:04}"

            # Combine the current date, model_name, and the 4-digit counter to form the unique code
            #unique_code = f"{model_name.upper()}-{current_date}-{four_digit_counter}"
            unique_code = f"/{current_date}/{four_digit_counter}"

            # Log the generated unique code
            _logger.info(f"Generated Unique Code for {model_name}: {unique_code}")

        # Return the generated unique code
        return unique_code

    '''@api.model
    def generate_unique_code(self, model_name):
        """ Generate a unique code using the current date, a counter, and model name """
        current_date = self._get_current_date()

        # 1. Lock the database row for the current date and model name
        # We use self.env.cr.execute() to perform a raw SQL SELECT FOR UPDATE
        self.env.cr.execute("""
            SELECT id, counter 
            FROM unique_code_generator 
            WHERE date = %s AND model_name = %s 
            FOR UPDATE
        """, (current_date, model_name))

        result = self.env.cr.fetchone()

        if result:
            record_id, counter = result
            new_counter = counter + 1

            if new_counter > 9999:
                # Handle overflow error
                _logger.error(f"Counter for the model '{model_name}' has exceeded the limit!")
                raise ValueError(f"The counter has exceeded the maximum limit for model '{model_name}'.")

            # 2. Update the counter value atomically
            self.env.cr.execute("""
                UPDATE unique_code_generator 
                SET counter = %s 
                WHERE id = %s
            """, (new_counter, record_id))

        else:
            # 3. If record does not exist, create a new one (counter starts at 1)
            new_counter = 1
            self.create({'date': current_date, 'counter': new_counter, 'model_name': model_name})

        # Format the counter and generate the unique code
        four_digit_counter = f"{new_counter:04}"
        unique_code = f"/{current_date}/{four_digit_counter}"

        # Log and return
        _logger.info(f"Generated Unique Code for {model_name}: {unique_code}")
        return unique_code'''
