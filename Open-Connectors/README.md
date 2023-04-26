# Open Solutions for Everyone
This area will contain solutions that provide value to developers and companies trying to find solutions to managing thier IAM infrastructure by collecting information and data from Authomize. We expect two see two types of integrations in this area:

There are three main areas listed here in the form of folders. The corresponding folder information is found below to give you some detail about what you will find.

- **Connectors -** these pull identity and application data from one system and inject it into Authomize through the API. These are generally considered inbound connections.
- **Platform -** or incident processing - These applications or middleware in some cases pull Incidents from Authomize and make it generally available for use or consumption by other tools. These are generally considered outbound connections.
- **Webhooks -** Sends incidents for consumption by other tooling products such as SIEMs, Orchestration or support ticketing systems. Generally there is very little code and sometimes just configuration steps listed here due to the nature of Webhooks. Also be aware that these same tools sometimes have middleware applications built as Platform integrations due to complexity of the use case.

### Final Note
When deciding where to place your integration consider your use case and exactly what its requirements are from an Authomize perspective and the third party being integrated with.

## Authomize Python Code
Authomize provides code that can be used within your python projects, this can be found [here](https://pypi.org/project/authomize-rest-api-client/).

## Get Postman OpenAPI Specifications
To help with any code you may be creating please download the specifications from the [Authomize API reference page](https://api.authomize.com/documentation). This will assist you with writing code against the API stack that Authomize provides.
