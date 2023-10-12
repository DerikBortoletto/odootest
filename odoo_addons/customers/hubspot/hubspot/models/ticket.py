import logging
import datetime
from datetime import timedelta 
import time
import json
from datetime import timezone
from odoo import api, fields, models, _
from odoo.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT

logger = logging.getLogger(__name__)

HUBSPOT_DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%SZ'

class HelpdeskStage(models.Model):
    _inherit = 'helpdesk.stage'

    hubspot_id = fields.Char('Hubspot Id', store=True, readonly=True, copy=False)
    hubspot_instance_id = fields.Many2one('hubspot.instance', 'Hubspot Instance Name', help="Hubspot Instance Name", readonly=True, copy=False)

    def convert_epoch_to_gmt_timestamp(self, hubspot_date):
        modified_date = int(str(hubspot_date)[:10])
        formatted_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(modified_date))
        date_time_obj = datetime.datetime.strptime(formatted_time, '%Y-%m-%d %H:%M:%S')
        return date_time_obj

    def import_stage_from_hubspot(self, hubspot_instance, pipeline_id):
        logger.info('>>> Getting New and Modified ticket stages from hubspot')
        try:
            response_get_stages = hubspot_instance._send_get_request('/crm/v3/pipelines/tickets/{}/stages'.format(pipeline_id))
            json_stages_response = json.loads(response_get_stages)
            stage_ids = []
            for StageDetails in json_stages_response['results']:
                stage_id = self.search([('hubspot_id','=',StageDetails['id']),('hubspot_instance_id','=',hubspot_instance.id)],limit=1)
                if not bool(stage_id):
                    stage_ids.append(StageDetails['id'])
                else:
                    odoo_modifiedDate = stage_id.write_date
                    lastUpdated = self.convert_epoch_to_gmt_timestamp(StageDetails('updatedAt','1970-01-01T00:00:00Z'))
                    if odoo_modifiedDate < lastUpdated:
                        stage_ids.append(StageDetails['id'])
            self.get_stage_details_and_create(pipeline_id, stage_ids, hubspot_instance)
            message = 'Completed Getting All stages from hubspot'
            self.env['hubspot.logger'].create_log_message('Import Stages', message)
            logger.info('Completed Getting modified stages from hubspot')
        except Exception as e:
            error_message = 'Error while getting ticket stages in odoo, Hubspot response %s' % (str(e))
            self.env['hubspot.logger'].create_log_message('Import ticket stages', error_message)
            logger.exception(">>> Error in import_stage_from_hubspot, " + str(e))
            hubspot_instance._raise_user_error(e)

    def get_stage_details_and_create(self, pipeline_id, stage_ids, hubspot_instance):
        for stage_id in stage_ids:
            stage_info = []
            try:
                response_get_stage_by_id = hubspot_instance._send_get_request('/crm/v3/pipelines/tickets/{}/stages/{}'.format(str(pipeline_id),str(stage_id)))
                json_response_get_stage_by_id = json.loads(response_get_stage_by_id)
                logger.debug('>>> Get ticket stage %s details' % str(stage_id))
                stage_info.append(json_response_get_stage_by_id)
                self.CreateUpdateStageInOdoo(pipeline_id, stage_info, hubspot_instance)
                self._cr.commit()
            except Exception as e:
                error_message = 'Error while importing hubspot meeting in odoo Id: %s, Hubspot response %s' % (stage_id, str(e))
                self.env['hubspot.logger'].create_log_message('Import Ticket Stage', error_message)
                logger.exception(">>> Exception In getting stage ticket info from Hubspot : " + error_message)
                hubspot_instance._raise_user_error(e)
    
    def CreateUpdateStageInOdoo(self, pipeline_id, stage_dict, hubspot_instance):
        team = self.env['helpdesk.team']
        try:
            for stage_details in stage_dict:
                hubspot_id = stage_details['id']
                vals = {
                    'name': stage_details.get('label', 'new'),
                    'is_close': False,
                    'hubspot_id': hubspot_id,
                }
                if bool(pipeline_id):
                    team_ids = team.search(['|',('active','=',True),('active','=',False),('hubspot_id','=',pipeline_id),('hubspot_instance_id','=',hubspot_instance.id)])
                    if bool(team_ids):
                        vals['team_ids'] = []
                        for team_id in team_ids:
                            vals['team_ids'] += [(4,team_id.id,)]
                if bool(stage_details.get('displayOrder')):
                    try:
                        vals['sequence'] = int(stage_details['displayOrder'])
                    except:
                        pass
                if bool(stage_details.get('metadata')) and stage_details['metadata'].get('ticketState') and stage_details['metadata']['isClosed'] == 'true':
                    vals['is_close'] = True
                stage_id = self.sudo().search([('hubspot_id','=',hubspot_id),('hubspot_instance_id','=',hubspot_instance.id)])
                if bool(stage_id):
                    stage_id.sudo().with_context({'from_hubspot': True}).write(vals)
                    logger.debug('>>> Write into existing Odoo ticket stage id %s' % str(stage_id.ids))
                else:
                    vals['hubspot_instance_id'] = hubspot_instance.id
                    stage_id = self.sudo().with_context({'from_hubspot': True}).create(vals)
                    logger.info(">>> Created New ticket stage Into Odoo %s" % str(stage_id.id))
                self._cr.commit()
        except Exception as e:
            error_message = 'Error while creating hubspot ticket stage in odoo vals: %s, Hubspot response %s' % (stage_details, str(e))
            self.env['hubspot.logger'].create_log_message('Import ticket stage', error_message)
            logger.exception(">>> Exception in Creating New ticket stage in Odoo : " + error_message)
            hubspot_instance._raise_user_error(e)

