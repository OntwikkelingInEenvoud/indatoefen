from odoo import models, fields


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    x_from_company_id = fields.Many2one('res.company',
                                        string="From company id",
                                        help="The company from which the invoice is purchased")
    x_sale_journal_id = fields.Many2one('account.journal',
                                        string="Linked Sales Journal",
                                        help="The journal to which the payments to wsb are booked",
                                        domain="[('type','=', 'sale')]")
    x_pur_journal_id = fields.Many2one('account.journal',
                                        string="Linked Purchase Journal",
                                        help="The journal to which the payments to wsb are booked",
                                        domain="[('type','=', 'purchase')]")
