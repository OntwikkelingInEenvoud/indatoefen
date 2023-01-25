from odoo import models, api, exceptions, Command, fields, _


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'


    @api.model
    def create_account_invoice_move_line(self, values):
        if isinstance(values, dict):
            values['display_type'] = 'product'
        else:
            for value in values:
                value['display_type'] = 'product'

        account_move_lines = self.env['account.move.line'].create(values)
        return account_move_lines

    @api.model
    def get_purchase_invoice_line_data(self, product_id, move_id):
        account_id = product_id.property_account_expense_id or product_id.categ_id.property_account_expense_categ_id
        if not account_id:
            account_id = move_id.journal_id.default_account_id
        if not account_id.id:
            raise exceptions.UserError(
                _("Please provide an income account for product %s") % product_id.product_tmpl_id.name)
        taxes = self.get_taxes_purchase_product_id(product_id, move_id)
        return account_id, taxes

    @api.model
    def get_sales_invoice_line_data(self, product_id, move_id):
        account_id = product_id.property_account_income_id or product_id.categ_id.property_account_income_categ_id
        if not account_id:
            account_id = move_id.journal_id.default_account_id
        if not account_id.id:
            raise exceptions.UserError(
                _("Please provide an income account for product %s") % product_id.product_tmpl_id.name)
        taxes = self.add_sales_taxes(product_id, move_id)
        return account_id, taxes

    @api.model
    def create_account_invoice_move_line_from_product(self, move_id, product_id, quantity=False, price_unit=False,
                                                      name=False):
        account_id = False
        taxes = False
        if not name:
            name = product_id.name
        if not price_unit:
            price_unit = product_id.list_price
        if not quantity:
            quantity = 1
        if move_id.move_type in ('out_invoice', 'out_refund'):
            account_id, taxes = self.get_sales_invoice_line_data(product_id, move_id)
        if move_id.move_type in ('in_invoice', 'in_refund'):
            account_id, taxes = self.get_purchase_invoice_line_data(product_id, move_id)
        values = {'quantity': quantity,
                  'price_unit': price_unit,
                  'name': name,
                  'product_id': product_id.id,
                  'account_id': account_id.id,
                  'tax_ids': [(6, 0, taxes)],
                  'display_type': 'product'
                  }
        move_id.write({'line_ids': [Command.create(values)]})
        return move_id.line_ids.filtered(lambda l: l.display_type == 'product').sorted(key=lambda r: -r.id)[0]


    @api.model
    def add_sales_taxes(self, product_id, move_id):
        taxes = product_id.taxes_id.filtered(lambda l: l.company_id.id == self.env.company.id)
        fiscal_position_id = move_id.partner_id.property_account_position_id
        if fiscal_position_id and taxes:
            tax_ids = fiscal_position_id.map_tax(taxes, product_id, move_id.partner_id).ids
        else:
            tax_ids = taxes.ids
        return tax_ids

    def update_account_invoice_move_line(self, values, context=False, check_invoice=True):
        context = self._check_context(context)
        #context['check_move_validity'] = False
        account_move_lines = self.write(values)
        #2023_0103 Check if this code is not needed anymore in Odoo v16
        #self.with_context(context)._onchange_price_subtotal()
        #if check_invoice:
        #    invoices = self.mapped('move_id')
        #    invoices.with_context(context).update_invoice_after_account_move_line_change()
        return account_move_lines

    def get_taxes_product_id(self, product_id, partner_id, fiscal_position_id=False, company_id=False):
        if not company_id:
            company_id = self.env.company
        taxes = product_id.taxes_id.filtered(
            lambda r: r.company_id.id == company_id.id)
        if fiscal_position_id and taxes:
            tax_ids = fiscal_position_id.map_tax(taxes, product_id, partner_id).ids
        else:
            tax_ids = taxes.ids
        return tax_ids

    def get_taxes_purchase_product_id(self, product_id, partner_id, fiscal_position_id=False, company_id=False):
        if not company_id:
            company_id = self.env.company
        taxes = product_id.supplier_taxes_id.filtered(
            lambda r: r.company_id.id == company_id.id)
        if fiscal_position_id and taxes:
            tax_ids = fiscal_position_id.map_tax(taxes, product_id, partner_id).ids
        else:
            tax_ids = taxes.ids
        return tax_ids

    def get_taxes_product_id_from_type_tax_use(self, type_tax_use, product_id, partner_id, fiscal_position_id=False,
                                               company_id=False):
        if type_tax_use == 'purchase':
            return self.get_taxes_purchase_product_id(product_id, partner_id, fiscal_position_id, company_id)
        return self.get_taxes_product_id(product_id, partner_id, fiscal_position_id, company_id)

    def _check_context(self, context):
        if not context:
            context = {}
        return context
