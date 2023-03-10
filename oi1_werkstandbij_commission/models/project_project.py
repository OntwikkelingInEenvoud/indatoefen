from odoo import models, fields, api

import logging

_logger = logging.getLogger(__name__)


class Project(models.Model):
    _inherit = 'project.project'

    @api.model_create_multi
    def create(self, vals_list):
        free_worker_poule_obj = self.env['oi1_freeworkerpoule']
        try:
            poule_product_id = self.env.ref('oi1_werkstandbij.product_template_default_product_poule')
        except Exception as e:
            _logger.warning(e)
        projects = super().create(vals_list)
        for project in projects:
            #2023_0208  When the project is created with a salesorderline then a poule should be automatically
            #           created. Standard Odoo doesn't create a workpoule. 
            if project.sale_line_id.id:
                values = {'name': project.name,
                          'project_id': project.id,
                          'act_description': project.name,
                          'product_id': poule_product_id.product_variant_id.id,
                          }
                name = (project.name + ' ' + project.sale_line_id.name).strip()
                values['act_description'] = project.sale_line_id.name
                values['description'] = (values['act_description'] + ' ' + project.sale_line_id.name).strip()
                values['name'] = name
                project.write({'name': name})
                free_worker_poule_obj.create(values)
        return projects
