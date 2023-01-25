from odoo import models, fields, api


class InsurancePayment(models.Model):
    _name = 'oi1_insurance_premium_payment'
    _description = "Insurance premium payment"

    sale_id  = fields.Many2one('sale.order')
    partner_id = fields.Many2one('res.partner')
    amount = fields.Monetary(string="Fixed rate", currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id.id,
                                  string="Currency", store=True)
    insurance_id = fields.Many2one('oi1_insurance', string="Insurance", required=True)
    package_id  = fields.Many2one('oi1_insurance_package', string="Package")
    account_analytic_line_id = fields.Many2one('account.analytic.line', required=True)
    free_worker_id = fields.Many2one('oi1_free_worker', required=True)
    payed_by_customer = fields.Boolean(string='Paid by customer', default=False)
    date = fields.Date(string="Date", required=True)

    @api.model
    def calculate_premium_payments_customer(self, hour_line):
        package_id = hour_line.x_sale_id.x_insurance_package_id
        for insurance_id in package_id.insurance_ids:
            self.insert_insurence_premium_payment(hour_line, insurance_id, package_id, True)

    @api.model
    def insert_insurence_premium_payment(self, hour_line, insurance_id, package_id, payed_by_customer=False):
        if hour_line.x_sale_id.id:
            partner_id = hour_line.x_sale_id.partner_id
            sale_id = hour_line.x_sale_id
            amount = insurance_id.calculate_amount(hour_line)
        free_worker_id = hour_line.x_free_worker_id

        return self.create({'sale_id': sale_id.id,
                            'partner_id': partner_id.id,
                            'amount': amount,
                            'insurance_id': insurance_id.id,
                            'package_id': package_id.id,
                            'account_analytic_line_id': hour_line.id,
                            'free_worker_id': free_worker_id.id,
                            'payed_by_customer': payed_by_customer,
                            'date': hour_line.date
                            })



