# -*- coding: utf-8 -*-
{
    'name': "Cash Advance Request",

    'summary': """Cash Advance Request""",

    'description': """Cash Advance Request""",

    'author': "Mahmoud Magdy",
    'website': "",

    'category': 'Payroll',
    'version': '16',

    # any module necessary for this one to work correctly
    'depends': ['base', 'hr_payroll'],

    # always loaded
    'data': [
        'reports/report_cash_advance_request.xml',
        'reports/cash_advance_request_report_template_id.xml',
        'views/hr_salary_attachment_views.xml',
    ],
}
