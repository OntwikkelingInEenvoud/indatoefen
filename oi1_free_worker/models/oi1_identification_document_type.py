from odoo import models, fields


class IdentificationDocumentType(models.Model):
	_name = 'oi1_identification_document_type'
	_description = "Identification document type"
	_order = "name"

	_sql_constraints = [
		('oi1_identification_document_type_name_uniq',
		 'unique (name)',
		 'A name should be defined only once'),
		]
	name = fields.Char(name="name", required=True, translate=True, help="The name of the document type")
