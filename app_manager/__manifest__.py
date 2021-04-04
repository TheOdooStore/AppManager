# -*- coding: utf-8 -*-
{
    'name': "AppManager",

    'summary': """
        AppManager: the number one way to manage your external apps!""",

    'description': """
        AppManager is here to help you manage all your external apps.
    """,

    'author': "The Odoo Store",
    'website': "http://www.theodoostore.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.0.1',

    # any module necessary for this one to work correctly
    'depends': ['product'],

    # always loaded
    'data': [
        # Default data
        'data/app_manager_data.xml',
        'data/mail_data.xml',

        # Cron job
        'data/ir_cron_module.xml',

        'security/ir.model.access.csv',
        'views/ir_module_module_views.xml',
        'views/app_manager_views.xml',
        'views/res_config_settings_view.xml',
        'views/actions.xml',
        'views/menus.xml',
    ],
}
