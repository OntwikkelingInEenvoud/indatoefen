from odoo import models, api, fields, exceptions, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    x_freeworker_ids = fields.One2many('oi1_free_worker', 'partner_id', string="Free workers")
    x_freeworker_id = fields.Many2one('oi1_free_worker', compute="_compute_x_freeworker_id", store=True,
                                      string="Free worker")
    x_is_freeworker_visible = fields.Boolean(string="x_is_freeworker_visible",
                                             compute="_compute_x_is_freeworker_visible", compute_sudo=True)
    x_is_freeworker = fields.Boolean("Is freeworker", compute="_compute_x_is_freeworker_visible", store=True,
                                     compute_sudo=True)
    x_communication_email = fields.Char(compute="_compute_communication_email", string="Communication email")



    @api.depends('x_freeworker_id', 'email', 'x_freeworker_id.communication_email')
    def _compute_communication_email(self):
        for res_partner in self:
            if not res_partner.x_is_freeworker:
                res_partner.x_communication_email = res_partner.email
            else:
                res_partner.x_communication_email = res_partner.x_freeworker_id.communication_email

    @api.constrains('email')
    def _check_if_a_free_worker_has_an_unique_email(self):
        res_partner_obj = self.env['res.partner']
        for res_partner in self:
            if not res_partner.x_is_freeworker:
                continue
            if not res_partner.email or res_partner.email.strip() == '':
                continue
            free_workers = res_partner_obj.search([('email', '=', res_partner.email),
                                                   ('id', '!=', res_partner.id),
                                                   ('x_is_freeworker', '=', True),
                                                   ])
            if len(free_workers) > 0:
                old_free_worker = free_workers[0]
                raise exceptions.ValidationError(
                    _("An free worker should have an unique email address. Free worker %s has "
                      "already the same email. You could select a communication partner "
                      "for this freeworker") % old_free_worker.display_name)

    @api.constrains('commercial_partner_id')
    def check_commercial_partner_id_bank_id(self):
        res_partner_bank_obj = self.env['res.partner.bank']
        for partner in self:
            if not partner.commercial_partner_id.id or not partner.x_is_freeworker_visible:
                continue
            partner_banks_qty = res_partner_bank_obj.search_count(
                [('partner_id', '=', partner.commercial_partner_id.id)])
            if partner.commercial_partner_id.id != partner.id and partner_banks_qty == 0:
                raise exceptions.ValidationError(_(
                    'The commercial partner %s of partner %s has no banking account this is not allowed for a commercial partner')
                                                 % (partner.commercial_partner_id.name, partner.name))

    @api.depends('x_freeworker_id')
    def _compute_x_is_freeworker_visible(self):
        for rp in self:
            if rp.x_freeworker_id.id:
                rp.x_is_freeworker_visible = True
                rp.x_is_freeworker = True
            else:
                rp.x_is_freeworker_visible = False
                rp.x_is_freeworker = False

    @api.depends('x_freeworker_ids')
    def _compute_x_freeworker_id(self):
        for rp in self:
            free_workers = self.env['oi1_free_worker'].search([('partner_id', '=', rp.id)], limit=1)
            if len(free_workers) > 0:
                rp.x_freeworker_id = free_workers[0]
            else:
                rp.x_freeworker_id = False

    def unlink(self):
        for partner in self:
            if partner.x_freeworker_id.id:
                raise exceptions.UserError(
                    _("The contact  %s is related to a freeworker and shouldn't be deleted. Please delete the freeworker") % partner.name)
        super().unlink()

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        """
        if not self.env.user.has_group('oi1_free_worker.freeworker_view_group'):
        """
        args += [('x_is_freeworker', '=', False)]
        return super().search(args, offset, limit, order, count)
