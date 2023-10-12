import re
from datetime import datetime, date

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class UniqueContacts(models.Model):
    _name = "unique.contacts"
    _description = "Unique Contacts"
    _rec_name = "name"
    # _sql_constraints = [("unique_cellphone", "unique(cellphone)",
    #                      "Este número de celular já está cadastrado")]

    name = fields.Char(string="Name", required=True)
    birthdate = fields.Date(string="Birthdate")
    cellphone = fields.Char(string="Cellphone", required=True)
    cellphone_normalized = fields.Char(
        string='Normalized Cellphone',
        compute='_compute_cellphone_normalized',
        store=True
    )

    @api.constrains('name')
    def validate_name(self):
        for record in self:
            if len(record.name) < 10 or len(record.name) > 50:
                raise ValidationError(
                    "O nome deve ter no mínimo 10 e no máximo 50 caracteres.")

    @api.onchange('birthdate')
    def _onchange_birthdate(self):
        if self.birthdate:
            pass
            # print(self.birthdate)

    @api.constrains('birthdate')
    def _check_birthdate_format(self):
        for record in self:
            if record.birthdate:
                birthdate_str = record.birthdate.strftime('%d/%m/%Y')
                try:
                    datetime.strptime(birthdate_str, '%d/%m/%Y')
                except ValueError:
                    raise ValidationError(
                        'Formato de data de nascimento inválido. Use '
                        'DD/MM/AAAA.'
                    )
            if record.birthdate and record.birthdate > date.today():
                raise ValidationError(
                    'A data de nascimento não pode estar no futuro.'
                )

    @api.depends('cellphone')
    def _compute_cellphone_normalized(self):
        for record in self:
            record.cellphone = re.sub(r'\s', '',
                                      record.cellphone)  # Remove all
            # whitespace characters
            normalized_cellphone = re.sub(r'[\D()]+', '',
                                          record.cellphone)  # Remove all
            # non-numeric and non-parentheses characters
            if len(normalized_cellphone) == 11:  # Format as (DDD) XXXXX-XXXX
                # if it has 11 digits
                record.cellphone_normalized = '({}) {}-{}'.format(
                    normalized_cellphone[:2], normalized_cellphone[2:7],
                    normalized_cellphone[7:])
            else:
                record.cellphone_normalized = normalized_cellphone

    @api.constrains('cellphone_normalized')
    def _check_unique_cellphone_normalized(self):
        for record in self:
            if record.cellphone_normalized and self.search_count(
                    [('id', '!=', record.id), (
                            'cellphone_normalized', '=',
                            record.cellphone_normalized)]):
                raise ValidationError(
                    'Este número de celular já está registrado.')

