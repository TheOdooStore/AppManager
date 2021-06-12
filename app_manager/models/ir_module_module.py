# -*- coding: utf-8 -*-
import requests
import json
import logging
import tempfile
import os
import io
import shutil
import zipfile
import odoo
from odoo.exceptions import UserError, AccessDenied
from odoo import models, fields, api, _, tools, modules

_logger = logging.getLogger(__name__)


def backup(path, raise_exception=True):
    """
        Creates a temp backup of the code in case anything fails. It will be removed again if all went well.
    """
    path = os.path.normpath(path)
    if not os.path.exists(path):
        if not raise_exception:
            return None
        raise OSError("The path '%s' does not exist on the server." % path)
    cnt = 1
    while True:
        bck = '%s~%d' % (path, cnt)
        if not os.path.exists(bck):
            shutil.move(path, bck)
            return bck
        cnt += 1


class IrModuleModule(models.Model):
    _inherit = 'ir.module.module'

    store_version = fields.Char(
        string='Remote version'
    )

    store_url = fields.Char(
        string='Store URL'
    )

    store_download_url = fields.Char(
        string='Store download URL'
    )

    store_is_free = fields.Boolean(
        string='Is free'
    )

    store_app = fields.Boolean(
        string='Store app'
    )

    store_update_available = fields.Boolean(
        string='Remote update available'
    )

    store_is_certified = fields.Boolean(
        string='Certified app'
    )

    store_has_security_issue = fields.Boolean(
        string='Has security issue'
    )

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        """
            Override of the fields_view_get to inject our custom XML view if the view is "store_manager".
        """
        res = super(IrModuleModule, self).fields_view_get(view_id, view_type, toolbar=toolbar, submenu=False)
        if view_type == 'kanban' and "store_manager" in res.get('arch'):
            res['arch'] = self.env['app.manager'].sudo().search([], limit=1).xml_kanban
        return res

    @api.model
    def get_app_store_server(self):
        """
            Returns the URL endpoint to The Odoo Store
        """
        return 'https://www.theodoostore.com'

    def _download_remote_app_code(self):
        """
            Makes a call to the external apps server, requests the zipped app, puts it in our local path and unzips it.
        """
        tmp = tempfile.mkdtemp()
        download_url = self.store_download_url

        try:
            _logger.info('Downloading module `%s` from appstore.', self.name)
            response = requests.get(download_url)
            response.raise_for_status()
            content = response.content
        except Exception:
            _logger.exception('Failed to fetch module %s from %s', self.name, download_url)
            raise UserError(
                _('The `%s` module appears to be unavailable at the moment. Please try again later.') % self.name)
        else:
            zipfile.ZipFile(io.BytesIO(content)).extractall(tmp)
            assert os.path.isdir(os.path.join(tmp, self.name))

        module_path = modules.get_module_path(self.name, downloaded=True, display_warning=False)

        bck = backup(module_path, False)
        _logger.info('Copy downloaded module `%s` to `%s`', self.name, module_path)
        shutil.move(os.path.join(tmp, self.name), module_path)
        if bck:
            # All went well - removing the backup
            shutil.rmtree(bck)

        self.update_list()

    def _update_app_code(self):
        """
            Triggers an actual update of the code and updates the database thanks to the button_immediate_install().
        """
        downloaded = self.search([('name', '=', self.name)])
        installed = self.search([('id', 'in', downloaded.ids), ('state', '=', 'installed')])

        to_install = self.search([('name', 'in', list(self.name)), ('state', '=', 'uninstalled')])
        post_install_action = to_install.button_immediate_install()

        if installed or to_install:
            # in this case, force server restart to reload python code...
            self._cr.commit()
            odoo.service.server.restart()
            return {
                'type': 'ir.actions.client',
                'tag': 'home',
                'params': {'wait': True},
            }

        return post_install_action

    def _validate_configuration_and_access(self):
        """
            Checks if the AppManager has been configured and if the user pressing update buttons has enough rights.
        """
        # See if the user configured a module path in our configuration view.
        app_storage_location = self.env['ir.config_parameter'].sudo().get_param('app_manager.app_storage_location')
        if not app_storage_location:
            raise UserError(_('We cannot download this app as you haven\'t configured a download path yet.\n'
                            'You can do this from AppManager > Settings.'))

        # We'll only allow people with group_system rights to do these kind of operations.
        if not self.env.user.has_group('base.group_system'):
            raise AccessDenied()

        # Check if the directory exists and if we have enough access rights.
        if not os.access(app_storage_location, os.W_OK):
            raise UserError(_('The location specified is not accessible by the Odoo user.\n'
                              'Please make sure the directory exists and is writable.'))

    def download_remote_app(self):
        """
            Main function to handle app downloading logic. Does the following:
            1. Check if user has enough access and if everything is configured well.
            2. Download the remote code (ZIP), unpack it in the specified path and update the apps list
            3. If the button "Download & update app" was triggered we will also do an actual app update for the db.
               Notice that this is only for people who really know what they do!
        """
        self._validate_configuration_and_access()
        self._download_remote_app_code()
        if self.env.context.get('update_app'):
            # TODO: should we trigger a wizard asking for double verification here?
            post_install_action = self._update_app_code()
            return post_install_action

    def _check_kanban_update(self, kanban_view_details):
        """
            Checks if the database version of our Kanban view is outdated or not. If it is we store the new
            (remote) version in our local database.

            Args:
                kanban_view_details (dictionary): dictionary with the remote Kanban XML & the version
            Returns:
                None
        """
        remote_kanban_version = float(kanban_view_details.get('version'))
        remote_kanban_view = kanban_view_details.get('kanban')

        # We will only keep one record in the db!
        app_manager_view = self.env['app.manager'].sudo().search([], limit=1)

        # Updated remote version - saving in our database for rendering!
        if app_manager_view.kanban_version < remote_kanban_version:
            app_manager_view.write({
                'xml_kanban': remote_kanban_view,
                'kanban_version': remote_kanban_version
             })

    def _prepare_local_app_details(self):
        """
            Gets all locally installed modules and stores them into a dictionary along with the Odoo version.
            This is used to compare local app details with remote details.

            returns:
            app_dictionary (dictionary): dict with the most important details of the installed apps along with the db
            it's version
        """
        installed_modules = self.env['ir.module.module'].search_read(
            [('state', '=', 'installed')], ["id", "name", "installed_version", "latest_version", "state", "author"]
        )

        # Don't worry we are not going to do anything unethical with this. In fact, right now we do not do anything
        # with it. We're just including this for possible feature services related to your specific database.
        database_uuid = self.env['ir.config_parameter'].sudo().get_param('database.uuid')

        app_dictionary = json.dumps({
            'modules': installed_modules,
            'version': odoo.service.common.exp_version(),
            'database_uuid': database_uuid
        })

        return app_dictionary

    def check_external_app_updates(self):
        """
            Main function which will get all details about apps from The Odoo Store.
            1. Gets The Odoo Store URL
            2. Stores the details about installed apps on the customer database in JSON format
            3. Posts the data and gets back details about these apps from The Odoo Store server
               This is details such as the certification, if there is a remote update, security issues,  ...
            4. Stores the details in the local db for showing a visual UI to the end user about all apps
        """
        app_store_server_url = self.get_app_store_server()

        # Prepares all local app details and converts them into a JSON
        app_dictionary = self._prepare_local_app_details()

        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        response = requests.post(
            url=app_store_server_url + '/api/get_apps_to_update', data=app_dictionary, headers=headers
        )

        # Failsafe for a down server, maintenance, ... Either way The Odoo Store API is not reachable.
        if response.status_code != 200:
            _logger.critical("We could not connect to '%s'. Falling back to old view/values." % app_store_server_url)
            return self.env.ref('app_manager.open_store_module_action').read()[0]
        else:
            _logger.info(
                "We could connect to the API's from '%s'. Fetching possible view updates & app details." %
                app_store_server_url
            )

        # We should have a good JSON load now - let's parse it
        json_response = json.loads(response.text).get('result')

        # Return the actual view (which now has updated database values for our apps & the (possible) new Kanban view

        # Failsafe in case we do not get any good response
        # or because we do not yet have an XML architecture tested/supported for this Odoo version.
        if not json_response or json_response.get('version_not_supported'):
            # For sure no new view or changes - let's fall back to our already stored view.
            return self.env.ref('app_manager.open_store_module_action').read()[0]

        # Checks if our remote server has a new XML update for the Kanban design or not
        self._check_kanban_update(json_response.get('views'))

        apps_to_update = json_response.get('modules')
        to_update_apps = []
        if apps_to_update:
            for app_to_update in apps_to_update:
                app = self.browse(int(app_to_update.get('id')))
                app.update({
                    'store_app': True,
                    'store_is_certified': app_to_update.get('is_certified'),
                    'store_is_free': True if app_to_update.get('app_type') == 'Free' else False,
                    'store_url': app_to_update.get('store_url'),
                    'store_download_url': app_to_update.get('download_url'),
                    'store_version': app_to_update.get('remote_version'),
                    'store_update_available': True if app_to_update.get('remote_version') != app.installed_version else False,
                    'store_has_security_issue': True if app_to_update.get('has_security_issue') else False,
                })
                to_update_apps += app
                self.env['ir.module.module'].write(to_update_apps)

        # We (might have had) a view update - let's call the action.
        # This has to be done after our remote sync so we 'get' the possible new remote view.
        action = self.env.ref('app_manager.open_store_module_action').read()[0]
        return action

    def get_updatable_apps(self):
        """
            Fetches details about all apps that have updates available on The Odoo Store and passes the details
            along as a list. This is used for the email template.
        """
        module_values = []
        # There is a reason why we search apps & then convert the values we need in a dictionary!
        # Odoo is unable to fetch fields on the base model in a new module within Jinja2. This is the easiest workaround
        modules = self.search([
            ('store_update_available', '=', True)
        ])

        for module in modules:
            module_values.append({
                'name': module.shortdesc,
                'technical_name': module.name,
                'app_icon': module.icon,
                'installed_version': module.installed_version,
                'store_version': module.store_version,
                'store_url': module.store_url,
                'store_has_security_issue': module.store_has_security_issue
            })
        return module_values

    def send_app_update_email(self):
        """
            Automatically sends an e-mail to the user which is configured under AppManager > Settings.
        """
        # Check if this database should send an e-mail or not
        notify_by_email = self.env['ir.config_parameter'].sudo().get_param('app_manager.receive_app_update_mails')

        if notify_by_email:
            # Get all the details that we need for sending out the email
            app_update_email_template = self.env['ir.config_parameter'].sudo().get_param(
                'app_manager.app_update_mail_template_id')
            user_id = self.env['ir.config_parameter'].sudo().get_param('app_manager.app_update_user_id')
            user_email = self.env['res.users'].browse(int(user_id)).partner_id.email
            # Just a placeholder for generating an unique id
            app_manager = self.env['app.manager'].search([], limit=1).id

            mail_template = self.env['mail.template'].sudo().browse(int(app_update_email_template))
            mail_template['email_to'] = user_email
            mail_template.send_mail(app_manager, force_send=True)
