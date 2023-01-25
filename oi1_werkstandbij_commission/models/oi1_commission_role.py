from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class CommissionRole(models.Model):
	_name = "oi1_commission_role"
	_description = "Commission_role"

	name = fields.Char('name', translate=True)
	description = fields.Char('description', translate=True)

	@api.model
	def get_seller_role(self):
		try:
			return self.env.ref('oi1_werkstandbij_commission.oi1_commission_role_sales')
		except Exception as e:
			_logger.warning(e)
			return False

	@api.model
	def get_reservation_role(self):
		try:
			return self.env.ref('oi1_werkstandbij_commission.oi1_commission_role_reservation')
		except Exception as e:
			_logger.warning(e)
			return False

	@api.model
	def get_account_manager_role(self):
		try:
			return self.env.ref('oi1_werkstandbij_commission.oi1_commission_role_account_manager')
		except Exception as e:
			_logger.warning(e)
			return False

	@api.model
	def get_assistant_account_manager_role(self):
		try:
			return self.env.ref('oi1_werkstandbij_commission.oi1_commission_role_assistant_account_manager')
		except Exception as e:
			_logger.warning(e)
			return False

	@api.model
	def get_operational_work_planner_role(self):
		try:
			return self.env.ref('oi1_werkstandbij_commission.oi1_commission_role_operational_work_planner')
		except Exception as e:
			_logger.warning(e)
			return False

	@api.model
	def get_poule_manager_role(self):
		try:
			return self.env.ref('oi1_werkstandbij_commission.oi1_commission_role_poule_manager')
		except Exception as e:
			_logger.warning(e)
			return False

	@api.model
	def get_mediator_role(self):
		try:
			return self.env.ref('oi1_werkstandbij_commission.oi1_commission_role_mediator')
		except Exception as e:
			_logger.warning(e)
			return False

	@api.model
	def get_recruiter_role(self):
		try:
			return self.env.ref('oi1_werkstandbij_commission.oi1_commission_role_recruiter')
		except Exception as e:
			_logger.warning(e)
			return False

	@api.model
	def get_practical_work_planner_role(self):
		try:
			return self.env.ref('oi1_werkstandbij_commission.oi1_commission_role_practical_work_planner')
		except Exception as e:
			_logger.warning(e)
			return False


