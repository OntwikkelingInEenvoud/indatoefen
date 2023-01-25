from odoo import models, api


class ReportModel(models.AbstractModel):
    _name = 'report.oi1_werkstandbij_commission.active_partner_commissions'
    _description = "Partner active commissions report"

    @api.model
    def _get_report_values(self, docids, data=None):
        """in this function can access the data returned from the button
        click function"""

        partner_id = False
        free_worker = False
        role_commissions = []
        free_worker_obj = self.env['oi1_free_worker']
        free_workers = free_worker_obj.with_context(active_test=False).search([('id', '=', docids[0])])
        if len(free_workers) == 1:
            free_worker = free_workers[0]
            partner_id = free_worker.partner_id

        value = [partner_id.id]
        query = """
                SELECT DISTINCT log.role_id  
                ,  com_rol.name AS role_name 
                FROM oi1_commission_log log 
                INNER JOIN oi1_commission_role com_rol
                    ON log.role_id  = com_rol.id 
                WHERE log.partner_id = %s 
                ORDER BY com_rol.name  
                """
        self._cr.execute(query, value)
        role_records = self._cr.dictfetchall()

        query = """        
        
       SELECT log.partner_id,
       log.start_date, 
       log.end_date, 
       log.name AS log_name,
       log.model_name, 
       log.res_id, 
       log.model_name_res_id, 
       coalesce(log.default_rate,0) AS default_rate,       
       -- rp 
       rp.name AS partner_name, 
       -- com 
       com.name as commission_name,        
       -- com_rol 
       com_rol.name AS rol_name 
       FROM oi1_commission_log log
       INNER JOIN res_partner rp 
        ON log.partner_id = rp.id 
       LEFT JOIN  oi1_commission  com 
        ON log.commission_id = com.id 
       LEFT JOIN oi1_commission_role com_rol 
        ON log.role_id = com_rol.id 
       WHERE log.start_date < CURRENT_DATE 
       AND (log.end_date > CURRENT_DATE or log.end_date is null)
       AND log.partner_id = %s
       and log.role_id = %s       
       
       ORDER by rp.name, com_rol.name, log.model_name_res_id                   
                """

        for rol_record in role_records:
            if partner_id:
                value = [partner_id.id]
            else:
                value = [0]
            value.append(rol_record['role_id'])
            self._cr.execute(query, value)
            records = self._cr.dictfetchall()
            role_commissions.append(records)
        return {
            'role_commissions': role_commissions,
            'free_worker': free_worker

        }