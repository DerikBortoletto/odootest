from odoo import fields, models, api



class AccountMove(models.Model):
    _inherit = "account.move"

    def write(self, vals):
      if self.type_name != 'Lançamento de Diário':
        # checking if the account.move has id to procceeds the concatenation process
        if self.id:
          if vals.get('line_ids'):
            # validate if the first invoice_line_ids has name
            index_dict = 0
            for prod in self.invoice_line_ids:
              if self.invoice_line_ids[index_dict].name:
                # get the lot_ids inside the move_line_ids inside the invoice line
                product_lot_ids = self.invoice_line_ids[index_dict].move_line_ids.lot_ids

                # As the write function is used every time that we change the state of the invoice / account.move
                # We had to validate the function to trigger ONLY when the model name is account.move
                if self._name == 'account.move':
                  # Destructuring the object that contains the product batch, 
                  # to be able to handle only the batch id, batch values, serial number, expiration date and manufacturing date
                  lot_ids = product_lot_ids.id
                  lot_name = product_lot_ids.name
                  lot_serial = product_lot_ids.serial
                  lot_expiration_date = product_lot_ids.expiration_date
                  lot_manufacture_date = product_lot_ids.manufacture_date

                  # if the record has a batch's name, the flow proceeds
                  if lot_name:
                      # First the name will be saved into an appropriate variable
                      nome = self.invoice_line_ids[index_dict].name
                      # indice_01 will be used to find if the batch has already been filled previously
                      indice_01 = nome.find(lot_name)
                      # if the product has already received the concatenation, 
                      # the flow is interrupted so as not to be overwritten,
                      # as result of the search, the find() will return -1 if the concatenation does not have been run yet, and the flow will proceeds
                      if indice_01 == -1:
                        # due to the amount of data, the concatenation was divided into parts:
                        # 1 - concatenation of product name + batch number (lot_name)
                        if lot_name:
                          rotulo_1 = self.invoice_line_ids[index_dict].name + " | LT: " + lot_name
                        # [WIP] 2 - concatenation of product name + batch number + serial number
                        # if lot_serial:
                        #   rotulo_1 += " | SN: " + lot_serial
                        # 3 - concatenation of product name + batch number + serial number + batch expiration date
                        if lot_expiration_date:
                          rotulo_1 += " | V: " + str(lot_expiration_date.day) + "/" + str(lot_expiration_date.month) + "/" + str(lot_expiration_date.year)
                        # 4 - concatenation of product name + batch number + serial number + batch expiration date + batch manufacture date
                        if lot_manufacture_date:
                          rotulo_1 += " | F: " + str(lot_manufacture_date.day) + "/" + str(lot_manufacture_date.month) + "/" + str(lot_manufacture_date.year)
                        # Finally the result will replace the invoice line name
                        self.invoice_line_ids[index_dict].name = rotulo_1
              index_dict += 1
      # global method to write the changes into account.move record, write the vals values, and self changes
      res = super(AccountMove, self).write(vals)
      return res