class HelpdeskTeam(models.Model):
    _inherit = "helpdesk.team"

    hubspot_id = fields.Char('Hubspot Id', store=True, readonly=True, copy=False)
    hubspot_instance_id = fields.Many2one('hubspot.instance', 'Hubspot Instance Name', help="Hubspot Instance Name", readonly=True, copy=False)

    @api.model
    def _cron_import_pipelines_from_hubspot(self):
        hubspot_instance_obj = self.env['hubspot.instance'].search([('active', '=', True), ('hubspot_is_import_ticket_pipeline', '=', True), ('hubspot_sync_ticket_pipeline', '=', True)])
        for hubspot_instance in hubspot_instance_obj:
            self.import_pipelines_from_hubspot(hubspot_instance)
        # crow_id = self.env.ref('hubspot.import_tickets_to_hubspot').sudo()
        # if bool(crow_id) and not crow_id.active:
        #     logger.debug('>>> Active Crow Import Tickets From Hubspot')
        #     crow_id.nextcall = fields.Datetime.now() + timedelta(minutes=5)
        #     crow_id.active = True
        
    def import_pipelines_from_hubspot(self, hubspot_instance):
        logger.info('>>> Getting New and Modified pipelines (teams) from hubspot')
        try:
            response_get_pipelines = hubspot_instance._send_get_request('/crm/v3/pipelines/tickets')
            json_pipelines_response = json.loads(response_get_pipelines)
            pipelines_ids = []
            for pipelineDetails in json_pipelines_response['results']:
                pipeline_id = self.search(['|',('active','=',True),('active','=',False),('hubspot_id','=',pipelineDetails['id']),('hubspot_instance_id','=',hubspot_instance.id)],limit=1)
                if not bool(pipeline_id):
                    pipelines_ids.append(pipelineDetails['id'])
                else:
                    odoo_modifiedDate = pipeline_id.write_date
                    lastUpdated = self.convert_epoch_to_gmt_timestamp(pipelineDetails('updatedAt','1970-01-01T00:00:00Z'))
                    if odoo_modifiedDate < lastUpdated:
                        pipelines_ids.append(pipelineDetails['id'])
            self.get_pipeline_details_and_create(pipelines_ids, hubspot_instance)
            message = 'Completed Getting All Pipelines from hubspot'
            self.env['hubspot.logger'].create_log_message('Import Stages', message)
            logger.debug('>>> Completed Getting modified Pipelines from hubspot')
        except Exception as e:
            error_message = 'Error while getting ticket stages in odoo, Hubspot response %s' % (str(e))
            self.env['hubspot.logger'].create_log_message('Import Pipelines', error_message)
            logger.exception(">>> Error in _cron_import_pipelines_from_hubspot, " + str(e))
            hubspot_instance._raise_user_error(e)
    
    def get_pipeline_details_and_create(self, pipeline_ids, hubspot_instance):
        stage = self.env['helpdesk.stage']
        for pipeline_id in pipeline_ids:
            logger.debug('>>> Get Ticket Pipeline %s details' % str(pipeline_id))
            pipeline_info = []
            try:
                response_get_pipeline_by_id = hubspot_instance._send_get_request('/crm/v3/pipelines/tickets/{}'.format(str(pipeline_id)))
                json_response_get_pipeline_by_id = json.loads(response_get_pipeline_by_id)
                pipeline_info.append(json_response_get_pipeline_by_id)
                self.createNewPipelineInOdoo(pipeline_info, hubspot_instance)
                stage.import_stage_from_hubspot(hubspot_instance, pipeline_id)
                self._cr.commit()
            except Exception as e:
                error_message = 'Error while importing hubspot ticket pipeline in odoo Id: %s, Hubspot response %s' % (pipeline_id, str(e))
                self.env['hubspot.logger'].create_log_message('Import Ticket Pipeline', error_message)
                logger.exception(">>> Exception In getting Ticket Pipeline info from Hubspot: " + error_message)
                hubspot_instance._raise_user_error(e)
    
    @api.model
    def createNewPipelineInOdoo(self, pipelines_dict, hubspot_instance):
        try:
            for pipeline_details in pipelines_dict:
                hubspot_id = pipeline_details['id']
                vals = {
                    'name': pipeline_details.get('label', 'new'),
                    'hubspot_id': hubspot_id,
                    'active': False if pipeline_details.get('archived', False) else True,
                }
                if bool(pipeline_details.get('displayOrder')):
                    try:
                        vals['sequence'] = int(pipeline_details['displayOrder'])
                    except:
                        pass
                team_id = self.sudo().search(['|',('active','=',True),('active','=',False),('hubspot_id','=',hubspot_id),('hubspot_instance_id','=',hubspot_instance.id)])
                if bool(team_id):
                    team_id.with_context({'from_hubspot': True}).write(vals)
                    self._cr.commit()
                    logger.debug('>>> Write into existing Odoo ticket stage id %s' % str(team_id.ids))
                else:
                    vals['hubspot_instance_id'] = hubspot_instance.id
                    team_id = self.with_context({'from_hubspot': True}).create(vals)
                    logger.info(">>> Created New ticket stage Into Odoo %s" % str(team_id.id))
        except Exception as e:
            error_message = 'Error while creating hubspot ticket stage in odoo vals: %s, Hubspot response %s' % (pipeline_details, str(e))
            self.env['hubspot.logger'].create_log_message('Import ticket stage', error_message)
            logger.exception(">>> Exception in Creating New ticket team in Odoo: " + error_message)
            hubspot_instance._raise_user_error(e)

