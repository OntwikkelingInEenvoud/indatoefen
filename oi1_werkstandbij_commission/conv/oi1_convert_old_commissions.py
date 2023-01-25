from odoo import models, fields, api, exceptions, _
from datetime import timedelta


class SaleCommissionPartnerDeclaration(models.Model):
	_name = "oi1_sale_commission_partner_declaration"
	_description = "Sale commissions to pay by partners"

class SaleCommission(models.Model):
	_name = "oi1_sale_commission"