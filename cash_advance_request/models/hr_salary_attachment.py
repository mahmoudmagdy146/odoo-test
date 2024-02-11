# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError
from docxtpl import DocxTemplate, InlineImage
import os
import tempfile
import binascii
import base64
from subprocess import Popen
from docx.shared import Mm


class HrSalaryAttachment(models.Model):
    _inherit = 'hr.salary.attachment'

    def action_print(self):
        for rec in self:
            template_name = 'cash_advance_request'
            full_path = os.path.realpath(__file__)
            path = full_path.split('/')
            path = path[0:-2]
            path = '/'.join(path)
            c_p = path + '/static/docs/'

            if not c_p:
                raise ValidationError('Check addon paths on configuration file')
            doc = DocxTemplate(c_p + template_name + ".docx")


            logo = False
            vat_image = False
            if rec.company_id.logo:
                image = tempfile.NamedTemporaryFile(suffix=".png")
                image.write(binascii.a2b_base64(rec.company_id.logo))
                logo = InlineImage(doc, image_descriptor=image, width=Mm(30), height=Mm(30))
            data_lines = []

            context = {
                'logo': logo,
                'en_id_code_name': '',
                'ar_id_code_name': '',
                'en_name': '',
                'ar_name': '',
                'en_id_no': '',
                'ar_id_no': '',
                'en_id_type': '',
                'ar_id_type': '',
                'en_start_date': '',
                'ar_start_date': '',
                'en_org_div': '',
                'ar_org_div': '',
                'en_assign_job': '',
                'ar_assign_job': '',
                'en_sal_wage': '',
                'ar_sal_wage': '',
                'account_number': '',
                'en_currency': '',
                'ar_currency': '',
                'en_amount_in_words': '',
                'ar_amount_in_words': '',
                'en_deduct_no': '',
                'ar_deduct_no': '',
                'en_payment_num': '',
                'ar_payment_num': '',
                'en_payment_start_date': '',
                'ar_payment_start_date': '',
                'en_payment_end_date': '',
                'ar_payment_end_date': '',
                'en_beneficiary_sign': '',
                'ar_beneficiary_sign': '',
                'en_name_manager': '',
                'ar_name_manager': '',
                'en_sign_manager': '',
                'ar_sign_manager': '',
            }
            doc.render(context)
            file_number = template_name + '.pdf'
            doc.save('/tmp/' + template_name + '.docx')
            LIBRE_OFFICE = '/usr/lib/libreoffice/program/soffice'

            def convert_to_pdf(input_docx, out_folder):
                p = Popen([LIBRE_OFFICE, '--headless', '--convert-to', 'pdf', '--outdir',
                           out_folder, input_docx])
                p.communicate()

            convert_to_pdf('/tmp/' + template_name + '.docx', '/tmp')
            file_name = '/tmp/' + template_name + '.pdf'
            with open(file_name, 'rb') as fh:
                buf = fh.read()
            b64_pdf = base64.b64encode(buf)
            res = self.env['ir.attachment'].create({
                'name': file_number,
                'datas': b64_pdf,
                'store_fname': file_number,
                'type': 'binary'
            })
            url = '/web/content/%s?download=true' % res.id
            return {
                'type': 'ir.actions.act_url',
                'url': url,
                'target': 'new',
            }
