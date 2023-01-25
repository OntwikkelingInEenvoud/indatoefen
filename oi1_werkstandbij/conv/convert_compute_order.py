from odoo import models, api

import logging

_logger = logging.getLogger(__name__)


class AccountAccount(models.TransientModel):
    _name = 'convert_compute_order'
    _description = 'convert_compute_order_id_account_move'

    @api.model
    def do_cron_calculate_order_id(self):
        account_move_obj = self.env['account.move']
        for account_move in account_move_obj.search([('type','=', 'out_invoice'), ('x_sale_id', '=', False)], order='create_date desc'):
            account_move.invoice_line_ids._compute_x_sale_id()
            account_move._compute_x_sale_id()
            self.env.cr.commit()


