from odoo import models, fields, api, _
import datetime
from odoo.exceptions import ValidationError


class InsurancePolis(models.Model):
    _name = 'oi1_insurance_polis'
    _description = "Insurance polis"

    name = fields.Char(string='Name', compute="_compute_name", store=True)
    number = fields.Char(string='Polis number', required=True)
    free_worker_id = fields.Many2one('oi1_free_worker', string="Free worker")
    date_from = fields.Date(string="From date")
    date_to = fields.Date(string="To date")
    partner_id = fields.Many2one('res.partner', string="Insurance company", help="The company", required=True)
    insurance_id = fields.Many2one('oi1_insurance', string="Type", help="The insurance",
                                        required=True)
    active = fields.Boolean(string="Active", default=True)

    @api.constrains('date_from', 'date_to')
    def _check_date_from_date_to(self):
        for polis in self:
            if not polis.date_from or not polis.date_to:
                continue
            if polis.date_to < polis.date_from:
                raise ValidationError(_('Start date  %s should not be greater then end date %s.')
                                      % (polis.date_from, polis.date_to))

    @api.onchange('insurance_id')
    def _onchange_insurance_id(self):
        for polis in self:
            insurance_id = polis.insurance_id
            if insurance_id.id:
                polis.partner_id = insurance_id.partner_id
                polis.onchange_date_from()

    @api.onchange('date_from')
    def onchange_date_from(self):
        for polis in self:
            insurance_id = polis.insurance_id
            if not polis.date_from:
                polis.date_from = datetime.datetime.now()
            if not polis.date_to and insurance_id.duration > 0:
                polis.date_to = polis.date_from + datetime.timedelta(days=insurance_id.duration)

    @api.depends('insurance_id', 'number', 'date_from', 'date_to', 'partner_id')
    def _compute_name(self):
        for polis in self:
            name = (polis.insurance_id.name or "") + " " + \
                   (polis.insurance_id.insurance_type_id.name or "") + " :" + \
                   (polis.partner_id.name or "") + " " + \
                   (polis.number or "")

            if polis.date_from:
                name = name + " " + polis.date_from.strftime("%Y%m%d")
            if polis.date_to:
                name = name + " - " + polis.date_to.strftime("%Y%m%d")
            polis.name = name.strip()

    def _check_commissions_on_free_worker(self):
        commission_free_worker_obj = self.env['oi1_commission_free_worker'];
        for insurance_polis in self:
            free_worker_id = insurance_polis.free_worker_id
            commission_id = insurance_polis.insurance_id.commission_id
            if free_worker_id.id and commission_id.id:
                commissions = commission_free_worker_obj.search([('free_worker_id','=', free_worker_id.id),
                                                                             ('commission_id', '=', commission_id.id)])
                if len(commissions) == 0:
                    commission_free_worker_obj.create({'free_worker_id': free_worker_id.id,
                                                       'commission_id': commission_id.id
                                                       })
                    message = _("Automatic commission %s added" % commission_id.name)
                    free_worker_id.message_post(body=message)

    @api.model_create_multi
    def create(self, vals_list):
        insurance_polis_list = super().create(vals_list)
        for insurance_polis in insurance_polis_list:
            insurance_polis._check_commissions_on_free_worker()
        return insurance_polis_list

    def write(self, values):
        res = super().write(values)
        self._check_commissions_on_free_worker()
        return res





