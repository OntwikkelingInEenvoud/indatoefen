# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase, tagged
from odoo.exceptions import UserError
import datetime


@tagged('post_install', 'test_resource_calendar_attendance_workday_part')
class TestResourceCalendarAttendanceWorkDayPart(TransactionCase):

	def setUp(self, *args, **kwargs):
		result = super().setUp(*args, **kwargs)
		self.env.user.lang = False
		return result

	def test_create_ResourceCalendarAttendanceWorkDayPart(self):
		work_day_part_obj = self.env['oi1_resource_calendar_attendance_workday_part']
		work_day_part = work_day_part_obj.create({'dayofweek': '1', 'day_period': 'night'})
		self.assertEqual(work_day_part.sequence, 14)
		self.assertEqual(work_day_part.code, 'Tuesday.night')




