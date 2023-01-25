from odoo import models, fields


class FreeWorkerLabel(models.Model):
    _name = "oi1_free_worker_label"
    _description = "Free worker label"

    name = fields.Char('name')
