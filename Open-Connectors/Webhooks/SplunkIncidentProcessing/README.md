## Get details from Splunk on HTTP Event Collector
By enabling the following feature on Splunk and then configuring a webhook within Authomize to point to your instance, Splunk will ingest Authomize events.

1. Read through the splunk technical documention for the [event collector](https://docs.splunk.com/Documentation/Splunk/latest/Data/FormateventsforHTTPEventCollector).
2. Understand how to configure the Webhook back on Authomize by reading the [splunk admin documentation](https://docs.splunk.com/Documentation/Splunk/9.0.4/Data/UsetheHTTPEventCollector#Configure_HTTP_Event_Collector_on_Splunk_Cloud_Platform).
3. You will need to contact Splunk Support if you are using Splunk Cloud to ensure you enable "query string authentication". This enables Authomize to send JSON events to splunk and authenticate using the token in the URI.

Once you have a token from Splunk.

## Create a Webhook In Authomize
1. **Login** to your Authomize tenant with **Admin** priveleges.
2. From the **Configuration** menu found on the top right of your screen, select **Webhooks** located on the menu bar to the left.
3. Click the **Create Webhook** button found top right.
4. When the **Create Webhook** dialogue box comes up you will see three fields:
   * **Webhook Name**
   * **URL**
   * **Events to subscribe**
5. On the **Webhook Name** field enter a meaningful name such as `Splunk-Authomize-Events`.
6. On the **URL** field enter the url [https://```<see splunk doco>```.splunk.com/```<see splunk doco>```] .
   * Remember to use the  **Splunk key** you get from Splunk Support in this url.
7. On the **Events to subscribe** field select **Incident Created**
8. Click the **Create** button to save your settings.

You are now complete, you should montor the **Webhook logs** found on the left menu bar to determine when events are being sent. Authomize customer success team work closley with all Authomize customers and will be able to support you in the process. If you have any questions or issues please reach out to us on support@authomize.com and a success team member will respond to you as they can.