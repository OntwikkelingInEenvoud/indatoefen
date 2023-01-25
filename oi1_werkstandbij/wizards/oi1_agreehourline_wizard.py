from odoo import models, exceptions, _


class AgreeHourLine_Wizard(models.TransientModel):
    _name = "oi1_werkstandbij.agreehourline_wizard"
    _description = "Agree hour lines"

    def do_create_agreements(self):
        hour_lines = self.env['account.analytic.line'].browse(self._context.get('active_ids', []))
        for hour_line in hour_lines:
            if not hour_line.x_partner_id.id:
                continue
            if hour_line.x_state != 'concept':
                continue
            if not hour_line.project_id.id:
                raise exceptions.UserError(
                    _("There is no poule or project related to the hour line. Please correct this"))
            hour_line.write({'x_state': 'approved'})
            if hour_line.x_partner_id.x_freeworker_id.id:
                hour_line.x_partner_id.x_freeworker_id.set_date_last_worked(hour_line)

    def do_create_agreements_and_invoice(self):
        self.do_create_agreements()
        invoice_wizard = self.env['oi1_werkstandbij.invoice_wizard'].create({})
        return invoice_wizard.with_context({"active_ids": self._context.get('active_ids', [])}).do_create_invoices()


