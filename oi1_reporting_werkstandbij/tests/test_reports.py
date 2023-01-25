# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase, tagged, Form
import logging

_logger = logging.getLogger(__name__)


@tagged('post_install', 'oi1')
class TestReports(TransactionCase):

    def test_create_res_partner(self):
        partner_form = Form(self.env['res.partner'])
        partner_form.name = 'a partner'
        partner_form.save()

    """
    def test_reports(self):
        domain = [('report_type', 'like', 'qweb'), ('report_name', 'like', 'oi1_')]
        for report in self.env['ir.actions.report'].search(domain):
            report_model = 'report.%s' % report.report_name
            try:
                self.env[report_model]
            except KeyError:
                # Only test the generic reports here
                _logger.info("testing report %s", report.report_name)
                report_model = self.env[report.model]
                report_records = report_model.search([], limit=10)
                if not report_records:
                    _logger.info("no record found skipping report %s", report.report_name)
                if not report.multi:
                    report_records = report_records[:1]

                # Test report generation
                report.render_qweb_html(report_records.ids)
            else:
                continue
    """