# -*- coding: utf-8 -*-
# Copyright 2017 Camptocamp (<http://www.camptocamp.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import api, fields, models
from odoo import _
from .common import INDICATOR_STATUS


class ProjectStatusReport(models.Model):
    _name = 'project.status.report'
    _inherit = ['mail.thread']
    _order = 'date desc, name'

    @api.depends('project_id', 'date')
    def _compute_name(self):
        """
        Compute the name of the status report.
        project_id.name + ' ' + date
        """
        for rec in self:
            rec.name = '%s %s' % (self.project_id.name or "",
                                  fields.Datetime.to_string(self.date)
                                  )

    date = fields.Date(required=True,
                       default=fields.Date.today(),
                       states={'draft': [('readonly', True)]})
    project_id = fields.Many2one(comodel_name='project.project',
                                 required=True,
                                 states={'draft': [('readonly', True)]})
    name = fields.Char(compute='_compute_name',
                       store=True,
                       states={'draft': [('readonly', True)]})
    cost_status = fields.Selection(selection=INDICATOR_STATUS,
                                   states={'draft': [('readonly', True)]})
    cost_color = fields.Char(states={'draft': [('readonly', True)]})
    cost_remarks = fields.Html(states={'draft': [('readonly', True)]})
    quality_status = fields.Selection(selection=INDICATOR_STATUS,
                                      states={'draft': [('readonly', True)]})
    quality_color = fields.Char(states={'draft': [('readonly', True)]})
    quality_remarks = fields.Html(states={'draft': [('readonly', True)]})
    delay_status = fields.Selection(selection=INDICATOR_STATUS,
                                    states={'draft': [('readonly', True)]})
    delay_color = fields.Char(states={'draft': [('readonly', True)]})
    delay_remarks = fields.Html(states={'draft': [('readonly', True)]})
    global_status = fields.Selection(selection=INDICATOR_STATUS,
                                     states={'draft': [('readonly', True)]})
    global_color = fields.Char(states={'draft': [('readonly', True)]})
    global_remarks = fields.Html(states={'draft': [('readonly', True)]})
    risks = fields.Html(states={'draft': [('readonly', True)]})
    user_id = fields.Many2one(comodel_name='res.users',
                              related='project_id.user_id',
                              stored=True,
                              readonly=True)
    indicator_ids = fields.One2many('project.status.indicator.value',
                                    'report_id',
                                    states={'draft': [('readonly', True)]})
    task_snapshot_ids = fields.One2many('project.task.snapshot',
                                        'report_id',
                                        states={'draft': [('readonly', True)]})
    state = fields.Selection(selection=[('draft', _('Draft')),
                                        ('ready', _('Ready')),
                                        ('published', _('Published'))
                                        ],
                             string='Status', readonly=True, copy=False,
                             index=True, track_visibility='onchange',
                             default='draft'
                             )

    @api.multi
    def action_confirm(self):
        self.state = 'ready'

    @api.multi
    def action_validate(self):
        self.state = 'published'

    @api.model
    def compute_indicator_values(self, project, report):
        indicators = self.env['project.status.indicator.value'].browse()
        for indicator in self.env['project.status.indicator'].search([]):
            indicators |= indicator.compute_value(project, report.date)
        return indicators

    @api.model
    def create_task_snapshots(self, project, report):
        tasks = self.env['project.task.snapshot'].browse()
        task_snap_obj = self.env['project.task.snapshot']
        for task in project.task_ids:
            tasks |= task_snap_obj.create({'task_id': task.id})
        return tasks

    @api.model
    def compute_last_statuses(self, project):
        res = {}
        fields = [
            'cost_status',
            'cost_color',
            'cost_remarks',
            'quality_status',
            'quality_color',
            'quality_remarks',
            'delay_status',
            'delay_color',
            'delay_remarks',
            'global_status',
            'global_color',
            'global_remarks',
            'risks'
        ]
        # find last report for the given project
        last_report = self.search([('project_id', '=', project.id),
                                   ('state', '=', 'published')], limit=1)
        for f in fields:
            res[f] = last_report[f]

        return res

    @api.model
    def create(self, values):
        report = super(ProjectStatusReport, self).create(values)
        last_statuses = self.compute_last_statuses(report.project_id)
        task_snapshots = self.create_task_snapshots(report.project_id,
                                                    report)
        indicator_values = self.compute_indicator_values(report.project_id,
                                                         report)
        update_dict = {
            'indicator_ids': (0, 0, indicator_values.ids),
            'task_snapshot_ids': (0, 0, task_snapshots.ids),
        }
        update_dict.update(last_statuses)

        report.write(update_dict)

        return report
