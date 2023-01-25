from odoo import models


class AttachmentImport(models.TransientModel):
    _inherit = 'oi1_odooimport'

    def do_import_attachments(self, records):
        attachment_obj = self.env['ir.attachment']
        table_conversion_obj = self.env['oi1_dataimport.table_conversion']

        for record in records:
            print(record)
            res_model = False
            store_fname = False
            if 'store_fname' in record:
                store_fname = record['store_fname']
                fnames = store_fname.split(":\\")
                if len(fnames) > 1:
                    store_fname = fnames[1]
                store_fname = store_fname.replace("\\", "/")
            if 'res_model' in record:
                res_model = record['res_model']
            if not store_fname:
                print("Record wordt niet ingelezen, omdat er geen document locatie is meegegeven")
                continue
            if not res_model:
                print("Record wordt niet ingelezen, omdat er geen model is meegegeven")
                continue
            attachment = False
            attachments = attachment_obj.search([('store_fname', '=', store_fname)])
            if len(attachments) > 0:
                attachment = attachments[0]
            if not attachment:
                names = store_fname.split('/')
                name = names[len(names) - 1]
                attachment = attachment_obj.create({'store_fname': store_fname, 'name': name})
            if 'res_id_x_prev_code' in record:
                x_prev_code = record['res_id_x_prev_code']
                tables = table_conversion_obj.search([('prev_code', '=', x_prev_code),
                                                      ('res_model_name', '=', res_model)
                                                      ])
                if len(tables) > 0:
                    attachment.res_id = tables[0].res_id
            if 'res_id' in record:
                attachment.res_id = record['res_id']
            if 'res_model' in record:
                attachment.res_model = record['res_model']
            if 'name' in record:
                attachment.name = record['name']
            if store_fname:
                attachment.store_fname = store_fname
                extensions = store_fname.split(".")
                extension = extensions[len(extensions) - 1].strip().lower()
                names = store_fname.split('/')
                name = names[len(names) - 1]
                attachment.datas_fname = name
                if extension == 'pdf':
                    attachment.mimetype = 'application/pdf'
                    attachment.index_content = 'application'

            self.env.cr.commit();
            print(attachment.id)
