import datetime
import html
import json
import re

from odoo.modules.module import get_module_resource

from odoo import http, models, fields, _
from odoo.http import request
from odoo.exceptions import ValidationError


class UniqueCoffeeController(http.Controller):

    @http.route('/register', type='http', auth='public', website=True,
                csrf=False)
    def contact_form(self, **kwargs):
        return request.render('unique_coffee.contact_form_template', {})

    @http.route('/create_contact', type='http', auth='public', website=True,
                csrf=False)
    def create_contact(self, **kwargs):
        name = kwargs.get('name')
        birthdate = kwargs.get('birthdate')
        cellphone = kwargs.get('cellphone')

        errors = []

        if not name:
            errors.append(_('Por favor, insira um nome.'))
        elif len(name) < 10 or len(name) > 50:
            errors.append(
                _("O nome deve ter no mínimo 10 e no máximo 50 caracteres."))

        if birthdate:
            try:

                date_obj = datetime.datetime.strptime(birthdate,
                                                      '%d/%m/%Y').date()

                if date_obj > datetime.date.today():
                    errors.append(
                        "A data de nascimento não pode ser uma data futura.")
            except Exception as e:
                errors.append(_(e))

        if not cellphone:
            errors.append(_('Por favor, digite um número de celular.'))
        else:
            registered_cellphone = request.env['unique.contacts'].search(
                []).mapped(lambda r: r.cellphone)
            if cellphone in registered_cellphone:
                errors.append(_(
                    'Este número de celular já está registrado.'))
        if errors:
            return request.render('unique_coffee.contact_form_template',
                                  {'errors': errors})

        try:
            ucObject = self._get_ucObject()
            if ucObject and ucObject.cellphone == cellphone:
                raise ValidationError(
                    _('Este número de celular já está registrado.'))

            new_contact = {
                "name": name,
                "cellphone": cellphone,
                "birthdate": birthdate
            }
            contact = request.env['unique.contacts'].sudo().create(new_contact)
        except ValidationError as e:
            errors.append(e.args[0])
            return request.render('unique_coffee.contact_form_template',
                                  {'errors': errors})

        except ValueError as ve:
            errors.append(_(ve))

        except Exception as e:
            errors.append(
                _(f'Ocorreu um erro ao criar o registro. Por favor, '
                  f'tente novamente. {e}'))
            return request.render('unique_coffee.contact_form_template',
                                  {'errors': errors})

        all_contacts = request.env['unique.contacts'].search([])

        # Redirecionar para uma página de sucesso
        return request.render('unique_coffee.contact_success_template',
                              {"contacts": all_contacts})

    def _get_ucObject(self):
        ucObject = request.env['unique.contacts'].sudo().search([], limit=1)
        return ucObject or False

    @http.route('/cardapio', type='http', auth='public', website=True,
                csrf=False)
    def menu_list(self, **kwargs):
        data = self.get_json_data()
        return request.render('unique_coffee.menu_cafe_unique', {
            'data': data,  # Passamos o resultado da função, não a função em si
        })

    def get_json_data(self):
        file_path = get_module_resource('unique_coffee', 'static', 'src', 'img',
                                        'menu.json')
        with open(file_path) as f:
            data = json.load(f)

        formatted_data = []
        for topic, items in data.items():
            topic_cards = []
            for item in items:
                topic_cards.append({
                    'nome': html.escape(item['nome']),
                    'descrição': html.escape(item['descrição']),
                    'preço': html.escape(item['preço']),
                })
            formatted_data.append({
                'topico': html.escape(topic),
                'cards': topic_cards,
            })

        return formatted_data

    @http.route('/add_to_cart', type='http', auth='public', website=True,
                methods=['POST'], csrf=False)
    def add_to_cart(self, **kwargs):
        item_name = kwargs.get('nome')
        item_description = kwargs.get('descrição')
        item_price = kwargs.get('preço')
        print(
            f"Item adicionado ao carrinho: {item_name}, {item_description}, "
            f"{item_price}")
        # Aqui você pode adicionar o item ao carrinho
        return "OK"
