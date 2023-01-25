from odoo import models, fields, _
from odoo.exceptions import UserError
import datetime

import xml.etree.ElementTree as ET


class ExportWsbWizard(models.TransientModel):
    _name = "oi1_werkstandbij.export_wsb_wizard"
    _description = "Export WSB Wizard"

    path = fields.Char("FilePath", default="/home/odoodev/odoo")

    def set_export_to_wsb(self):
        account_move_obj = self.env['account.move']
        factoring_export_obj = self.env['oi1_werkstandbij.factoring_export']
        factoring_export = False

        for wizard in self:
            data = ET.Element('Export')

            account_moves = account_move_obj.search([('state', '=', 'Start_Factoring')])

            if len(account_moves) > 0:
                export_name = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
                factoring_export = factoring_export_obj.create({'name': export_name})
                data.set('name', export_name)

            element_company = ET.SubElement(data, 'Company')
            self.set_partner_data_to_xml(self.env.company.partner_id, element_company)

            element_partners = ET.SubElement(data, 'Partners')

            for partner_id in account_moves.mapped('commercial_partner_id'):
                element_partner = ET.SubElement(element_partners, 'Partner')
                self.set_partner_data_to_xml(partner_id, element_partner)

            element_invoices = ET.SubElement(data, 'Invoices')

            for account_move in account_moves:
                self.set_account_move_to_xml(account_move, element_invoices)
                account_move.x_factoring_export_id = factoring_export

            account_moves.state = 'Factored'

            ET.indent(data)
            b_xml = ET.tostring(data, encoding='unicode', method='xml')
            print(b_xml)
            with open(wizard.path + "/test.xml", "wb") as f:
                f.write(b_xml.encode())

    @staticmethod
    def set_partner_data_to_xml(partner_id, element_partner):
        ET.SubElement(element_partner, 'Code').text = partner_id.x_prev_code
        ET.SubElement(element_partner, 'Name').text = partner_id.name
        ET.SubElement(element_partner, 'Email').text = partner_id.email

    @staticmethod
    def set_account_move_to_xml(move_id, element_invoices):
        element_account_move = ET.SubElement(element_invoices, 'Invoice')
        ET.SubElement(element_account_move, 'PartnerCode').text = move_id.partner_id.x_prev_code
        ET.SubElement(element_account_move, 'Name').text = move_id.name
        ET.SubElement(element_account_move, 'MoveType').text = move_id.move_type
        ET.SubElement(element_account_move, 'AmountTotal').text = str(move_id.amount_total)

