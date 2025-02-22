# Copyright (c) 2025, MD Kaleem  and contributors
# For license information, please see license.txt


from frappe.utils import getdate, today, date_diff, flt
from collections import defaultdict

import frappe
from frappe.model.document import Document



class NPFGratuity(Document):


	def before_insert(self):
		self.salary_component = "Gratuity Pay"
		employee_doc = frappe.get_doc("Employee", self.employee)

		leave_records = frappe.get_all("Leave Application", filters={"leave_type": "Leave Without Pay", "employee": self.employee})
		
		if not leave_records:
			frappe.msgprint("Employee has not taken any Leave Without Pay")
		
		if not employee_doc:
			frappe.throw("Please Select Proper Employee")
		
		if not employee_doc.date_of_joining:
			frappe.throw("Date of Joining is not set for the selected Employee")
		
		joining_date = getdate(employee_doc.date_of_joining)
		current_date = getdate(today())
		self.current_work_experience = date_diff(current_date, joining_date) // 365
		
		basic_pay = next(
			(amount.amount for amount in employee_doc.custom_earnings 
			 if amount.salary_component == "Basic Pay"), 0
		)
	 
		if basic_pay <= 0:
			frappe.throw("Basic Pay is not set for the selected Employee")
		leave_by_year = defaultdict(list)
		for record in leave_records:
			year = record["from_date"].year
			leave_by_year[year].append(record)
		twentone_days = 0 
		thaty_days = 0   
		if self.current_work_experience < 1:
			self.custom_amount = 0
		elif self.current_work_experience < 5:
			for year in range(1, self.current_work_experience + 1):
				leave_days_in_year = sum(
					(date_diff(record["to_date"], record["from_date"]) + 1) 
					for record in leave_by_year.get(year, [])
				)
				twentone_days += leave_days_in_year
			self.custom_amount = flt((basic_pay / 30) * 21 - twentone_days * self.current_work_experience)
		else:
			for year in range(1, 6):
				leave_days_in_year = sum(
					(date_diff(record["to_date"], record["from_date"]) + 1) 
					for record in leave_by_year.get(year, [])
				)
				twentone_days += leave_days_in_year
			gratuity_for_first_5_years = flt((basic_pay / 30) * 21 - twentone_days * 5)
			for year in range(6, self.current_work_experience + 1):
				leave_days_in_year = sum(
					(date_diff(record["to_date"], record["from_date"]) + 1) 
					for record in leave_by_year.get(year, [])
				)
				thaty_days += leave_days_in_year
			gratuity_for_first_5_years = flt((basic_pay / 30) * 21 - twentone_days * 5)
			gratuity_for_remaining_years = flt((basic_pay / 30) * 30 - thaty_days * (self.current_work_experience - 5))
			self.custom_amount = gratuity_for_first_5_years + gratuity_for_remaining_years



	def on_submit(self):
		new_additional_salary = frappe.new_doc("Additional Salary")
		new_additional_salary.update({
			"employee":self.employee,
			"company":self.company,
			"payroll_date":self.payroll_date,
			"salary_component":"Gratuity Pay",
			"currency":"AED",
			"amount": self.custom_amount,
			"docstatus":1

		})
		new_additional_salary.insert()
		frappe.db.commit()
