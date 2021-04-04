# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _


class AppManager(models.Model):
    _name = 'app.manager'
    _description = 'App Manager management details'
    _rec_name = 'kanban_version'
    _order = 'id'

    xml_kanban = fields.Text(
        string='Kanban code'
    )

    kanban_version = fields.Float(
        string='Version'
    )