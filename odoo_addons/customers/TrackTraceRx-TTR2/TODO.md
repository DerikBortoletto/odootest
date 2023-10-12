# Description of project
Please check the [README](README.md) File

---
# TODO
- [ ] All App Description needs to improve
- [ ] The Contact import needs to improve
  - [ ] The Trading Partner needs to be imported as **Company** not as ~~Individual~~
  - [ ] The address needs to be imported as **Individual** contact
  - [ ] The address imported as above, needs to be linked to the company
  - [ ] The field name in Address will be the name in Odoo Contact
  - [ ] When import address the TP UUID needs to be saved in the Tracktrace TAB in General Tab, field UUID
  - [ ] The address UUID **CANNOT BE SAVED IN TP UUID** it should be saved in Addresses TAB in TT2 tab
- [ ] Make some standards fields, like State and Address in Company, required.
## Inbound
- [ ] When sending the information of Receiving, the sdi/Lot need to be informed
  - Log:
Tracktrace == {'error': True, 'code': 'TT2LC_SHIPMENTS-V00549', 'message': 'The field "Product sdi is required" is required', 'details': None, 'event_id': None}
- [ ] The user should be able to send the Shipment from Odoo -> TT2 Portal
- [ ] The system should be able to receive a Shipment via EDI/EPCIS - TT2 -> Odoo
- [ ] The Invoice should update the Shipment

## Outbound
- [ ] Sales Order error:
  - Tracktrace== {'error': True, 'code': 'TT2LC_PICKINGS-G04722', 'message': 'Not found this lot for this product UUID', 'details': 'Product: "b8355ac4-b6f1-4602-b894-c6227a9a294a";\r\nlot: {{ FALSE }}', 'event_id': None}