from odoo import models, fields, api, _
import datetime
import logging

_logger = logging.getLogger(__name__)


class FactoringExport(models.Model):
    _name = 'oi1_werkstandbij.factoring_export'

    name = fields.Char("name", required=True)
    date = fields.Date("export date", default=datetime.date.today())
    file = fields.Binary("export file")

    account_move_ids = fields.One2many('account.move', 'x_factoring_export_id', string="Related invoices")
