

from odoo import api, fields, models, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    short_code_sequence_id = fields.Many2one('ir.sequence', help='Sequence to use in short code')

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env.company.short_code_sequence_id = self.short_code_sequence_id

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res['short_code_sequence_id'] = self.env.company.short_code_sequence_id.id
        return res
    
    @api.onchange('chart_template_id')
    def on_change_chart_template_id(self):
        self.short_code_sequence_id = self.chart_template_id.short_code_sequence_id