from odoo import models, fields, api


class FreeWorkerPoule(models.Model):
	_name = "oi1_freeworkerpoule"
	_description = "Freeworker poule"
	_order = "sequence,name"
	_inherit = ['mail.thread', 'mail.activity.mixin']
	_inherits = {'project.project': 'project_id'}

	sequence = fields.Integer(required=True, default=1, help = "The sequence field is used to define order in which poules are visible")
	parent_id = fields.Many2one('oi1_freeworkerpoule', string='Parent Poule', index=True, tracking=True, help="The main poule of the poule")
	description = fields.Char('Description', help="The description of the poule for internal use")
	act_description = fields.Char('Activity description', required=True, help="The description of the poule which is soon on the invoices")
	free_worker_ids = fields.Many2many('oi1_free_worker','oi1_poule_free_worker_rel',
									   'poule_id', 'free_worker_id', string='Freeworkers')
	experiences_ids = fields.Many2many('oi1_experience_level', string="Needed experience", tracking=True)
	basichourrate = fields.Monetary('basic hour rate', tracking=True, help="The basic hour rate of the poule which the freeworker is paid when working within the poule")
	currency_id = fields.Many2one('res.currency', compute='_get_currency', string="Currency")
	poule_rate_ids = fields.One2many('oi1_poule_rate', 'poule_id', string="Rates")
	project_id = fields.Many2one('project.project', ondelete='restrict', auto_join=True, required=True)
	product_id = fields.Many2one('product.product', string='Invoice product', required=True, tracking = True, help="The product which is chosen on the invoices when activities within the poule are invoiced ")
	company_id = fields.Many2one('res.company', string='Company', required=True,
								 default=lambda self: self.env.company,
								 help="Company related to this poule")
	child_ids = fields.One2many('oi1_freeworkerpoule','parent_id', string="Child poules")

	def _get_currency(self):
		for poule in self:
			poule.currency_id = self.env.user.company_id.currency_id

	def calculate_rate(self):
		self.ensure_one()
		if not self.basichourrate:
			return 0.0
		return self.basichourrate

	def get_free_worker_poule(self, project_id):
		free_worker_poule_obj = self.env['oi1_freeworkerpoule']
		poule_id = False
		if project_id.id:
			free_worker_poule_list = free_worker_poule_obj.search([('project_id', '=', project_id.id)])
			if len(free_worker_poule_list) > 0:
				poule_id = free_worker_poule_list[0]
		return poule_id
