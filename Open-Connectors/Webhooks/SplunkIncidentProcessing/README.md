# Splunk-Authomize Integration

This document provides step-by-step instructions on how to set up a Splunk HTTP Event Collector (HEC) for integrating Splunk with Authomize. The guide covers the setup process for both Splunk Cloud and Splunk Enterprise.

The Splunk-Authomize integration enables you to collect and analyze security events from Authomize in your Splunk environment. This integration relies on tokens for authentication.

## Prerequisites

- A Splunk Cloud or Splunk Enterprise instance.
- Authomize account with the necessary permissions.
- Basic understanding of Splunk and Authomize.

## Setting up the HTTP Event Collector (HEC)

Follow these steps to set up the Splunk HEC for both Splunk Cloud and Splunk Enterprise:

### 1. Enable HEC

**Splunk Cloud**

If you are using Splunk Cloud, submit a support request to enable HEC:
- Go to https://www.splunk.com/en_us/support-and-services.html
- Ensure you request that you can use query string authorization for HEC
- Click "Submit a request" and follow the instructions to request HEC enablement

**Splunk Enterprise**

If you are using Splunk Enterprise, enable HEC by following these steps:
- Log in to Splunk Web as an administrator.
- Go to Settings > Data Inputs.
- Click on HTTP Event Collector.
- Click on "Global Settings" in the top-right corner.
- Set "All Tokens" to "Enabled".
- Click "Save".
- Now enable the query string authorization for HEC
   - You'll need to modify the HEC configuration in your Splunk instance.
   - Open the inputs.conf file located in `$SPLUNK_HOME/etc/apps/<your-app>/local` (create the file if it doesn't exist).
      - `<your-app>` should be splunk_httpinput
   - Add the following lines:
      - `[http]`
      - `allowQueryStringAuth = true`


### 2. Create an HEC Token

**Splunk Cloud and Splunk Enterprise**

To create an HEC token, follow these steps:
- Log in to Splunk Web as an administrator.
- Go to Settings > Data Inputs.
- Click on HTTP Event Collector.
- Click "New Token".
- Fill in the required fields (Name, Description, and Source type) and click "Next".
- Select an existing index or create a new one, and click "Review".
- Review your token settings and click "Submit" to create the token.
- Copy the generated token value and save it. You will use this token for the Authomize webhook configuration.

## Configuring Authomize Webhook

To configure the Authomize webhook, follow these steps:

1. Log in to your Authomize account.
2. Go to the settings or integrations page.
3. Locate the webhook settings or integration section.
4. Enter the Splunk HEC URL and the token you saved earlier.
   - The HEC URL format should be: `https://<hec_hostname>:<hec_port>/services/collector/raw?token=<your-token>`
   - Replace `<hec_hostname>` with your Splunk instance's hostname, and `<hec_port>` with the port on which HEC is listening (default is 8088) and `<your-token>` which you got when you configured the HTTP Event Collector.
5. Save the configuration.

## Testing the Integration

To test the integration, trigger a test event from Authomize. The event should appear in Splunk in the index you specified during the HEC token creation.

## Troubleshooting

If you encounter any issues during the setup process, consult the Splunk and Authomize documentation or contact their respective support teams:

- Splunk Support: https://www.splunk.com/en_us/support-and-services.html
- Authomize Support: https://www.authomize.com/contact

## Further Reading

- Splunk HTTP Event Collector documentation: https://docs.splunk.com/Documentation/Splunk/9.0.4/Data/UsetheHTTPEventCollector
- Authomize documentation: https://www.authomize.com/docs