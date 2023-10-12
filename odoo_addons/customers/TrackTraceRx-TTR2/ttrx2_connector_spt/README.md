# Track Trace Rx2 - TTRX2 - Odoo ERP Connector

## Description
<ul>
    <li>Provide integration with Track TraceRx2.</li>
    <li>Import and Export customer and vendor along with its child contact.</li>
    <li>Import and Export Product, and it's stock and price.</li>
    <li>Import sale order with its delivery order</li>
    <li>Import purchase order with its shipment.</li>
    <li>Other inventory operation like manage location,stock adjustment etc.</li>
</ul>

# About this project
This project aims to integrate the Odoo ERP with Track Trace API, using a custom made module based on REST requests and responses.

## Summary
This module was developed to integrate Odoo and Track Trace Portal, this occurs in 3 ways:

<ol>
    <li>Receive data (From TTRX Portal)</li>
    <li>Send data (To TTRX Portal)</li>
    <li>Receive and Send data</li>
</ol>

In summary, the connector receive a lot of data from the Portal API. The most important data are:

<ul>
    <li>
        <h4>Trading Partners</h4>
        <code>models: res.partner | trading.partner.address.spt</code>
    </li>
    <li>
        <h4>Products</h4>
        <code>models: product.spt | product.template | product.product</code>
    </li>
    <li>
        <h4>Manufacturers</h4>
        <code>models: manufacturers.spt</code>
    </li>
    <li>
        <h4>Sale Orders</h4>
        <code>models: sale.order</code>
    </li>
    <li>
        <h4>Purchase Orders</h4>
        <code>models: purchase.order</code>
    </li>
    <li>
        <h4>Stock Picking from:</h4>
    </li>
    <ul>
        <li>Sale Orders</li>
        <code>models: stock.picking (self.origin appointing to sale.order)</code>
        <li>Purchase Orders</li>
        <code>models: stock.picking (self.origin appointing to sale.order)</code>
    </ul>
</ul>

#
## Debugging the module
Each one of these data referenced above has methods to receive and to send data through the Track Trace RX API

### Where to debug?
The best recommended way to debug the connector related methods is to use the python debugger configured in your code editor, focusing the breakpoints into the following methods:

<ul>
    <li>
        <h3>To Receive data from API to Odoo ERP</h3>
        <code>def FromTTRxToOdoo(self, connector, values)</code>
    </li>
    <li>
        <h3>To Send data from Odoo ERP to API</h3>
        <code>def FromOdooToTTRx(self, connector, values={})</code>
    </li>
</ul>

## What is necessary to run the connector?
There are some configurations that is needed to make the connector works accordingly:

<ul>
    <li>Track Trace Portal URL</li>
    <li>Track Trace Portal API Key</li>
    <li>Click at the connector button "to approve"</li>
    <li>Click at the connector button "validate" to stabilish the connection</li>
</ul>

## Cautions and Warnings!
BEFORE you activate the actions to loading the integration data, you must validate, at the connector sync wizard the way that the module will work the syncronization!

# EPCIS Integration
Although the Track Trace API returns the EPCIS data related with the products movimentation, there are not already finished in Track Trace, so far we know.

Thinking in it, we had just implemented 4 new classes to make the connector module be ready to receive its data when this development and implementation will be done in the future.

These classes are:

<ul>
    <li>
        <h4>Copy EPCIS Aggregation and Disaggregation to Custom 2nd Party</h4>
        <code>model: copy.epcis.aggregation.and.disaggregation.custom.2nd.party</code>
    </li>
    <li>
        <h4>Copy EPCIS Commission and Decommission to Custom 2nd Party</h4>
        <code>model: copy.epcis.commission.and.decommission.custom.2nd.party</code>
    </li>
    <li>
        <h4>Copy Outbound Shippment to Custom Party</h4>
        <code>model: copy.outbound.shipment.to.custom.2nd.party</code>
    </li>
    <li>
        <h4>Format of Copy Outbound Shipment to Custom 2nd Party</h4>
        <code>model: format.of.copy.outbound.shipment.to.custom.2nd.party</code>
    </li>
</ul>
