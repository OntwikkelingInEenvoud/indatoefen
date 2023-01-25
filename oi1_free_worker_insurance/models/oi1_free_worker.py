import datetime

from odoo import models, fields, api


class FreeWorker(models.Model):
    _inherit = 'oi1_free_worker'

    def _default_package(self):
        package_obj = self.env['oi1_insurance_package']
        package_ids = package_obj.search([('default_free_worker', '=', True)])
        if len(package_ids) > 0:
            return package_ids[0]
        return False

    no_schengen_polis_needed = fields.Boolean(string="No Schengen insurance needed", default=False, tracking=True)
    oi1_insurance_polis_ids = fields.One2many('oi1_insurance_polis', 'free_worker_id', string="Polis")
    schengen_insurance_polis_id = fields.Many2one('oi1_insurance_polis', compute="_compute_insurance_polis")
    schengen_insurance_polis_id_number = fields.Char(compute="_compute_insurance_polis_number", string="Polis number")
    schengen_insurance_polis_id_date_to = fields.Date(compute="_compute_insurance_polis_date_to", string="Date to")
    schengen_insurance_needs_attention = fields.Boolean(string="Needs schengen attention",
                                                        compute="compute_needs_attention", store=True,
                                                        tracking=True)
    insurance_package_id = fields.Many2one('oi1_insurance_package', string="Insurance Package",
                                           default=_default_package, tracking=True)

    @api.depends('state', 'nationality_id', 'oi1_insurance_polis_ids')
    def compute_needs_attention(self):
        for free_worker in self:
            if free_worker.no_schengen_polis_needed:
                free_worker.schengen_insurance_needs_attention = False
                continue
            if free_worker.state in ('concept', 'old'):
                free_worker.schengen_insurance_needs_attention = False
                continue
            if not free_worker.nationality_id.schengen_insurance:
                free_worker.schengen_insurance_needs_attention = False
                continue
            insurance_polis_id = free_worker.schengen_insurance_polis_id
            if insurance_polis_id.id and (not insurance_polis_id.date_to \
                    or (insurance_polis_id.date_to and insurance_polis_id.date_to > datetime.date.today() + datetime.timedelta(days=5))):
                free_worker.schengen_insurance_needs_attention = False
                continue
            free_worker.schengen_insurance_needs_attention = True

    def get_current_insurance_polis(self, free_worker):
        schengen_polis_type = self.env.ref('oi1_free_worker_insurance.oi1_insurance_schengen_type')
        current_date = datetime.date.today()
        list_insurance_polis = free_worker.oi1_insurance_polis_ids. \
            filtered(lambda l: l.insurance_id.insurance_type_id.id == schengen_polis_type.id and
                               (not l.date_from or l.date_from <= current_date) and
                               (not l.date_to or l.date_to >= current_date)
                     )
        if len(list_insurance_polis) > 0:
            return list_insurance_polis[0]
        return False

    @api.depends('oi1_insurance_polis_ids')
    def _compute_insurance_polis_number(self):
        for free_worker in self:
            schengen_insurance_polis = self.get_current_insurance_polis(free_worker)
            if schengen_insurance_polis:
                free_worker.schengen_insurance_polis_id_number = schengen_insurance_polis.number

    @api.depends('oi1_insurance_polis_ids')
    def _compute_insurance_polis_date_to(self):
        for free_worker in self:
            schengen_insurance_polis = self.get_current_insurance_polis(free_worker)
            if schengen_insurance_polis:
                free_worker.schengen_insurance_polis_id_date_to = schengen_insurance_polis.date_to

    @api.depends('oi1_insurance_polis_ids')
    def _compute_insurance_polis(self):
        for free_worker in self:
            free_worker.schengen_insurance_polis_id = self.get_current_insurance_polis(free_worker)

    @api.model
    def do_calculate_status_free_workers_cron(self):
        super().do_calculate_status_free_workers_cron()
        free_worker_obj = self.env['oi1_free_worker']
        for free_worker in free_worker_obj.search([('state', 'not in', ('concept', 'old'))]):
            free_worker.compute_needs_attention()







