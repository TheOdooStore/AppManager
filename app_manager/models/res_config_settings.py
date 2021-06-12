# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    receive_app_update_mails = fields.Boolean(
        string='Receive app update e-mails',
        default=True,
        config_parameter='app_manager.receive_app_update_mails',
    )

    app_update_mail_template_id = fields.Many2one(
        'mail.template',
        string='E-mail template',
        default=lambda self: self.env.ref('app_manager.mail_template_app_updates'),
        domain=[('model_id.model', '=', 'ir.module.module')],
        config_parameter='app_manager.app_update_mail_template_id')

    app_update_user_id = fields.Many2one(
        'res.users',
        string='Users',
        default=lambda self: self.env.ref('base.user_admin'),
        config_parameter='app_manager.app_update_user_id'
    )

    app_storage_location = fields.Char(
        string='Location to download apps too',
        help='This will be the default location where we store downloaded apps for you to use.',
        config_parameter='app_manager.app_storage_location'
    )
