# Security Research
You can find here an live list of security content, research, and tools, researched/developed by Authomize and the broader community. This includes:


* Authomize Security Lab Research and Talks:
    1.  Passbleed - Authomize's discovered Okta misconfiguration that allows clear-text password exfiltration via SCIM
    2.  Authomize security lab Okta IdP misconfigurations research
    3.  Authomize security lab research on account takeover attemps discovered in its proprietary data and related tactics
    4.  Authomize's CTO's, Gal Diskin, HITB 2021 talk on modern post explotation via IAM 

* General Security Research and Talks:
    1. SAML attacks and vulnerabilities - Black Hat USA 2018 talk by [Kelby Ludwig](https://infocondb.org/presenter/kelby-ludwig) from Duo Security.                      Find the lecture [here](https://infocondb.org/con/black-hat/black-hat-usa-2018/identity-theft-attacks-on-sso-systems)
    2. Modern attack vectors - "Excuse Me, Your Sword Is In My Eye: Responding to Red Teams and 'IRL' Threats in 2019 and Beyond" - BSidesLV 2019 talk by [Jeremy Galloway](https://infocondb.org/presenter/jeremy-galloway) from Atlassian. Find the lecture [here](https://www.youtube.com/watch?v=HvFi6xCHnHE)
    3. Azure AD attack and defense playbook by AAD security researchers - find the playbook [here](https://github.com/Cloud-Architekt/AzureAD-Attack-Defense)
    4. [Rhino Secuirty Labs](https://rhinosecuritylabs.com/) AWS explotation framework - [Pacu](https://github.com/RhinoSecurityLabs/pacu)
    5. [HackTricks pentesting tools](https://book.hacktricks.xyz/welcome/readme), built by [Carlos Polop](https://www.linkedin.com/in/carlos-polop-martin/). Take a close look at the [AWS](https://cloud.hacktricks.xyz/pentesting-cloud/aws-pentesting) and [AAD](https://cloud.hacktricks.xyz/pentesting-cloud/azure-pentesting/az-lateral-movement-cloud-on-prem/azure-ad-connect-hybrid-identity) chapters.
    6. [infosecn1nja](https://github.com/infosecn1nja) has curated some awsome open source security tools on his [red teaming toolkit repo](https://github.com/infosecn1nja/Red-Teaming-Toolkit), including [enumerate-iam](https://github.com/andresriancho/enumerate-iam), [AAD connect password extraction](https://github.com/fox-it/adconnectdump), and [stormspotter](https://github.com/Azure/Stormspotter) - Azure and AAD attack graph tool.

## Authomize Security Lab Research

1. Passbleed - Okta SCIM security research
Authomize security lab discovered passbleed Okta misconfiguration - [#passbleed](https://authomize.com/blog/authomize-discovers-password-stealing-and-impersonation-risks-to-in-okta/#challenges), allowing the extraction of clear text passwords from Okta by abusing Okta's implementation of the System for Cross-domain Identity Management (SCIM) protocol. The issue allows for clear text password stealing and PII theft. More information can be found in this [blog post](https://authomize.com/blog/authomize-discovers-password-stealing-and-impersonation-risks-to-in-okta/#challenges). Watch Authomize's CTO, Gal Diskin, talk at HITB Singapore 2022 on this topic [here](https://conference.hitb.org/hitbsecconf2022sin/session/commsec-clear-text-psswrds-idp-more/_). See the related attack tool GitHub repository [here](https://github.com/authomize/okta_scim_attack_tool) and a technical video about the tool [here](https://www.youtube.com/watch?v=tPiuOimbwRY)
<br /><br />


2. Okta identity provider misconfigurations security research
This blog elaborates on Authomize's security reasearch with regards to Okta's IdP potential misconfigurations and the related risks. Read more [here](https://www.authomize.com/blog/trust-but-verify-how-to-secure-identity-provider-trust-relationships/)

3. Account takeover security research
This blog elaborates on Authomize's security reasearch with regards to account takeover attempts detected in its proprietarty data and an overview of related account takeover tactics. Read more [here](https://www.authomize.com/blog/authomize-research-on-post-holiday-account-takeovers/)

4. Gal Diskin, Authomize's CTO, HITB 2021 talk on modern post explotation via IAM 
Watch Gal Diskin's talk [here](https://www.youtube.com/watch?v=gkv4bWNWd3Q)

