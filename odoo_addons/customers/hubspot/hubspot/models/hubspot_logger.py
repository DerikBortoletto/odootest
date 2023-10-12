from odoo import fields, models, _


class hubspotLogger(models.Model):
    _name = "hubspot.logger"
    _order = "id desc"
    _description = "Hubspot Loggers"

    hubspot_datetime = fields.Datetime('Hubspot DateTime', default=fields.Datetime.now)
    hubspot_user_id = fields.Char("User id", default=lambda self: self.env.user.id)
    hubspot_operation = fields.Char("Operation")
    hubspot_description = fields.Text("Description")
    debug_logs = fields.Boolean("Odoo Debug Logs", default=False)
    name = fields.Char("Name")

    def create_log_message(self, hubspot_operation, hubspot_description, is_debug=False):
        try:
            if is_debug:
                self.env['hubspot.logger'].create({
                    'hubspot_operation': hubspot_operation,
                    'hubspot_description': hubspot_description,
                    'debug_logs': True
                })
                self._cr.commit()
            else:
                self.env['hubspot.logger'].create({
                    'hubspot_operation': hubspot_operation,
                    'hubspot_description': hubspot_description,
                })
                self._cr.commit()
        except Exception as e:
            print(e)
        return True
