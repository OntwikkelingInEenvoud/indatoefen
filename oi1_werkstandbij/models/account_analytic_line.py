from odoo import models, fields, api, exceptions
from odoo import _


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    x_partner_id = fields.Many2one('res.partner', string='Free worker', domain=[('x_is_freeworker', '=', True)])
    x_free_worker_id = fields.Many2one('oi1_free_worker', string='Freeworker',
                                       domain=[('state', 'in', ('checked', 'active'))], ondelete='restrict',
                                       index=True)
    x_customer_id = fields.Many2one('res.partner', compute="_compute_x_customer_id", store=True)
    x_sale_id = fields.Many2one('sale.order', string='Order', related="project_id.sale_order_id", store=True)
    x_from_time = fields.Char(string='Start Time', size=5, default="00:00")
    x_to_time = fields.Char(string='End Time', size=5, default="00:00")
    x_pause_time = fields.Char(string='Pause Time', size=5, required=True, default="")
    x_state = fields.Selection([
        ('concept', 'Ingevoerd'),
        ('approved', 'Goedgekeurd'),
        ('customer_invoiced', "Klant gefactureerd"),
        ('invoiced', 'Gefactureerd'),
    ], default='concept', string="Status")
    x_rate = fields.Monetary(string="Price Unit")
    x_customer_name = fields.Char(related='x_sale_id.partner_id.name', readonly=True, string="Customer")
    x_amount = fields.Monetary(string='Free worker Amount', compute="_compute_amount", store=True)
    x_sale_invoice_line_id = fields.Many2one('account.move.line', string="Sales Invoice", ondelete="set null")
    x_pur_invoice_line_id = fields.Many2one('account.move.line', string="Purchase Invoice", ondelete="set null")
    x_commission_created = fields.Boolean(string="Commissions created", compute="_compute_x_commission_created",
                                          store=True)
    x_sale_invoice_id = fields.Many2one(comodel_name='account.move', compute="_compute_x_sale_invoice_id", store=True)
    x_pur_invoice_id = fields.Many2one(related='x_pur_invoice_line_id.move_id', string="Pur invoice")
    x_commission_payment_line_ids = fields.One2many('oi1_sale_commission_payment_line', 'account_analytic_line_id',
                                                    string="Related Commissions")
    x_sales_amount = fields.Monetary(string="Sales Amount", compute="_compute_x_sales_amount")
    x_com_amount = fields.Monetary(string="Com. Amount", compute="_compute_x_com_amount")
    x_pur_amount = fields.Monetary(string="Pur. Amount", compute="_compute_x_pur_amount")
    x_margin = fields.Monetary(string="Margin", compute="_compute_x_margin")
    x_poule_id = fields.Many2one('oi1_freeworkerpoule', compute="_compute_x_poule_id", store=True)
    active = fields.Boolean(string="Active", default=True)

    @api.depends('x_pur_invoice_line_id')
    def _compute_x_pur_invoice_id(self):
        aal_with_pur_invoice_line_id = self.filtered(lambda l: l. x_pur_invoice_line_id.id)
        aal_with_pur_invoice_line_id.x_pur_invoice_id = aal_with_pur_invoice_line_id.x_pur_invoice_line_id.move_id.id
        aal_without_pur_invoice_line_id = self.filtered(lambda l: not l.x_pur_invoice_line_id.id)
        aal_without_pur_invoice_line_id.x_pur_invoice_id = False

    @api.depends('x_sale_invoice_line_id')
    def _compute_x_sale_invoice_id(self):
        for aal in self:
            sale_invoice_id = False
            if aal.x_sale_invoice_line_id.id:
                sale_invoice_id = aal.x_sale_invoice_line_id.move_id
            aal.x_sale_invoice_id = sale_invoice_id

    @api.depends('project_id')
    def _compute_x_poule_id(self):
        free_worker_poule_obj = self.env['oi1_freeworkerpoule']
        for aal in self:
            aal.x_poule_id = free_worker_poule_obj.get_free_worker_poule(aal.project_id)

    @api.onchange('x_free_worker_id')
    def _onchange_x_free_worker_id(self):
        for aal in self:
            aal.x_partner_id = aal.x_free_worker_id.partner_id

    @api.onchange('project_id')
    def _calculate_default_pause_time(self):
        for aal in self:
            if aal.project_id.id:
                old_all = self.search([('project_id', '=', aal.project_id.id), ('id', '!=', aal.id or -1)],
                                      order='id desc', limit=1)
                if len(old_all) == 1:
                       aal.x_pause_time = old_all.x_pause_time

    @api.constrains('x_rate')
    def _check_x_rate_value(self):
        for aal in self:
            if aal.x_partner_id.id and aal.x_rate == 0.0:
                raise exceptions.ValidationError(_(" The price unit shouldn't be zero. "))

    def _compute_x_margin(self):
        for account_analytic_line in self:
            account_analytic_line.x_margin = account_analytic_line.x_sales_amount - (
                    account_analytic_line.x_pur_amount + account_analytic_line.x_com_amount)

    def _compute_x_pur_amount(self):
        for account_analytic_line in self:
            if account_analytic_line.x_pur_invoice_line_id.id:
                account_analytic_line.x_pur_amount = account_analytic_line.x_pur_invoice_line_id.price_subtotal
            else:
                account_analytic_line.x_pur_amount = account_analytic_line.x_amount

    def _compute_x_com_amount(self):
        for account_analytic_line in self:
            account_analytic_line.x_com_amount = sum(
                account_analytic_line.x_commission_payment_line_ids.mapped('amount'))

    def _compute_x_sales_amount(self):
        for account_analytic_line in self:
            account_analytic_line.x_sales_amount = account_analytic_line.get_sales_tariff() * account_analytic_line.unit_amount

    @api.onchange('project_id')
    def _check_if_project_has_a_related_order(self):
        for aal in self:
            if not aal.project_id.id:
                continue
            if not aal.project_id.sale_order_id.id:
                title = _("Warning poule/project is not related to a sales order")
                message = _(
                    "Project/Poule %s has no related sales order so invoicing is not possible " % aal.project_id.name)
                return {'warning': {'title': title,
                                    'message': message},
                        }

    @api.depends('x_commission_payment_line_ids')
    def _compute_x_commission_created(self):
        for aal in self:
            if len(aal.x_commission_payment_line_ids) > 0:
                aal.x_commission_created = True
            else:
                aal.x_commission_created = False

    @api.depends('x_sale_id', 'x_sale_id.partner_id')
    def _compute_x_customer_id(self):
        for aal in self:
            if aal.x_sale_id.id:
                aal.x_customer_id = aal.x_sale_id.partner_id
            else:
                aal.x_customer_id = False

    def get_sales_tariff(self):
        self.ensure_one()
        if not self.project_id.sale_line_id.id:
            raise exceptions.UserError(_("There is no sales order related to the hour line"))
        if self.project_id.sale_line_id.x_surcharge_amount > 0.0:
            return self.x_rate * self.project_id.sale_line_id.x_surcharge_amount
        else:
            return self.x_rate + self.project_id.sale_line_id.x_price

    def get_gross_margin(self):
        self.ensure_one()
        return self.get_sales_tariff() - self.x_rate

    def get_account_manager(self):
        self.ensure_one()
        partner_account_manager = self.env.company.partner_id
        if self.x_sale_id.partner_id.x_account_manager_partner_id.id:
            partner_account_manager = self.x_sale_id.partner_id.x_account_manager_partner_id
        if self.x_sale_id.x_account_manager_partner_id.id:
            partner_account_manager = self.x_sale_id.x_account_manager_partner_id
        return partner_account_manager

    @api.onchange('x_partner_id', 'project_id', 'date')
    def _compute_hour_line_name(self):
        for ts_line in self:
            if not ts_line.x_partner_id.id:
                continue
            if not ts_line.project_id.id:
                continue
            name = ts_line.x_partner_id.name
            if ts_line.project_id.x_poule_id.id and ts_line.project_id.x_poule_id.description:
                name = name + " - " + ts_line.project_id.x_poule_id.description + " - "
            if ts_line.date:
                date = fields.Date.from_string(ts_line.date)
                str_date = ("0" + str(date.day))[-2:] + "-" + ("0" + str(date.month))[-2:] + "-" + str(date.year)
                name = name + ' ' + str_date
            ts_line.name = name.strip()

    @api.onchange('x_partner_id')
    def _compute_poule_id(self):
        for ts_line in self:
            if not ts_line.x_partner_id:
                continue
            account_analytic_lines = self.env['account.analytic.line'].sudo().search(
                [('x_partner_id', '=', ts_line.x_partner_id.id)
                 ], limit=1, order="date desc");
            if len(account_analytic_lines) != 0:
                ts_line.x_poule_id = account_analytic_lines[0].x_poule_id
                ts_line.project_id = account_analytic_lines[0].project_id
                continue
            poules = ts_line.x_partner_id.x_poule_ids
            if len(poules) > 0:
                ts_line.x_poule_id = poules[0]
                ts_line.project_id = poules[0].project_id

    @api.onchange('project_id')
    def _compute_description(self):
        for ts_line in self:
            if not ts_line.project_id:
                continue;
            description = ts_line.project_id.name;
            if ts_line.project_id.x_poule_id.id != False:
                description = ts_line.project_id.x_poule_id.act_description;
            ts_line.name = description

    @api.onchange('x_from_time')
    def checkStartTime(self):
        for ts_line in self:
            ts_line.x_from_time = ts_line._checkTime(ts_line.x_from_time)

    @api.onchange('x_to_time')
    def checkEndTime(self):
        for ts_line in self:
            ts_line.x_to_time = ts_line._checkTime(ts_line.x_to_time)

    @api.onchange('x_pause_time')
    def checkPauseTime(self):
        for ts_line in self:
            ts_line.x_pause_time = ts_line._checkTime(ts_line.x_pause_time)

    @api.onchange('x_from_time', 'x_to_time', 'x_pause_time')
    def calculatedTotalTime(self):
        for ts_line in self:
            x_from_time = ts_line._checkTime(ts_line.x_from_time)
            x_to_time = ts_line._checkTime(ts_line.x_to_time)
            x_pause_time = ts_line._checkTime(ts_line.x_pause_time)

            x_from_time = ts_line.getTimeInHour(x_from_time)
            x_to_time = ts_line.getTimeInHour(x_to_time)
            x_pause_time = ts_line.getTimeInHour(x_pause_time)

            # 20180201 Totaltime should be calculated when the pause time is 0 or false
            if not x_pause_time:
                x_pause_time = 0
            if x_from_time == False or x_to_time == False:
                ts_line.unit_amount = 0
                continue
            if x_from_time <= x_to_time - x_pause_time:
                ts_line.unit_amount = x_to_time - x_from_time - x_pause_time
            else:
                ts_line.unit_amount = (24 - x_from_time) + x_to_time - x_pause_time

    @api.onchange('x_from_time', 'x_to_time', 'date', 'x_poule_id')
    def calculatedRate(self):
        for ts_line in self:
            if not ts_line.x_poule_id.id:
                continue
            ts_line.x_rate = ts_line.x_poule_id.calculate_rate()

    def getTimeInHour(self, time):
        if not time:
            return time
        if not ':' in time:
            return False
        times = time.split(":")
        min = float(times[1])
        minhour = min * 100 / 60
        return float(times[0]) + minhour / 100

    @api.depends('x_rate', 'unit_amount')
    def _compute_amount(self):
        for ts_line in self:
            amount = 0.0
            if ts_line.x_rate and ts_line.unit_amount:
                amount = ts_line.x_rate * ts_line.unit_amount
            ts_line.x_amount = amount


    def determine_so_line_from_project_id(self, vals):
        if 'project_id' in vals:
            project_obj = self.env['project.project']
            project = project_obj.browse(vals['project_id'])
            if project.sale_line_id.id:
                vals['so_line'] = project.sale_line_id.id
            else:
                vals['so_line'] = False


    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            self._check_duration(vals)
            if 'x_free_worker_id' in vals and 'x_partner_id' not in vals:
                free_worker_obj = self.env['oi1_free_worker']
                free_worker_id = free_worker_obj.browse([vals['x_free_worker_id']])
                vals['x_partner_id'] = free_worker_id.partner_id.id
            if 'x_partner_id' in vals:
                vals['product_uom_id'] = self.env.company.timesheet_encode_uom_id.id
                vals['employee_id'] = self.env.ref('hr.employee_admin').id
            self.determine_so_line_from_project_id(vals)
        return super(AccountAnalyticLine, self).create(vals_list)

    def write(self, values):
        # 2021_0521 A manager of the hours is allowed to archive the hours
        is_a_timesheet_manager = self.env.user.has_group('hr_timesheet.group_timesheet_manager')
        if 'active' in values and not is_a_timesheet_manager:
            raise exceptions.UserError(_("Archiving and unarchiving is only allowed if you're a timesheet administrator"))

        if 'active' in values and is_a_timesheet_manager:
            values['system'] = 1
        if 'system' not in self.env.context:
            if 'system' not in values:
                self._check_duration(values)
                for ts_line in self:
                    ts_line.check_all_is_invoiced
                    if not ts_line.x_partner_id.id:
                        continue
                    invoices_in_concept = self._are_ts_line_invoices_in_concept(ts_line)
                    if invoices_in_concept:
                        continue
                    # 2021_1123 In the state approved it's allowed to change the x_sale_invoice_id
                    #          because the invoice is still on concept this is needed for refunding invoices.
                    keys = ''
                    for key in values.keys():
                        keys = keys + key
                    if ts_line.x_state != 'concept' and keys not in ('x_sale_invoice_line_id'):
                        raise exceptions.UserError(_("Only hourlines in the state concept can be changed"))
        if 'system' in values:
            del values['system']
        self.determine_so_line_from_project_id(values)
        result = super().write(values)
        if result:
            for ts_line in self:
                invoices_in_concept = self._are_ts_line_invoices_in_concept(ts_line)
                if invoices_in_concept:
                    pur_line = ts_line.x_pur_invoice_line_id
                    sale_line = ts_line.x_sale_invoice_line_id

                    quantity = 0
                    account_analytic_line_obj = self.env['account.analytic.line']
                    account_analytic_lines = account_analytic_line_obj.search(
                        [('x_pur_invoice_line_id', '=', pur_line.id)])
                    for aal in account_analytic_lines:
                        quantity = quantity + aal.unit_amount
                    pur_line.with_context(check_move_validity=False).write(
                        {'quantity': quantity, 'price_unit': ts_line.x_rate})
                    quantity = 0
                    account_analytic_line_obj = self.env['account.analytic.line']
                    account_analytic_lines = account_analytic_line_obj.search(
                        [('x_sale_invoice_line_id', '=', sale_line.id)])
                    for aal in account_analytic_lines:
                        quantity = quantity + aal.unit_amount
                    sale_line.with_context(check_move_validity=False).write(
                        {'quantity': quantity, 'price_unit': ts_line.x_rate})
                    SaleInvoice = sale_line.move_id
                    SaleInvoice.set_surcharge_invoiceLine()
        return result

    def _are_ts_line_invoices_in_concept(self, ts_line):
        if ts_line.x_state != 'invoiced':
            return False
        if (ts_line.x_pur_invoice_line_id.id != False and ts_line.x_sale_invoice_line_id != False):
            if ts_line.x_sale_invoice_id.state == 'draft' and ts_line.x_pur_invoice_id.state == 'draft':
                return True
        return False

    def unlink(self):
        for ts_line in self:
            ts_line.check_all_is_invoiced
            if not ts_line.x_partner_id.id:
                continue
            if ts_line.x_state != 'concept':
                raise exceptions.UserError(_("Only hourlines in the state concept can be changed"))
        ts_line = super(AccountAnalyticLine, self).unlink()
        return ts_line

    def _checkTime(self, time):
        if not time:
            return False
        if len(time) == 3 and ':' not in time:
            time = '0' + time[:1] + ':' + time[1:3]
        if len(time) == 4 and ':' not in time:
                time = time[:2] + ":" + time[2:4]
        if len(time) == 4:
            time = '0' + time
        if ',' in time:
            time = time.replace(',', '.')
        if '.' in time:
            times = time.split('.')
            if len(times) == 2:
                min = times[1]
                while len(min) < 2:
                    min = min + '0'
                min = int(int(min) * 60 / 100)
                time = times[0] + ":" + str(min)
        if ':' not in time:
            time = time + ":00"
        if time[2:3] != ':':
            raise exceptions.UserError(_("The time %s should contain a :") % time)
        hours = time[0:2]
        if not hours.isnumeric():
            raise exceptions.UserError(_("The hours should only contain numbers"))
        hours = int(hours)
        if hours < 0:
            raise exceptions.UserError(_("The hours could not be negative"))
        if hours > 23:
            raise exceptions.UserError(_("The hours could not be higher then 23"))
        min = time[3:5]
        if not min.isnumeric():
            raise exceptions.UserError(_("The minutes should only contain numbers"))
        min = int(min)
        if min < 0:
            raise exceptions.UserError(_("The minutes could not be negative"))
        if min > 60:
            raise exceptions.UserError(_("The minutes could not be higher then 60"))
        return time

    def _check_state(self):
        return True

    def _check_duration(self, values):
        for aal in self:
            partner_id = aal.x_partner_id;
            if 'x_partner_id' in values:
                partner_id = values['x_partner_id']
            if not partner_id:
                return
            unit_amount = aal.unit_amount;
            if 'unit_amount' in values:
                unit_amount = values['unit_amount']
            if unit_amount == 0.0:
                raise exceptions.UserError(
                    _("The calculated hours is 0. Please check the filled in start time, end time en pause time"))
            if unit_amount > 24:
                raise exceptions.UserError(_("A day has no more then 24 hours"))

    @api.model
    def check_invoiced(self):
        account_analytic_lines = self.env['account.analytic.line'].search(
            [('x_state', '=', 'customer_invoiced'), ('x_sale_invoice_line_id', '=', False)]);
        account_analytic_lines.write({'x_state': 'approved', 'system': '1'})
        for account_analytic_line in account_analytic_lines:
            if account_analytic_line.x_pur_invoice_line_id.id:
                pur_invoice_line = account_analytic_line.x_pur_invoice_line_id
                if pur_invoice_line.move_id.state == 'draft':
                    pur_invoice_line.with_context({'check_move_validity': False}).unlink()
            for x_commission_payment_line_id in account_analytic_line.x_commission_payment_line_ids:
                if x_commission_payment_line_id.state == 'concept':
                    x_commission_payment_line_id.oi1_sale_commission_id.message_post(body=_((
                            "Payment %s remove with amount %s" % (
                        x_commission_payment_line_id.name,
                        x_commission_payment_line_id.amount))))
                    x_commission_payment_line_id.unlink()

    def check_all_is_invoiced(self):
        for aal in self:
            if aal.x_sale_invoice_line_id.id != False or all.x_pur_invoice_line_id.id != False:
                raise exceptions.UserError(_("This hourline can't be changed. There are invoices related to it"))

    def _find_free_worker(self, partner_id):
        free_worker_obj = self.env['oi1_free_worker']
        if not partner_id.id:
            return
        free_workers = free_worker_obj.search([('partner_id', '=', partner_id.id)])
        if len(free_workers) != 1:
            return False
        return free_workers[0]

    @api.onchange('x_partner_id')
    def notify_if_a_free_worker_has_an_invalid_legitimation(self):
        self.ensure_one()
        free_worker = self._find_free_worker(self.x_partner_id)
        if free_worker:
            has_valid_identification = free_worker.has_a_valid_legitimation
            if not has_valid_identification:
                title = _("No valid identification document")
                message = _("The free worker %s has no valid identification document " % free_worker.name)
                return {'warning': {'title': title,
                                    'message': message},
                        }
        return

    @api.onchange('x_partner_id')
    def notify_if_a_free_worker_has_no_active_commissions(self):
        self.ensure_one()
        free_worker = self._find_free_worker(self.x_partner_id)
        if free_worker:
            has_commissions = len(free_worker.commission_log_ids) > 0
            if not has_commissions:
                title = _("No commissions on free worker")
                message = _("There are no commissions defined on free worker % s" % free_worker.name)
                return {'warning': {'title': title, 'message': message}}
        return
