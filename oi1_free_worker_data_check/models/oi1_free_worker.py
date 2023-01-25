from odoo import models, fields, _
import datetime


class FreeWorker(models.Model):
    _inherit = 'oi1_free_worker'

    def do_action_check_data(self):
        return {
            'name': _('Check freeworker data wizard'),
            'res_model': 'oi1_free_worker_data_wizard',
            'view_mode': 'form',
            'context': "{'default_free_worker_id':" + str(self.id) + "}",
            'target': 'new',
            'type': 'ir.actions.act_window',
        }


