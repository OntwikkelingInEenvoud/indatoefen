from odoo import models, api

import logging

_logger = logging.getLogger(__name__)


class AccountAccount(models.TransientModel):
    _name = 'convert_to_sale_order_line'
    _description = 'convert_to_sale_order_line'

    @api.model
    def do_cron_convert_sale_order_line_invoiced(self):
        sale_order_line_obj = self.env['sale.order.line']
        sale_order_lines = sale_order_line_obj.search([])
        sale_order_lines._compute_untaxed_amount_invoiced()

    @api.model
    def convert_poule_to_sale_order_line(self):
        sale_order_obj = self.env['sale.order']
        sale_order_line_obj = self.env['sale.order.line']
        free_worker_poule_obj = self.env['oi1_freeworkerpoule']
        project_project_obj = self.env['project.project']
        product_template_free_worker = self.env.ref('oi1_werkstandbij.product_template_free_workers_poule')
        sale_orders = sale_order_obj.search([('company_id', '=', self.env.company.id)])
        for sale_order in sale_orders:
            sale_order_lines = sale_order.order_line
            if len(sale_order_lines) > 0:
                _logger.info("Removing saleorderlines of order " + sale_order.name)
                sale_order.action_cancel()
                sale_order.order_line.unlink()
                sale_order.action_draft()
                sale_order.action_confirm()
            free_worker_poule = sale_order.x_poule_id
            values = {'order_id': sale_order.id,
                      'product_id': product_template_free_worker.product_variant_id.id,
                      'x_price': sale_order.x_price,
                      'x_surcharge_amount': sale_order.x_surcharge_amount
                      }
            sale_order_line = sale_order_line_obj.create(values)
            project_project = project_project_obj.search([('sale_line_id', '=', sale_order_line.id)])
            for created_free_worker_poule in project_project.x_poule_ids:
                created_free_worker_poule.unlink()
            project_project.unlink()
            project_id = free_worker_poule.project_id
            project_id.write({'sale_order_id': sale_order.id,
                              'sale_line_id': sale_order_line.id,
                              'partner_id': sale_order.partner_id.id,
                              })
            sale_order_line.write({'project_id': project_id.id, })
            sale_order.x_wsb_ssf_commission_id = self.env.ref('oi1_werkstandbij.oi1_commission_wsb_ssf')
