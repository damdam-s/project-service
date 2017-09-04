# -*- coding: utf-8 -*-
# Copyright 2017 Camptocamp (<http://www.camptocamp.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import api, fields, models
from odoo import _, exceptions
from odoo import SUPERUSER_ID

import sys
import compiler
import traceback

from .common import PYTHON_CODE_DEFAULT

import logging
logger = logging.getLogger('project_status_indicator')


class ProjectStatusIndicator(models.Model):
    _name = 'project.status.indicator'

    _order = 'sequence'

    name = fields.Char(required=True, translate=True)
    report_id = fields.Many2one(comodel_name='project.status.report')
    sequence = fields.Integer(default=10)
    value_type = fields.Selection(selection=[('numeric', _('Numeric')),
                                             ('boolean', _('Boolean')),
                                             ('text', _('Text'))
                                             ],
                                  required=True,
                                  )
    python_code = fields.Text(default=PYTHON_CODE_DEFAULT)

    @api.multi
    @api.constrains('python_code')
    def _check_python_code_syntax(self):
        """
        Syntax check the python code of a step
        """
        for step in self:
            try:
                compiler.parse(step.python_code)
            except SyntaxError, exception:
                logger.error(''.join(traceback.format_exception(
                    sys.exc_type,
                    sys.exc_value,
                    sys.exc_traceback,
                )))
                raise exceptions.ValidationError(
                    _('Error in python code for step "%s"'
                      ' at line %d, offset %d:\n%s') % (
                        step.name,
                        exception.lineno,
                        exception.offset,
                        exception.msg,
                    ))

        return True

    @api.multi
    def compute_value(self, project, date):
        ld = {
            'self': project,
            'date': date,
            'green': '#00FF00',
            'orange': '#FF6600',
            'red': '#FF0000',
            'color': '#00FF00',
            'value': None
        }

        exec self.python_code in ld

        vals = {
            'indicator_id': self.id,
            'report_id': self.report_id.id,
            'color': ld.get('color', '#00FF00'),
            ('value_%s' % self.value_type): ld.get('value', None),
        }

        indicator_value = self.env[
            'project.status.indicator.value'].create(vals)

        return indicator_value


class ProjectStatusIndicatorValue(models.Model):
    _name = 'project.status.indicator.value'

    _order = 'project_id, date, sequence'

    @api.depends('value_type', 'value_boolean', 'value_float', 'value_text')
    def _compute_display_value(self):
        for rec in self:
            rec.display_value = '%s' % rec['value_'+rec.value_type]

    indicator_id = fields.Many2one(comodel_name='project.status.indicator',
                                   required=True)
    report_id = fields.Many2one(comodel_name='project.status.report',
                                required=True)
    project_id = fields.Many2one(comodel_name='project.project',
                                 related='report_id.project_id',
                                 store=True,
                                 readonly=True)
    date = fields.Date(related='report_id.date',
                       store=True,
                       readonly=True
                       )
    name = fields.Char(related='indicator_id.name',
                       store=True,
                       readonly=True)
    sequence = fields.Integer(related='indicator_id.sequence',
                              store=True,
                              readonly=True)
    value_type = fields.Selection(related='indicator_id.value_type',
                                  store=True,
                                  readonly=True)
    value_float = fields.Float()
    value_boolean = fields.Boolean()
    value_text = fields.Text()
    display_value = fields.Char(string='Value',
                                compute='_compute_display_value')
    color = fields.Char(size=7, required=True)

    _sql_constraint = [('unique value per indicator report',
                        'UNIQUE (indicator_id, report_id)',
                        'Value must be unique per indicator/report')]

    @api.model
    def create(self, values):
        """
            allow users != admin to create records only if the context
            contains the key 'status_report_creation'=True
        """
        if self.env.user.id != SUPERUSER_ID:
            if not self.env.context.get('status_report_creation', False):
                # TODO: check if AccessDenied or UserError ?
                raise exceptions.AccessDenied(
                    _('User %s tried to create a record') % self.env.user.id)

        return super(ProjectStatusIndicatorValue, self).create(values)

    @api.multi
    def write(self, values):
        """
        allow users != admin to write records only if the context
        contains the key 'status_report_creation'=True
        """
        if self.env.user.id != SUPERUSER_ID:
            if not self.env.context.get('status_report_creation', False):
                # TODO: check if AccessDenied or UserError ?
                raise exceptions.AccessDenied(
                    _('User %s tried to create a record') % self.env.user.id)
        return super(ProjectStatusIndicatorValue, self).write(values)
