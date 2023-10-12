import logging
import random
import json
from datetime import timedelta
from odoo import fields, models

from .hubspot import convert_time_to_unix_timestamp

logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    _inherit = "res.users"

    hubspot_id = fields.Char('Hubspot id', readonly=True, copy=False)
    hubspot_uid = fields.Char('Hubspot User id', readonly=True, copy=False)
    hubspot_instance_id = fields.Many2one('hubspot.instance', 'Hubspot Instance Name', help="Hubspot Instance Name", readonly=True, copy=False)

    def _cron_syncAllUsers(self):
        hubspot_instance_obj = self.env['hubspot.instance'].search([('active', '=', True)])
        for hubspot_instance in hubspot_instance_obj:
            self.syncAllUsers(hubspot_instance)
        # crow_id = self.env.ref('hubspot.import_contacts_to_hubspot').sudo()
        # if bool(crow_id) and not crow_id.active:
        #     crow_id.nextcall = fields.Datetime.now() + timedelta(minutes=5)
        #     crow_id.active = True

    def syncAllUsers(self, hubspot_instance):
        try:
            logger.info('>>> Getting All Users from hubspot')
            allUsers = self.search(['|', ('active', '=', True), ('active', '=', False), ('hubspot_uid', '!=', False), ('hubspot_id', '!=', False), ('hubspot_instance_id', '=', hubspot_instance.id), ('id', 'not in', [3, 1, 5, 4])])
            Userids = allUsers.read(['hubspot_uid'])
            UserHubspotIds = [each['hubspot_uid'] for each in Userids]
            response_get_all_users = hubspot_instance._send_get_request('/owners/v2/owners')
            json_response_all_contacts = json.loads(response_get_all_users)

            logger.info(">>> Owner response logger %s: " % json_response_all_contacts)
            for owner in json_response_all_contacts:
                try:
                    owner_id = str(owner.get('ownerId'))
                    user_id = str(owner.get('activeUserId'))
                    user_dict = {'hubspot_uid': owner_id, 'hubspot_id': user_id}
                    if owner.get('email'):
                        user_dict.update({'login': owner.get('email')})
                        user_dict.update({'email': owner.get('email')})
                    user_name = ''
                    if owner.get('firstName'):
                        user_name += owner.get('firstName') + ' '
                        # user_dict.update({'name': owner.get('firstName')})
                    if owner.get('lastName'):
                        user_name += owner.get('lastName')
                        # user_dict.update({'name': owner.get('lastName')})
                    user_dict['name'] = user_name
                    if not owner.get('firstName') and not owner.get('lastName'):
                        user_dict.update({'name': owner.get('email')})
                    hubspot_modifiedDate = owner.get('updatedAt')
                    hubspot_modifiedDate = owner.get('updatedAt')
                    search_user = self
                    if owner_id in UserHubspotIds:
                        search_user = self.search(['|', ('active', '=', True), ('active', '=', False), 
                                                        ('hubspot_uid', '=', owner_id), ('hubspot_instance_id', '=', hubspot_instance.id)], limit=1)
                        if bool(search_user):
                            odoo_modifiedDate = convert_time_to_unix_timestamp(search_user.write_date)
                            logger.debug(">>> Owner Is Available with hubspot id in odoo: " + str(search_user))
                            if int(hubspot_modifiedDate) > int(odoo_modifiedDate):
                                search_user.with_context({'from_hubspot': True}).write(user_dict)
                                search_user.write({'hubspot_instance_id':hubspot_instance.id})
                                self._cr.commit()
                    if not bool(search_user):
                        search_user = self.search(
                            ['|', ('active', '=', True), ('active', '=', False), ('login', '=', owner.get('email'))], limit=1)
                        if search_user:
                            logger.debug(">>> Found owner with email in odoo: " + str(search_user))
                            search_user.with_context({'from_hubspot': True}).write(user_dict)
                            search_user.with_context({'from_hubspot': True}).write({'hubspot_instance_id':hubspot_instance.id})
                            self._cr.commit()
                        else:
                            email_exists = self.search(['|', ('active', '=', True), ('active', '=', False), ('hubspot_instance_id', '=', hubspot_instance.id),
                                                        ('hubspot_uid', '=', owner.get('ownerId'))], limit=1)
                            if not email_exists and owner.get('email'):
                                user_id = self.with_context({'from_hubspot': True}).create(user_dict)
                                user_id.write({'hubspot_instance_id': hubspot_instance.id})
                                logger.debug(">>> Owner created in odoo : {}".format(user_id))
                                self._cr.commit()
                            else:
                                logger.debug(">>> Before formatting email_id owner dict logger %s: " % str(owner))
                                email_id = owner.get('email') + str(random.randint(0, 999))
                                logger.debug(">>> email_id logger %s: " % str(email_id))
                                user_dict.update({'login': email_id})
                                logger.debug(">>> In if not email_exists exists logger %s: " % user_dict)
                                user_id = self.with_context({'from_hubspot': True}).create(user_dict)
                                user_id.write({'hubspot_instance_id': hubspot_instance.id})
                                logger.debug(">>> Owner created in odoo : {}".format(user_id))
                                self._cr.commit()
                except Exception as ex:
                    error_message = 'Error while sync users in odoo vals: %s\n Hubspot response %s' % (owner, str(ex))
                    self.env['hubspot.logger'].create_log_message('Import Users', error_message)
                    logger.exception(">>> Exception in sync users in Odoo :\n" + error_message)
                    hubspot_instance._raise_user_error(ex)
                message = 'Done Syncing Users'
                self.env['hubspot.logger'].create_log_message('Import Users', message)
                logger.info('>>> Done Syncing Users')
        except Exception as ex:
            error_message = 'Error while getting users in odoo \nHubspot response %s' % (str(ex))
            self.env['hubspot.logger'].create_log_message('Import Users', error_message)
            logger.exception(">>> Error in getting users From Hubspot\n" + error_message)
            hubspot_instance._raise_user_error(ex)

    def getOwnerDetailsFromHubspot(self, owner_id, hubspot_instance):
        '''
        Args:
            @param owner_id: hubspot owner id used to update or add in user
        Returns:
            @return: return user if availble with same email or create new one
        '''
        logger.info('>>> Getting Owner Details from hubspot')
        
        # Hubspot Owner Information
        try:
            response_get_user_by_id = hubspot_instance._send_get_request('/owners/v2/owners/{}'.format(str(owner_id)))
            json_response_get_user_by_id = json.loads(response_get_user_by_id)
            res_user_id = self.createNewUserInOdoo(json_response_get_user_by_id, hubspot_instance)
            # self.syncAllUsers(hubspot_instance)
            # search_user = self.search(
            #     ['|', ('active', '=', True), ('active', '=', False), ('hubspot_uid', '=', owner_id), ('hubspot_instance_id', '=', hubspot_instance.id)])
            message = 'Created/updated user in odoo'
            self.env['hubspot.logger'].create_log_message('Import Users', message)
            logger.debug('>>> Created/updated user in odoo')
            return res_user_id
        except Exception as ex:
            error_message = 'Error while importing hubspot users in odoo Id: %s\n Hubspot response %s' % (owner_id, str(ex))
            self.env['hubspot.logger'].create_log_message('Import Users', error_message)
            logger.exception(">>> Could not get owner details from hubspot : %s " % ex)
            hubspot_instance._raise_user_error(ex)

        return False

    def createNewUserInOdoo(self, hubspot_dict, hubspot_instance):
        try:
            user_dict = {'hubspot_uid': hubspot_dict.get('ownerId'), 'hubspot_id': hubspot_dict.get('userId'),}
            if hubspot_dict.get('email'):
                user_dict.update({'login': hubspot_dict.get('email')})
                user_dict.update({'email': hubspot_dict.get('email')})
            user_name = ''
            if hubspot_dict.get('firstName'):
                user_name += hubspot_dict.get('firstName') + ' '
            if hubspot_dict.get('lastName'):
                user_name += hubspot_dict.get('lastName')
            user_dict['name'] = user_name
            if not hubspot_dict.get('firstName') and not hubspot_dict.get('lastName'):
                user_dict.update({'name': hubspot_dict.get('email')})
            res_user_id = self.search(['|', ('active', '=', True), ('active', '=', False), ('hubspot_uid', '=', str(hubspot_dict.get('ownerId'))), ('hubspot_instance_id', '=', hubspot_instance.id)], limit=1)
            hubspot_modifiedDate = hubspot_dict.get('updatedAt')
            if res_user_id:
                odoo_modifiedDate = convert_time_to_unix_timestamp(res_user_id.write_date)
                if int(hubspot_modifiedDate) > int(odoo_modifiedDate):
                    res_user_id.with_context({'from_hubspot': True}).write(user_dict)
                    return res_user_id
            else:
                if 'login' in user_dict or 'email' in user_dict:
                    user_id = self.search(['|', ('active', '=', True), ('active', '=', False), ('login', '=', hubspot_dict.get('email'))], limit=1)
                    if user_id:
                        user_id.with_context({'from_hubspot': True}).write(user_dict)
                        user_id.write({'hubspot_instance_id': hubspot_instance.id})
                        return user_id
                    else:
                        res_user_email_exists = self.search(['|', ('active', '=', True), ('active', '=', False), ('login', '=', hubspot_dict.get('email'))], limit=1)
                        if res_user_email_exists:
                            email_id = hubspot_dict.get('email') + str(random.randint(0, 999))
                            logger.debug(">>> email_id logger %s: " % str(email_id))
                            user_dict.update({'login': email_id, 'email': email_id})
                            logger.debug(">>> In if not email_exists exists logger7 %s: " % user_dict)
                            user_id = self.with_context({'from_hubspot': True}).create(user_dict)
                            user_id.write({'hubspot_instance_id': hubspot_instance.id})
                            logger.debug(">>> Owner created in odoo : {}".format(user_id))
                            self._cr.commit()
                            return user_id
                        else:
                            user_id = self.with_context({'from_hubspot': True}).create(user_dict)
                            user_id.with_context({'from_hubspot': True}).write({'hubspot_instance_id': hubspot_instance.id})
                            logger.debug("Owner updated in odoo : {}".format(user_id))
                            self._cr.commit()
        except Exception as ex:
            error_message = 'Error while creating hubspot deals in odoo vals: %s\n Hubspot response %s' % (hubspot_dict, str(ex))
            self.env['hubspot.logger'].create_log_message('Import Users', error_message)
            logger.exception(">>> Exception in Creating New Users in Odoo :\n" + error_message)
            hubspot_instance._raise_user_error(ex)








