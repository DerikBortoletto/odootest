import logging
import datetime
import json
from datetime import timezone, timedelta
from odoo import api, fields, models, _

logger = logging.getLogger(__name__)


class CrmLead(models.Model):
    _inherit = "crm.lead"

    hubspot_id = fields.Char('Hubspot Id', store=True, readonly=True, copy=False)
    hubspot_instance_id = fields.Many2one('hubspot.instance', 'Hubspot Instance Name', help="Hubspot Instance Name", readonly=True, copy=False)
    hubspot_deal_stage = fields.Char('Hubspot Deal Stage')
    hubspot_deal_type = fields.Char('Hubspot Deal Type')
    partner_ids = fields.Many2many('res.partner', 'crm_lead_res_partner_rel', 'lead_id', 'partner_id', 'Partners')

    def write(self, vals):
        '''Update Contact or company details in hubspot on change of details in odoo'''
        res = super(CrmLead, self).write(vals)
        for record in self:
            if vals.get('stage_id'):
                stage_id = self.env['crm.stage'].sudo().search([('id', '=', vals.get('stage_id'))])
                record.hubspot_deal_stage = stage_id.name
            # Hubspot Information
            if record.hubspot_instance_id.hubspot_app_key and record.hubspot_instance_id.name:
                if not self.env.context.get('from_hubspot', False):
                    deals_field_mapping = self.env['deals.field.mapping'].search([('hubspot_instance_id', '=', record.hubspot_instance_id.id)])
                    try:
                        if record.hubspot_id and record.hubspot_instance_id and record.type == 'lead':
                            instance = record.hubspot_instance_id
                        if instance:
                            if instance.active and instance.hubspot_sync_deals and instance.hubspot_is_export_deals and record.type == 'lead':
                                record.UpdateDealsInHubspot(instance)
                                if len(deals_field_mapping):
                                    record.UpdateDealsInHubspotFieldMapping(deals_field_mapping, instance)
                    except Exception as e_log:
                        error_message = 'Error while updating crm leads from odoo %d \n\n Odoo vals: %s\n Hubspot response %s' % (
                            record.id, str(vals), str(e_log))
                        self.env['hubspot.logger'].create_log_message('Export Deals', error_message)
                        logger.exception("Exception updating crm leads  :\n" + str(e_log))
                        instance._raise_user_error(e_log)

        return res

    def unlink(self):
        '''Delete contact in hubspot on delete of contact or company in odoo'''
        for record in self:
            if record.hubspot_instance_id.hubspot_sync_deals and record.hubspot_instance_id and record.hubspot_instance_id.active:
                record.deleteFromHubspot(record.hubspot_instance_id)
                self._cr.commit()
        return super(CrmLead, self).unlink()

    def deleteFromHubspot(self, hubspot_instance_id):
        logger.info('>>> Delete CRM Lead from hubspot')
        try:
            for each in self:
                response = hubspot_instance_id._send_delete_request('/deals/v1/deal/' + str(each.hubspot_id))
        except Exception as e:
            error_message = 'Error while deleting deals in hubspot \nHubspot response %s' % (str(e))
            self.env['hubspot.logger'].create_log_message('Delete Deals', error_message)
            logger.exception(">>> Error in deleted Deals From Hubspot\n" + str(e))
            hubspot_instance_id._raise_user_error(e)
        logger.info('>>> Completed Delete CRM Lead from hubspot')

    def convert_time_to_unix_timestamp(self, deadline_date):
        '''
            This method converts date to unix timestamp
            @param : deadline_date(datetime.date)
            @returns : timestamp in millisecound(str)
        '''
        date_deadline = fields.Datetime.from_string(deadline_date)
        timestamp = date_deadline.replace(tzinfo=timezone.utc)
        generic_epoch = datetime.datetime(1970, 1, 1, 0, 0, 0)
        generic_epoch = generic_epoch.replace(tzinfo=timezone.utc)
        timestamp = (timestamp - generic_epoch).total_seconds()
        return int(timestamp * 1000)

    @api.model
    def _cron_import_deals_from_hubspot(self):
        hubspot_instance_obj = self.env['hubspot.instance'].search([('active', '=', True), ('hubspot_is_import_deals', '=', True), ('hubspot_sync_deals', '=', True)])
        for hubspot_instance in hubspot_instance_obj:
            self.import_deals_from_hubspot(hubspot_instance)
        # crow_id = self.env.ref('hubspot.import_tickets_pipelines_to_hubspot').sudo()
        # if bool(crow_id) and not crow_id.active:
        #     crow_id.nextcall = fields.Datetime.now() + timedelta(minutes=5)
        #     crow_id.active = True

    def import_deals_from_hubspot(self, hubspot_instance):
        modifiedDateForDeals = float(hubspot_instance.modifiedDateForDeals or 0)
        all_deals = float(hubspot_instance.all_deals or 0)
        if hubspot_instance.hubspot_sync_deals and not all_deals and hubspot_instance.hubspot_is_import_deals and hubspot_instance.active:  # This will execute only first time to sync all deals
            logger.info('>>> Getting All deals from hubspot')
            try:
                has_more = True
                offset = 0
                while has_more:
                    deals_ids = []
                    record_limit = 1
                    response_all_deals = hubspot_instance._send_get_request('/deals/v1/deal/paged?offset={}&limit={}'.format(str(offset),str(record_limit)))
                    json_response_all_deals = json.loads(response_all_deals)
                    has_more = json_response_all_deals.get('hasMore')
                    offset = json_response_all_deals.get('offset')
                    for deals_id in json_response_all_deals['deals']:
                        if deals_id['dealId']:
                            deals_ids.append(deals_id['dealId'])
                    if deals_ids:
                        self.get_deals_details_and_create(deals_ids, hubspot_instance)
                hubspot_instance.all_deals = True
                message = 'Completed Getting All deals from hubspot'
                self.env['hubspot.logger'].create_log_message('Import Deals', message)
                logger.info('>>> Completed Getting All deals from hubspot')
            except Exception as e:
                error_message = 'Error while getting deals in odoo \nHubspot response %s' % (str(e))
                self.env['hubspot.logger'].create_log_message('Import Deals', error_message)
                logger.exception(">>> Error in Getting All Deals From Hubspot\n" + error_message)
                hubspot_instance._raise_user_error(e)

        else:
            if hubspot_instance.hubspot_sync_deals and hubspot_instance.hubspot_is_import_deals and hubspot_instance.active:  # This will execute only first time to sync all deals

                logger.info('>>> Getting modified deals from hubspot')
                try:
                    has_more = True
                    offset = 0
                    while has_more:
                        updated_deals_ids = []
                        record_limit = 90
                        response_all_deals = hubspot_instance._send_get_request('/deals/v1/deal/recent/modified?offset={}&limit={}'.format(str(offset),str(record_limit)))
                        recent_update_deals_json_response = json.loads(response_all_deals)

                        record_limit += 1
                        offset = recent_update_deals_json_response.get('offset')
                        has_more = recent_update_deals_json_response.get('hasMore')
                        for dealId in recent_update_deals_json_response.get('results'):
                            if (int(dealId['properties']['hs_lastmodifieddate']['value'])) <= int(modifiedDateForDeals) or hubspot_instance.force_rewrite:
                                break  # Skip Not recently updated deals
                            elif (int(recent_update_deals_json_response.get('results')[0]['properties']['hs_lastmodifieddate']['value'])) > int(modifiedDateForDeals):
                                updated_deals_ids.append(dealId['dealId'])
                        updated_deals_ids.reverse()
                        if hubspot_instance.hubspot_sync_deals and hubspot_instance.active and updated_deals_ids and hubspot_instance.hubspot_is_import_deals:
                            self.get_deals_details_and_create(updated_deals_ids, hubspot_instance)
                        else:
                            break
                        new_modifiedDateForDeals = recent_update_deals_json_response['results'][0]['properties']['hs_lastmodifieddate']['value']
                        hubspot_instance.modifiedDateForDeals = new_modifiedDateForDeals
                        hubspot_instance.all_deals = True

                    message = 'Completed Getting All deals from hubspot'
                    self.env['hubspot.logger'].create_log_message('Import Deals', message)
                    logger.info('>>> Completed Getting modified deals from hubspot')
                except Exception as e:
                    error_message = 'Error while getting deals in odoo \nHubspot response %s' % (str(e))
                    self.env['hubspot.logger'].create_log_message('Import Deals', error_message)
                    logger.exception(">>> Error in getModifiedDealsFromHubspot\n" + str(e))
                    hubspot_instance._raise_user_error(e)

    def get_deals_details_and_create(self, deals_ids, hubspot_instance):
        for deals_id in deals_ids:
            deals_info = []
            try:
                get_deals_by_id_response = hubspot_instance._send_get_request('/deals/v1/deal/{}'.format(str(deals_id)))
                deals_profile = json.loads(get_deals_by_id_response)
                deals_info.append(deals_profile)
                logger.debug('>>> Get deals details')
                self.createNewDealsInOdoo(deals_info, hubspot_instance)
                self._cr.commit()
                deals_field_mapping = self.env['deals.field.mapping'].search([('hubspot_instance_id', '=', hubspot_instance.id)])
                if len(deals_field_mapping):
                    self.createNewDealsInOdooFieldMapping(deals_info, hubspot_instance)
            except Exception as e:
                error_message = 'Error while importing hubspot deals in odoo Id: %s\n Hubspot response %s' % (
                    deals_id, str(e))
                self.env['hubspot.logger'].create_log_message('Import Deals', error_message)
                logger.exception(">>> Exception In getting deals info from Hubspot : \n" + error_message)
                hubspot_instance._raise_user_error(e)


    @api.model
    def createNewDealsInOdoo(self, deals_dict, hubspot_instance):
        try:
            logger.info('>>> Create New Deals')
            newdealsModifiedDate = 10000000.0
            res_partner_obj = self.env['res.partner']
            for deals_dict_details in deals_dict:
                if 'hs_lastmodifieddate' in deals_dict_details['properties']:
                    if deals_dict_details['properties']['hs_lastmodifieddate']['value']:
                        newdealsModifiedDate = int(deals_dict_details['properties']['hs_lastmodifieddate']['value'])
                vals = {}
                if deals_dict_details['dealId']:
                    vals['hubspot_id'] = deals_dict_details['dealId']
                if 'dealname' in deals_dict_details['properties']:
                    vals['name'] = deals_dict_details['properties']['dealname']['value']
                if 'closedate' in deals_dict_details['properties']:
                    closedate = deals_dict_details['properties']['closedate']['timestamp']
                    vals['date_closed'] = self.env['mail.activity'].convert_epoch_to_gmt_timestamp(closedate)
                if 'dealstage' in deals_dict_details['properties']:
                    if deals_dict_details['properties']['dealstage']['value'] == 'appointmentscheduled':
                        vals['hubspot_deal_stage'] = 'Appointment scheduled'
                    if deals_dict_details['properties']['dealstage']['value'] == 'qualifiedtobuy':
                        vals['hubspot_deal_stage'] = 'Qualified to buy'
                    if deals_dict_details['properties']['dealstage']['value'] == 'presentationscheduled':
                        vals['hubspot_deal_stage'] = 'Presentation scheduled'
                    if deals_dict_details['properties']['dealstage']['value'] == 'decisionmakerboughtin':
                        vals['hubspot_deal_stage'] = 'Decision maker bought-In'
                    if deals_dict_details['properties']['dealstage']['value'] == 'contractsent':
                        vals['hubspot_deal_stage'] = 'Contract sent'
                    if deals_dict_details['properties']['dealstage']['value'] == 'closedwon':
                        vals['hubspot_deal_stage'] = 'Closed won'
                if 'dealtype' in deals_dict_details['properties']:
                    if deals_dict_details['properties']['dealtype']['value'] == 'newbusiness':
                        vals['hubspot_deal_type'] = 'New Business'
                    if deals_dict_details['properties']['dealtype']['value'] == 'existingbusiness':
                        vals['hubspot_deal_type'] = 'Existing Business'
                if 'hubspot_owner_id' in deals_dict_details['properties'] and deals_dict_details['properties'].get('hubspot_owner_id').get('value'):
                    user_id = self.env['res.users'].search(
                        [('hubspot_uid', '=', deals_dict_details['properties']['hubspot_owner_id']['value']), ('hubspot_instance_id', '=', hubspot_instance.id)], limit=1)
                    if not user_id:
                        get_user = self.env['res.users'].getOwnerDetailsFromHubspot(deals_dict_details['properties']['hubspot_owner_id']['value'], hubspot_instance)
                        if get_user:
                            vals['user_id'] = get_user.id
                    else:
                        vals['user_id'] = user_id.id
                if 'amount' in deals_dict_details['properties']:
                    vals['expected_revenue'] = deals_dict_details['properties']['amount']['value']

                partner_list = []
                if 'associations' in deals_dict_details:
                    if deals_dict_details['associations']['associatedVids'] and hubspot_instance.hubspot_is_import_contacts:
                        contact_ids = deals_dict_details['associations']['associatedVids']
                        partner_id = res_partner_obj.sudo().search([('hubspot_id', '=', str(contact_ids[0])), ('hubspot_instance_id', '=', hubspot_instance.id)], limit=1)
                        if partner_id:
                            vals['partner_id'] = partner_id.id
                        else:
                            res_partner_ids = res_partner_obj.get_contact_details_and_create([contact_ids[0]], hubspot_instance)
                            for res_partner_id in res_partner_ids:
                                partner_id = res_partner_obj.sudo().search([('hubspot_id', '=', res_partner_id)], limit=1)
                                if partner_id:
                                    vals['partner_id'] = partner_id.id
                        for contact_id in deals_dict_details['associations']['associatedVids']:
                            partner_id = self.env['res.partner'].sudo().search(
                                [('hubspot_id', '=', contact_id), ('is_company', '=', False), ('hubspot_instance_id', '=', hubspot_instance.id)])
                            if partner_id:
                                partner_list.append(partner_id.id)
                            else:
                                if hubspot_instance.hubspot_sync_contacts and hubspot_instance.hubspot_is_import_contacts:
                                    partner_ids = self.env['res.partner'].get_contact_details_and_create([contact_id], hubspot_instance)
                                    partner_list += partner_ids

                    elif deals_dict_details['associations']['associatedCompanyIds'] and hubspot_instance.hubspot_is_import_company:
                        company_id = self.env['res.partner'].sudo().search(
                            [('hubspot_id', '=', str(deals_dict_details['associations']['associatedCompanyIds'][0])), ('hubspot_instance_id', '=', hubspot_instance.id)], limit=1)
                        if company_id:
                            vals['partner_id'] = company_id.id

                        else:
                            res_partner_ids = res_partner_obj.get_company_details_and_create([deals_dict_details['associations']['associatedCompanyIds'][0]], hubspot_instance)
                            for res_partner_id in res_partner_ids:
                                company_id = res_partner_obj.sudo().search([('hubspot_id', '=', res_partner_id.id)], limit=1)
                                if company_id:
                                    vals['partner_id'] = company_id.id
                    for company_id in deals_dict_details['associations']['associatedCompanyIds']:
                        company_partner_id = self.env['res.partner'].sudo().search([('hubspot_id', '=', company_id), ('is_company', '=', True), ('hubspot_instance_id', '=', hubspot_instance.id)])
                        if company_partner_id:
                            partner_list += company_partner_id.ids
                        else:
                            if hubspot_instance.hubspot_sync_companies and hubspot_instance.hubspot_is_import_company:
                                company_partner_id = self.env['res.partner'].get_company_details_and_create([company_id], hubspot_instance)
                                if bool(company_partner_id):
                                    partner_list.append(company_partner_id.id)
                if len(partner_list) > 0:
                    vals['partner_ids'] = [(6, 0, partner_list)]
                vals['type'] = 'lead'
                crm_lead_id = self.env['crm.lead'].sudo().search(
                    ['|', ('active', '=', True), ('active', '=', False), ('hubspot_id', '=', str(deals_dict_details['dealId'])), ('hubspot_instance_id', '=', hubspot_instance.id),
                     ('type', '=', 'lead')], limit=1)
                if crm_lead_id:
                    odoo_modifiedDate = self.convert_time_to_unix_timestamp(crm_lead_id.write_date)
                    if int(newdealsModifiedDate) > int(odoo_modifiedDate):
                        crm_lead_id.with_context({'from_hubspot': True}).write(vals)
                        self._cr.commit()
                        hubspot_instance.modifiedDateForDeals = newdealsModifiedDate
                        logger.debug(">>> Write into Existing Odoo Deals " + str(crm_lead_id.hubspot_id))
                else:
                    if 'name' in vals:
                        crm_lead_exists = self.env['crm.lead'].sudo().search(
                            ['|', ('active', '=', True), ('active', '=', False), ('name', '=', vals['name']), ('type', '=', 'lead'),
                             ('hubspot_id', '=', False), ('hubspot_instance_id', '=', False)], limit=1)
                        if crm_lead_exists:
                            vals['hubspot_instance_id'] = hubspot_instance.id
                            crm_lead_exists.with_context({'from_hubspot': True}).write(vals)
                            logger.debug(">>> Write into Existing Odoo Deals name " + str(crm_lead_exists.hubspot_id))
                            hubspot_instance.modifiedDateForDeals = newdealsModifiedDate
                        else:
                            vals['hubspot_instance_id'] = hubspot_instance.id
                            crm_lead_id = self.with_context({'from_hubspot': True}).create(vals)
                            hubspot_instance.modifiedDateForDeals = newdealsModifiedDate
                            logger.info(">>> Created New Deals Into Odoo " + str(crm_lead_id.id))
        except Exception as e:
            error_message = 'Error while creating hubspot deals in odoo vals: %s\n Hubspot response %s' % (
                deals_dict, str(e))
            self.env['hubspot.logger'].create_log_message('Import Deals', error_message)
            logger.exception(">>> Exception in Creating New Deals in Odoo :\n" + error_message)
            hubspot_instance._raise_user_error(e)

    @api.model
    def createNewDealsInOdooFieldMapping(self, deals_info, hubspot_instance):
        deals_field_mapping = self.env['deals.field.mapping'].search([('hubspot_instance_id', '=', hubspot_instance.id)])
        vals = {}
        try:
            newDealsModifiedDate = 10000000.0
            for deals_info_dict in deals_info:
                for deals_field_mapping_id in deals_field_mapping:
                    if deals_field_mapping_id.hubspot_fields.technical_name in deals_info_dict['properties']:
                        if 'lastmodifieddate' in deals_info_dict['properties']:
                            if deals_info_dict['properties']['lastmodifieddate']['value']:
                                newDealsModifiedDate = int(deals_info_dict['properties']['lastmodifieddate']['value'])
                        if deals_field_mapping_id.hubspot_fields.field_type == 'date':
                            vals[deals_field_mapping_id.odoo_fields.name] = self.env['mail.activity'].convert_epoch_to_gmt_timestamp(
                                deals_info_dict['properties'][deals_field_mapping_id.hubspot_fields.technical_name]['timestamp'])
                        else:
                            vals[deals_field_mapping_id.odoo_fields.name] = deals_info_dict['properties'][deals_field_mapping_id.hubspot_fields.technical_name]['value']
                vals['type'] = 'lead'
                lead_id = self.search(
                    ['|', ('active', '=', True), ('active', '=', False), ('hubspot_id', '=', str(deals_info_dict['dealId'])), ('hubspot_instance_id', '=', hubspot_instance.id),
                     ('type', '=', 'lead')], limit=1)
                if lead_id and vals:
                    odoo_modifiedDate = self.convert_time_to_unix_timestamp(lead_id.write_date)
                    vals['hubspot_instance_id'] = hubspot_instance.id
                    lead_id.with_context({'from_hubspot': True}).write(vals)
                    logger.debug(">>> Write into Existing Odoo deals " + str(lead_id.hubspot_id))
                    self._cr.commit()
                    return lead_id
                else:
                    deals_id = self.with_context({'from_hubspot': True}).create(vals)
                    hubspot_instance.modifiedDateForDeals = newDealsModifiedDate
                    logger.debug(">>> Created New Deals Into Odoo " + str(deals_id.id))
                    self._cr.commit()
                    return deals_id

        except Exception as e:
            error_message = 'Error while creating hubspot deals in odoo vals using field mapping: %s\n Hubspot response %s' % (
                deals_info, str(e))
            self.env['hubspot.logger'].create_log_message('Import Deals', error_message)
            logger.exception(">>> Exception in Creating New Deals in Odoo :\n" + error_message)
            hubspot_instance._raise_user_error(e)

    @api.model
    def _cron_export_deals_to_hubspot(self):
        hubspot_instance_obj = self.env['hubspot.instance'].search([('active', '=', True), ('hubspot_is_export_deals', '=', True), ('hubspot_sync_deals', '=', True)])
        for hubspot_instance in hubspot_instance_obj:
            self.export_deals_to_hubspot(hubspot_instance)

    @api.model
    def export_deals_to_hubspot(self, hubspot_instance):
        # Hubspot Information

        crm_lead_ids = self.env['crm.lead'].search([('hubspot_id', '=', False), ('type', '=', 'lead')])
        if hubspot_instance.default_instance and hubspot_instance.active and hubspot_instance.hubspot_sync_deals and hubspot_instance.hubspot_is_export_deals:
            for lead_id in crm_lead_ids:
                if not lead_id.hubspot_id:
                    lead_id.createNewDealsInHubspot(hubspot_instance)
                    deals_field_mapping = self.env['deals.field.mapping'].search([('hubspot_instance_id', '=', hubspot_instance.id)])
                    if len(deals_field_mapping):
                        lead_id.createNewDealsInHubspotFieldMapping(hubspot_instance, deals_field_mapping)

    def createNewDealsInHubspot(self, hubspot_instance):
        logger.info('>>> Creating new leads in hubspot')
        for eachNewDeal in self:
            if eachNewDeal.type == 'lead':
                # create hubspot dictionary
                associatedVids = []
                associatedCompanyIds = []
                properties = []
                if eachNewDeal.name:
                    properties.append({'name': 'dealname', 'value': eachNewDeal.name})
                if eachNewDeal.hubspot_deal_stage:
                    if eachNewDeal.hubspot_deal_stage == 'Appointment scheduled':
                        properties.append({'name': 'dealstage', 'value': 'appointmentscheduled'})
                    if eachNewDeal.hubspot_deal_stage == 'Qualified to buy':
                        properties.append({'name': 'dealstage', 'value': 'qualifiedtobuy'})
                    if eachNewDeal.hubspot_deal_stage == 'Presentation scheduled':
                        properties.append({'name': 'dealstage', 'value': 'presentationscheduled'})
                    if eachNewDeal.hubspot_deal_stage == 'Decision maker bought-In':
                        properties.append({'name': 'dealstage', 'value': 'decisionmakerboughtin'})
                    if eachNewDeal.hubspot_deal_stage == 'Contract sent':
                        properties.append({'name': 'dealstage', 'value': 'contractsent'})
                    if eachNewDeal.hubspot_deal_stage == 'Closed won':
                        properties.append({'name': 'dealstage', 'value': 'closedwon'})
                else:
                    properties.append({'name': 'dealstage', 'value': 'appointmentscheduled'})
                if eachNewDeal.hubspot_deal_type:
                    if eachNewDeal.hubspot_deal_type == 'New Business':
                        properties.append({'name': 'dealtype', 'value': 'newbusiness'})
                    if eachNewDeal.hubspot_deal_type == 'Existing Business':
                        properties.append({'name': 'dealtype', 'value': 'existingbusiness'})
                else:
                    properties.append({'name': 'dealtype', 'value': 'newbusiness'})

                if eachNewDeal.expected_revenue:
                    properties.append({'name': 'amount', 'value': eachNewDeal.expected_revenue})
                if eachNewDeal.partner_id:
                    if eachNewDeal.partner_id.hubspot_id:
                        if eachNewDeal.partner_id.is_company:
                            associatedCompanyIds.append(eachNewDeal.partner_id.hubspot_id)

                        elif not eachNewDeal.partner_id.is_company:
                            associatedVids.append(eachNewDeal.partner_id.hubspot_id)
                # user (Owner) sync
                if eachNewDeal.user_id:
                    if eachNewDeal.user_id.hubspot_uid:
                        properties.append({'name': 'hubspot_owner_id', 'value': eachNewDeal.user_id.hubspot_uid})

                if properties:
                    try:
                        # try:
                        if associatedVids:
                            vals = {"associations": {"associatedVids": associatedVids}, 'properties': properties}
                            response_create_deals = hubspot_instance._send_post_request('/deals/v1/deal/', vals)
                            json_response_create_deals = json.loads(response_create_deals)

                            eachNewDeal.with_context({'from_hubspot': True}).hubspot_id = json_response_create_deals['dealId']
                            eachNewDeal.hubspot_instance_id = hubspot_instance.id
                            eachNewDeal.hubspot_deal_type = 'New Business'
                            eachNewDeal.hubspot_deal_stage = 'Appointment scheduled'
                        elif associatedCompanyIds:
                            vals = {"associations": {"associatedCompanyIds": associatedCompanyIds}, 'properties': properties}
                            response_create_deals = hubspot_instance._send_post_request('/deals/v1/deal/', vals)
                            json_response_create_deals = json.loads(response_create_deals)
                            eachNewDeal.with_context({'from_hubspot': True}).hubspot_id = json_response_create_deals['dealId']
                            eachNewDeal.hubspot_instance_id = hubspot_instance.id
                            eachNewDeal.hubspot_deal_type = 'New Business'
                            eachNewDeal.hubspot_deal_stage = 'Appointment scheduled'
                        else:
                            response_create_deals = hubspot_instance._send_post_request('/deals/v1/deal/', ({'properties': properties}))
                            json_response_create_deals = json.loads(response_create_deals)
                            eachNewDeal.with_context({'from_hubspot': True}).hubspot_id = json_response_create_deals['dealId']
                            eachNewDeal.hubspot_instance_id = hubspot_instance.id
                            eachNewDeal.hubspot_deal_type = 'New Business'
                            eachNewDeal.hubspot_deal_stage = 'Appointment scheduled'
                    except Exception as e_log:
                        error_message = 'Error while exporting odoo deals %d \n\n Odoo vals: %s\n Hubspot response %s' % (eachNewDeal.id, str(properties), str(e_log))
                        self.env['hubspot.logger'].create_log_message('Export Deals', error_message)
                        logger.exception("Exception in Hubspot Connection  :\n" + str(e_log))
                        hubspot_instance._raise_user_error(e_log)

                    message = 'Exported deals successfully'
                    self.env['hubspot.logger'].create_log_message('Export deals', message)
                    logger.info('>>> Exported deals successfully...')

    def createNewDealsInHubspotFieldMapping(self, hubspot_instance, deals_field_mapping):
        properties = []
        odoo_field_list = []
        lead_list = []
        for deals_field_mapping_id in deals_field_mapping:
            if deals_field_mapping_id.odoo_fields.name and deals_field_mapping_id.hubspot_fields.technical_name:
                odoo_field_list.append(deals_field_mapping_id.odoo_fields.name)
                lead_read_obj = self.read()[0]
                if deals_field_mapping_id.odoo_fields.name in lead_read_obj.keys():
                    if lead_read_obj.values():
                        if lead_read_obj.get(deals_field_mapping_id.odoo_fields.name):
                            if deals_field_mapping_id.hubspot_fields.field_type == 'date':
                                format_date = self.convert_time_to_unix_timestamp(lead_read_obj.get(deals_field_mapping_id.odoo_fields.name))
                                properties.append({'name': deals_field_mapping_id.hubspot_fields.technical_name,
                                                   'value': format_date})
                            else:
                                properties.append(
                                    {'name': deals_field_mapping_id.hubspot_fields.technical_name, 'value': str(lead_read_obj.get(deals_field_mapping_id.odoo_fields.name))})
        if properties:
            try:
                if self.hubspot_id and self.hubspot_instance_id:
                    response_create_deals = hubspot_instance._send_put_request('/deals/v1/deal/' + str(self.hubspot_id), ({'properties': properties}))
                    json_response_create_deals = json.loads(response_create_deals)
                else:
                    response_create_deals = hubspot_instance.send_post_request('/deals/v1/deal/', ({'properties': properties}))
                    json_response_create_deals = json.loads(response_create_deals)
                    self.with_context(from_hubspot=True).hubspot_id = json_response_create_deals['dealId']
                    self.with_context(from_hubspot=True).hubspot_instance_id = hubspot_instance.id
            except Exception as e_log:
                error_message = 'Error while exporting odoo deals field mapping %d \n\n Odoo vals: %s\n Hubspot response %s' % (self.id, str(properties), str(e_log))
                self.env['hubspot.logger'].create_log_message('Export Deals', error_message)
                logger.exception(">>> Exception in Hubspot Connection:\n" + str(e_log))
                hubspot_instance._raise_user_error(e_log)


    def UpdateDealsInHubspot(self, hubspot_instance):
        logger.info('>>> Updating Deals in hubspot')
        for eachNewDeal in self:
            if eachNewDeal.type == 'lead':
                # create hubspot dictionary
                associatedVids = []
                associatedCompanyIds = []
                properties = []
                if eachNewDeal.name:
                    properties.append({'name': 'dealname', 'value': eachNewDeal.name})
                if eachNewDeal.hubspot_deal_stage:
                    if eachNewDeal.hubspot_deal_stage == 'Appointment scheduled':
                        properties.append({'name': 'dealstage', 'value': 'appointmentscheduled'})
                    if eachNewDeal.hubspot_deal_stage == 'Qualified to buy':
                        properties.append({'name': 'dealstage', 'value': 'qualifiedtobuy'})
                    if eachNewDeal.hubspot_deal_stage == 'Presentation scheduled':
                        properties.append({'name': 'dealstage', 'value': 'presentationscheduled'})
                    if eachNewDeal.hubspot_deal_stage == 'Decision maker bought-In':
                        properties.append({'name': 'dealstage', 'value': 'decisionmakerboughtin'})
                    if eachNewDeal.hubspot_deal_stage == 'Contract sent':
                        properties.append({'name': 'dealstage', 'value': 'contractsent'})
                    if eachNewDeal.hubspot_deal_stage == 'Closed won':
                        properties.append({'name': 'dealstage', 'value': 'closedwon'})
                else:
                    properties.append({'name': 'dealstage', 'value': 'appointmentscheduled'})
                if eachNewDeal.hubspot_deal_type:
                    if eachNewDeal.hubspot_deal_type == 'New Business':
                        properties.append({'name': 'dealtype', 'value': 'newbusiness'})
                    if eachNewDeal.hubspot_deal_type == 'Existing Business':
                        properties.append({'name': 'dealtype', 'value': 'existingbusiness'})
                else:
                    properties.append({'name': 'dealtype', 'value': 'newbusiness'})
                if eachNewDeal.expected_revenue:
                    properties.append({'name': 'amount', 'value': eachNewDeal.expected_revenue})
                if eachNewDeal.partner_id:
                    if eachNewDeal.partner_id.hubspot_id:
                        if eachNewDeal.partner_id.is_company:
                            associatedCompanyIds.append(eachNewDeal.partner_id.hubspot_id)
                        elif not eachNewDeal.partner_id.is_company:
                            associatedVids.append(eachNewDeal.partner_id.hubspot_id)
                # user (Owner) sync
                if eachNewDeal.user_id:
                    if not eachNewDeal.user_id.hubspot_uid:
                        logger.warning(">>> Odoo User Not Available In Hubspot")
                        self.env['res.users'].syncAllUsers(eachNewDeal.hubspot_instance_id)
                    if eachNewDeal.user_id.hubspot_uid:
                        properties.append({'name': 'hubspot_owner_id', 'value': eachNewDeal.user_id.hubspot_uid})
                else:
                    properties.append({'property': 'hubspot_owner_id', 'value': ''})
                properties_vals = {'properties': properties}
                if properties:
                    try:
                        if associatedVids:
                            vals = {"associations": {"associatedVids": associatedVids}, 'properties': properties}
                            response = hubspot_instance._send_put_request('/deals/v1/deal/' + str(eachNewDeal.hubspot_id), vals)
                            parsed_resp = json.loads(response)
                            eachNewDeal.with_context({'from_hubspot': True}).hubspot_id = parsed_resp['dealId']
                        elif associatedCompanyIds:
                            vals = {"associations": {"associatedCompanyIds": associatedCompanyIds}, 'properties': properties}
                            response = hubspot_instance._send_put_request('/deals/v1/deal/' + str(eachNewDeal.hubspot_id), vals)
                            parsed_resp = json.loads(response)
                            eachNewDeal.with_context({'from_hubspot': True}).hubspot_id = parsed_resp['dealId']
                        else:
                            response = hubspot_instance._send_put_request('/deals/v1/deal/' + str(eachNewDeal.hubspot_id), properties_vals)
                            parsed_resp = json.loads(response)
                            eachNewDeal.with_context({'from_hubspot': True}).hubspot_id = parsed_resp['dealId']
                    except Exception as e_log:
                        error_message = 'Error while exporting odoo deals %d \n\n Odoo vals: %s\n Hubspot response %s' % (eachNewDeal.id, str(properties), str(e_log))
                        self.env['hubspot.logger'].create_log_message('Export Deals', error_message)
                        logger.exception(">>> Exception in Hubspot Connection  :\n" + str(e_log))
                        hubspot_instance._raise_user_error(e_log)

        logger.info('>>> Completed Updating deals in hubspot')

    def UpdateDealsInHubspotFieldMapping(self, deals_field_mapping, hubspot_instance):
        properties = []
        for eachNewDeal in self:
            for deals_field_mapping_id in deals_field_mapping:
                if deals_field_mapping_id.odoo_fields.name and deals_field_mapping_id.hubspot_fields.technical_name:
                    lead_read_obj = self.read()[0]
                    if deals_field_mapping_id.odoo_fields.name in lead_read_obj.keys():
                        if lead_read_obj.values():
                            if lead_read_obj.get(deals_field_mapping_id.odoo_fields.name):
                                if deals_field_mapping_id.hubspot_fields.field_type == 'date':
                                    format_date = self.convert_time_to_unix_timestamp(lead_read_obj.get(deals_field_mapping_id.odoo_fields.name))
                                    properties.append(
                                        {'name': deals_field_mapping_id.hubspot_fields.technical_name,
                                         'value': format_date})
                                else:
                                    properties.append(
                                        {'name': deals_field_mapping_id.hubspot_fields.technical_name,
                                         'value': str(lead_read_obj.get(deals_field_mapping_id.odoo_fields.name))})
            if properties:
                try:
                    hubspot_instance._send_put_request('/deals/v1/deal/' + str(eachNewDeal.hubspot_id), ({'properties': properties}))
                    eachNewDeal.with_context({'from_hubspot': True})
                    logger.info('>>> Completed updating deals in hubspot with custom field mapping')
                except Exception as e_log:
                    error_message = 'Error while exporting odoo deals with field mapping %d \n\n Odoo vals: %s\n Hubspot response %s' % (
                    eachNewDeal.id, str(properties), str(e_log))
                    self.env['hubspot.logger'].create_log_message('Export Deals', error_message)
                    logger.exception(">>> Exception in Hubspot Connection  :\n" + str(e_log))
                    hubspot_instance._raise_user_error(e_log)

