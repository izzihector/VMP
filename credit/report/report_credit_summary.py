# -*- coding:utf-8 -*-

from odoo import models, api

from datetime import date, datetime


class ReportCreditSummaryIndividual(models.AbstractModel):
    _name = 'report.credit.report_credit_summary_individual'

    @api.model
    def _get_report_values(self, docids, data=None):
        partner_id = self._context.get('partner_id')
        partner = self.env['res.partner'].browse(partner_id)
        partner_ids = [partner_id, partner.parent_id.id]
        contract_id = self.env['contract.contract'].search([('partner_id', '=', partner_ids),
                                                            ('type_contract', '=', 'credito')])
        if contract_id:
            if contract_id[0].payment_term_id:
                result = contract_id[0].payment_term_id.compute(5, data['end_date'])
                max_pay_date = date.strftime(datetime.strptime(result[0][0][0], '%Y-%m-%d'), '%d-%b-%Y')
        return {
            'data': data,
            "company_currency": self.env.user.company_id.currency_id,
            "partner": partner,
            "max_pay_date": max_pay_date
        }


class ReportCreditSummary(models.AbstractModel):
    _name = 'report.credit.report_credit_summary'

    @api.model
    def _get_report_values(self, docids, data=None):
        partner_id = self._context.get('partner_id')
        partner = self.env['res.partner'].browse(partner_id)
        partner_ids = [partner_id, partner.parent_id.id]
        contract_id = self.env['contract.contract'].search([('partner_id', '=', partner_ids),
                                                            ('type_contract', '=', 'credito')])
        if contract_id:
            if contract_id[0].payment_term_id:
                result = contract_id[0].payment_term_id.compute(5, data['end_date'])
                max_pay_date = date.strftime(datetime.strptime(result[0][0][0], '%Y-%m-%d'), '%d-%b-%Y')
        return {
            'data': data,
            'company_currency': self.env.user.company_id.currency_id,
            'partner': partner,
            "max_pay_date": max_pay_date
        }