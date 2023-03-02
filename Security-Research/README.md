# Security Research
You can find here our security content, research, and tools, researched/developed by Authomize. This includes:

* Okta SCIM security research and attack tool
* Okta identity provider misconfigurations security research
* Authomize security research on account takeover attemps discovered in its proprietary data and related tactics
* Authomize's CTO HITB 2021 talk on modern post-explotation via IAM

## Okta SCIM security research and attack tool
This tool is based on [#passbleed](https://authomize.com/blog/authomize-discovers-password-stealing-and-impersonation-risks-to-in-okta/#challenges), and allows pen-testers to extract clear text passwords from Okta by abusing Okta's implementation of the System for Cross-domain Identity Management (SCIM) protocol. The issue allows for clear text password stealing and PII theft. The issue was discovered by [Authomize](https://www.authomize.com/). More information can be found in this [blog post](https://authomize.com/blog/authomize-discovers-password-stealing-and-impersonation-risks-to-in-okta/#challenges).
<br /><br />
[Tool GitHub repository](https://github.com/authomize/okta_scim_attack_tool)
<br />
[Tool technical video](https://www.youtube.com/watch?v=tPiuOimbwRY)


## Okta identity provider misconfigurations security research
This blog elaborates on Authomize's security reasearch with regards to Okta's IdP potential misconfigurations and the related risks. Read more [here](https://www.authomize.com/blog/trust-but-verify-how-to-secure-identity-provider-trust-relationships/)

## Account takeover security research
This blog elaborates on Authomize's security reasearch with regards to account takeover attempts detected in its proprietarty data and an overview of related account takeover tactics. Read more [here](https://www.authomize.com/blog/authomize-research-on-post-holiday-account-takeovers/)

## Gal Diskin, Authomize's CTO, HITB 2021 talk on modern post explotation via IAM 
Watch Gal Diskin's talk [here](https://www.youtube.com/watch?v=gkv4bWNWd3Q)