class HelpdeskTicket(models.Model):
    _inherit = "helpdesk.ticket"

    hubspot_id = fields.Char('Hubspot Id', store=True, readonly=True, copy=False)
    hubspot_instance_id = fields.Many2one('hubspot.instance', 'Hubspot Instance Name', help="Hubspot Instance Name", readonly=True, copy=False)
    hubspot_response = fields.Text('Json response')

    def deleteFromHubspot(self, hubspot_instance_id):
        logger.info('>>> Delete Ticket from hubspot')
        try:
            for each in self:
                response = hubspot_instance_id._send_delete_request('/crm/v3/objects/tickets/' + str(each.hubspot_id))
        except Exception as e:
            error_message = '>>> Error while deleting tickets in hubspot, Hubspot response %s' % (str(e))
            self.env['hubspot.logger'].create_log_message('Delete Deals', error_message)
            logger.exception(">>> Error in deleted Deals From Hubspot, " + str(e))
            hubspot_instance_id._raise_user_error(e)
        logger.info('>>> Completed Delete Ticket from hubspot')

    def convet_hubspot_time_to_datetime(self,datetime_vl):
        dot = str(datetime_vl).find('.')
        if dot > -1:
            datetime_vl = datetime_vl[:dot]+'Z'
            res = datetime.datetime.strptime(datetime_vl, HUBSPOT_DATETIME_FORMAT)
        else:
            res = datetime.datetime.strptime(datetime_vl, HUBSPOT_DATETIME_FORMAT)
        return res

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
    def _cron_import_tickets_from_hubspot(self):
        hubspot_instance_obj = self.env['hubspot.instance'].search([('active', '=', True), ('hubspot_is_import_ticket', '=', True), ('hubspot_sync_ticket', '=', True)])
        for hubspot_instance in hubspot_instance_obj:
            self.import_tickets_from_hubspot(hubspot_instance)
                                  
        # crow_id = self.env.ref('hubspot.import_task_to_hubspot').sudo()
        # if bool(crow_id) and not crow_id.active:
        #     logger.debug('>>> Active Crow Import Tasks From Hubspot')
        #     crow_id.nextcall = fields.Datetime.now() + timedelta(minutes=5)
        #     crow_id.active = True

    def import_tickets_from_hubspot(self, hubspot_instance):
        if hubspot_instance.hubspot_sync_ticket and hubspot_instance.hubspot_is_import_ticket and hubspot_instance.active:
            # modifiedDateForDeals = float(hubspot_instance.modifiedDateForTicket or 0)
            logger.info('>>> Getting New and Modified tickets from hubspot')
            try:
                has_more = True
                after = False
                record_limit = 100
                while has_more:
                    tickets_ids = []
                    url = '/crm/v3/objects/tickets?limit={}'.format(str(record_limit))
                    if bool(after):
                        url = '{}&after={}'.format(url,after) 
                    response_get_tickets = hubspot_instance._send_get_request(url)
                    json_tickets_response = json.loads(response_get_tickets)
                    if bool(json_tickets_response.get('paging')) and bool(json_tickets_response['paging'].get('next')):
                        after = json_tickets_response['paging']['next'].get('after', False)
                    else:
                        has_more = False
                    logger.debug('>>> Get Tickets Parameters: Paging={}, limit={}, After={}, More={}'.format(str(json_tickets_response.get('paging','End')),
                                                                                                     str(record_limit),
                                                                                                     str(after),
                                                                                                     str(has_more)))
                    for ticketDetails in json_tickets_response['results']:
                        ticket_id = self.search(['|',('active','=',True),('active','=',False),('hubspot_id','=',ticketDetails['id']),('hubspot_instance_id','=',hubspot_instance.id)],limit=1)
                        if not bool(ticket_id) or hubspot_instance.force_rewrite:
                            tickets_ids.append(ticketDetails['id'])
                        else:
                            odoo_modifiedDate = ticket_id.write_date
                            lastUpdated = self.convet_hubspot_time_to_datetime(ticketDetails.get('updatedAt','1970-01-01T00:00:00Z'))
                            if odoo_modifiedDate < lastUpdated:
                                tickets_ids.append(ticketDetails['id'])
                    if bool(tickets_ids):
                        self.get_ticket_details_and_create(tickets_ids, hubspot_instance)
                tickets = self.search(['|',('active','=',True),('active','=',False),('hubspot_instance_id','=',hubspot_instance.id)])
                tickets.import_engagements_tickets_from_hubspot()
                hubspot_instance.all_ticket = True
                message = 'Completed Getting All Pipelines from hubspot'
                self.env['hubspot.logger'].create_log_message('Import Stages', message)
                logger.debug('>>> Completed Getting modified Ticket from hubspot')
            except Exception as e:
                error_message = 'Error while getting ticket stages in odoo, Hubspot response %s' % (str(e))
                self.env['hubspot.logger'].create_log_message('Import Pipelines', error_message)
                logger.exception(">>> Error in import_tickets_from_hubspot, " + str(e))
                hubspot_instance._raise_user_error(e)

    def import_engagements_tickets_from_hubspot(self):
        for ticket in self:
            hubspot_instance = ticket.hubspot_instance_id
            url_all = '/crm/v3/objects/tickets/{}/associations/engagements'.format(str(ticket.hubspot_id))
            response_engagements = hubspot_instance._send_get_request(url_all)
            json_response_engagements = json.loads(response_engagements)
            for engagement in json_response_engagements.get('results',[]):
                url = '/engagements/v1/engagements/{}'.format(engagement['id'])
                response_engagement_id = hubspot_instance._send_get_request(url)
                json_response_engagement_id = json.loads(response_engagement_id)
                if json_response_engagement_id['engagement']['type'] in ['NOTE','EMAIL','TASK','INCOMING_EMAIL']:
                    self.env['mail.activity'].get_task_details_and_create([engagement['id']], hubspot_instance)
            

    def get_name_ticket_fields(self):
        ticket_fields = self.env['hubspot.ticket.fields'].search([]).filtered(lambda x: str(x.field_type).find('calculation') < 0 )
        names = []
        for field_name in ticket_fields:
            names += [field_name.technical_name]
        return ','.join(names)

    def get_ticket_details_and_create(self, tickets_ids, hubspot_instance):
        for tickets_id in tickets_ids:
            logger.debug('>>> Get Ticket Pipeline %s details' % str(tickets_id))
            ticket_info = []
            try:
                response_get_ticket_by_id = hubspot_instance._send_get_request('/crm/v3/objects/tickets/{}?properties={}'.format(str(tickets_id),self.get_name_ticket_fields()))
                json_response_get_ticket_by_id = json.loads(response_get_ticket_by_id)
                response_association_contact = hubspot_instance._send_get_request('/crm/v3/objects/tickets/{}/associations/contact'.format(str(tickets_id)))
                json_response_get_ticket_by_id['response_association_contact'] = json.loads(response_association_contact)
                response_association_company = hubspot_instance._send_get_request('/crm/v3/objects/tickets/{}/associations/company'.format(str(tickets_id)))
                json_response_get_ticket_by_id['response_association_company'] = json.loads(response_association_company)
                response_association_deals = hubspot_instance._send_get_request('/crm/v3/objects/tickets/{}/associations/deals'.format(str(tickets_id)))
                json_response_get_ticket_by_id['response_association_deals'] = json.loads(response_association_deals)
                response_association_conversations = hubspot_instance._send_get_request('/crm/v3/objects/tickets/{}/associations/conversations'.format(str(tickets_id)))
                json_response_get_ticket_by_id['response_association_conversations'] = json.loads(response_association_conversations)
                json_response_get_ticket_by_id['json_response'] = response_get_ticket_by_id
                ticket_info.append(json_response_get_ticket_by_id)
                self.createNewTicketInOdoo(ticket_info, hubspot_instance)
                self._cr.commit()
            except Exception as e:
                error_message = 'Error while importing hubspot ticket in odoo Id: %s, Hubspot response %s' % (tickets_id, str(e))
                self.env['hubspot.logger'].create_log_message('Import Ticket Pipeline', error_message)
                logger.exception(">>> Exception In getting Ticket info from Hubspot: " + error_message)
                hubspot_instance._raise_user_error(e)

    @api.model
    def setFollowers(self,list_followers):
        for dict_follower in list_followers:
            dict_follower['res_id'] = self.id
            logger.debug(">>> Add follow New in ticket Into Odoo %s" % str(dict_follower['res_id']))
            if self.env['mail.followers'].search_count([('res_model','=',dict_follower['res_model']),
                                                        ('partner_id','=',dict_follower['partner_id']),
                                                        ('res_id','=',dict_follower['res_id']),]) == 0:
                try:
                    self.env['mail.followers'].create(dict_follower)
                except Exception as e:
                    self.env.cr.rollback()
                    logger.debug(">>> Try add follower in ticket: %s" % str(e))

    @api.model
    def createNewTicketInOdoo(self, ticket_dict, hubspot_instance):
        try:
            default_subtypes = self.env['mail.message.subtype'].search([('default','=', True),
                                                                        '|', ('res_model', '=', self._name), ('res_model', '=', False)])

            for ticket_details in ticket_dict:
                hubspot_id = ticket_details['id']
                
                vals = {
                    'hubspot_id': hubspot_id,
                    'active': False if ticket_details.get('archived', False) else True,
                }
                message_follower_ids = []
                properties = ticket_details.get('properties', {}) 
                if bool(properties.get('createdate')):
                    try:
                        create_date = self.convet_hubspot_time_to_datetime(properties['createdate'])
                        vals['create_date'] = datetime.datetime.strftime(create_date,DEFAULT_SERVER_DATETIME_FORMAT)
                    except:
                        logger.debug('>>> Data Criação inválida {}'.format(properties.get('createdate','not exist')))
                if bool(properties.get('closed_date')):
                    try:
                        closed_date = self.convet_hubspot_time_to_datetime(properties['closed_date'])
                        vals['close_date'] = datetime.datetime.strftime(closed_date, DEFAULT_SERVER_DATETIME_FORMAT)
                    except:
                        logger.debug('>>> Data Fechamento inválida {}'.format(properties.get('close_date','not exist')))
                
                if bool(properties.get('hs_created_by_user_id')):
                    user_id = self.env['res.users'].search([('hubspot_id','=',properties['hs_created_by_user_id'])],limit=1)
                    if bool(user_id):
                        vals['reporter_id'] = user_id.id
                        message_follower_ids += [{
                            'res_model': self._name,
                            'subtype_ids': [(6, 0, default_subtypes.ids)],
                            'partner_id': user_id.partner_id.id
                        }]

                if bool(properties.get('subject')):
                    vals['name'] = properties['subject']
                if bool(properties.get('content')):
                    vals['description'] = properties['content']
                if bool(properties.get('hs_pipeline')):
                    team_id = self.env['helpdesk.team'].sudo().search(['|',('active','=',True),('active','=',False),
                                                                           ('hubspot_id','=',properties['hs_pipeline']),
                                                                           ('hubspot_instance_id','=',hubspot_instance.id)],limit=1)
                    if bool(team_id):
                        vals['team_id'] = team_id.id
                if bool(properties.get('hs_pipeline_stage')):
                    stage_id = self.env['helpdesk.stage'].sudo().search([('hubspot_id','=',int(properties['hs_pipeline_stage'])),
                                                                         ('hubspot_instance_id','=',hubspot_instance.id)], limit=1)
                    if bool(stage_id):
                        vals['stage_id'] = stage_id.id
                if bool(properties.get('hs_ticket_category')):
                    vals['tag_ids'] = [(5,)]
                    tags = str(properties['hs_ticket_category']).split(';')
                    for tag in tags:
                        tag_id = self.env['helpdesk.tag'].sudo().search([('name','=',tag)])
                        if not bool(tag_id):
                            tag_id = self.env['helpdesk.tag'].sudo().create({'name': tag})
                        if bool(tag_id):
                            vals['tag_ids'] += [(4, tag_id.id)]
                if bool(properties.get('source_type')):
                    ticket_source_id = self.env['helpdesk.ticket.channel'].sudo().search([('name','=',properties['source_type'])])
                    if not bool(ticket_source_id):
                        ticket_source_id = self.env['helpdesk.ticket.channel'].sudo().create({'name': properties['source_type']})
                    if bool(ticket_source_id):
                        vals['channel_id'] = ticket_source_id.id

                if bool(properties.get('hs_ticket_priority')):
                    if properties['hs_ticket_priority'] == 'LOW':
                        vals['priority'] = '1'
                    elif properties['hs_ticket_priority'] == 'MEDIUM':
                        vals['priority'] = '2'
                    elif properties['hs_ticket_priority'] == 'HIGH':
                        vals['priority'] = '3'

                if bool(properties.get('hs_resolution')):
                    resolution_id = self.env['helpdesk.ticket.resolution'].sudo().search([('name','=',properties['hs_resolution'])])
                    if not bool(resolution_id):
                        resolution_id = self.env['helpdesk.ticket.resolution'].sudo().create({'name': properties['hs_resolution']})
                    if bool(resolution_id):
                        vals['resolution_id'] = resolution_id.id
                solicitante = True
                if bool(ticket_details.get('response_association_contact')):
                    for contact in ticket_details['response_association_contact']['results']:
                        partner_id = self.env['res.partner'].search(['|',('active','=',True),('active','=',False),('hubspot_id','=',contact['id']),
                                                                  ('hubspot_instance_id','=',hubspot_instance.id)])
                        if not bool(partner_id):
                            partner_ids = self.env['res.partner'].get_contact_details_and_create([contact['id']],hubspot_instance.id)
                            if len(partner_ids) > 0:
                                partner_id = self.env['res.partner'].browse(partner_ids[0])
                        if bool(partner_id) and solicitante:
                            vals['partner_id'] = partner_id.id
                            solicitante = False
                            
                        message_follower_ids += [{
                            'res_model': self._name,
                            'subtype_ids': [(6, 0, default_subtypes.ids)],
                            'partner_id': partner_id.id
                        }]

                if bool(ticket_details.get('response_association_company')):
                    for contact in ticket_details['response_association_company']['results']:
                        partner_id = self.env['res.partner'].search(['|',('active','=',True),('active','=',False),('hubspot_id','=',contact['id']),
                                                                  ('hubspot_instance_id','=',hubspot_instance.id)])
                        if bool(partner_id) and solicitante:
                            vals['partner_id'] = partner_id.id
                            vals['partner_email'] = partner_id.email
                            vals['partner_phone'] = partner_id.phone
                            solicitante = False
                        message_follower_ids += [{
                            'res_model': self._name,
                            'subtype_ids': [(6, 0, default_subtypes.ids)],
                            'partner_id': partner_id.id}]

                vals['hubspot_response'] = str(ticket_details)
                ticket_id = self.sudo().search(['|',('active','=',True),('active','=',False),('hubspot_id','=',hubspot_id),('hubspot_instance_id','=',hubspot_instance.id)])
                if bool(ticket_id):
                    logger.debug('>>> Write Ticket from Hubspot: %s' % str(vals))
                    ticket_id.with_context({'from_hubspot': True}).write(vals)
                    self._cr.commit()
                    logger.debug('>>> Write into existing Odoo ticket stage id %s' % str(team_id.ids))
                else:
                    logger.debug('>>> Create Ticket from Hubspot: %s' % str(vals))
                    vals['hubspot_instance_id'] = hubspot_instance.id
                    ticket_id = self.with_context({'from_hubspot': True}).create(vals)
                    logger.debug(">>> Created New ticket stage Into Odoo %s" % str(ticket_id.id))
                if bool(ticket_id):
                    ticket_id.setFollowers(message_follower_ids)
                return ticket_id
        except Exception as e:
            error_message = 'Error while creating hubspot ticket stage in odoo vals: %s, Hubspot response %s' % (ticket_details, str(e))
            self.env['hubspot.logger'].create_log_message('Import ticket stage', error_message)
            logger.exception(">>> Exception in Creating New Ticket in Odoo: " + error_message)
            hubspot_instance._raise_user_error(e)

    def action_engagement(self):
        for reg in self:
            reg.import_engagements_tickets_from_hubspot()
    