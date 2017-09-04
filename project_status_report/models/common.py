# -*- coding: utf-8 -*-
# Copyright 2017 Camptocamp (<http://www.camptocamp.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _


PYTHON_CODE_DEFAULT = """
<self> is the project for which this indicator is computed
<date> is the date at which the computation is done
<green>, <orange> and <red> are strings containing the RGB code for the colors

the code must set the value of the following variables
<value>: a float or boolean or string
        (depending on the value_type of the indicator)
<color>: a string containing the RGB code associated
        to the value of the indicator
"""

INDICATOR_STATUS = [('ok', _('OK')),
                    ('attention', _('Attention')),
                    ('alert', _('Alert')),
                    ]

TASK_FIELDS_TO_SYNC = {
    'user_id': 'm2o',
    'date_deadline': 'simple',
    'progress': 'simple',
    'planned_hours': 'simple',
    'kanban_state': 'simple',
    'stage_id': 'm2o',
}
