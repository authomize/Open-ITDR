# Templar Shield - Authomize / Archer Integration
This is a new project. Documentation will be evolving.  

## Info  
Connecting Authomize to select enterprise systems using Flask.  

## Codebase  
Project code is hosted in a private repository.  

## Development  
Development has been leveraging gitpod.io and VS Code.  

## Production  
Deployment models anticipated:
* AWS Lambda.
* Azure Functions.
* Other deployment models based on customer requirements.

## API Activities
These are routes in the Flask app which make requests to related Archer and Authomize API endpoints.<br/>

### Authomize

#### Test requests - Routes that trigger a GET request
* _/authomize/test/me_ - details associated with api token
* _/authomize/test/is_alive_ - API success test

#### Integration requests - Routes that pull from Archer and push to Authomize
These activities are deployed and run on a schedule or through some other mechanism for a customer deployment.
* _/authomize/archer/post_users_ - pull users from Archer, push them to Authomize as user accounts
* _/authomize/archer/post_assets_ - pull applications from Archer, push them to Authomize as assets
* _/authomize/archer/post_privileges_ - pull roles from Archer, push them to Authomize as privileges (e.g. SOA Docs - Update)
* _/authomize/archer/post_access_groupings/groups_ - pushes access groupings (groups) to Authomize
* _/authomize/archer/post_access_groupings/roles_ - pushes access groupings (roles) to Authomize
* _/authomize/archer/post_accounts_associations_ - pushes accounts associations (role memberships)
* _/authomize/archer/post_permissions_ - pushes account permissions (userId/groupingId, User/Grouping, privilegeId, assetId, isRole)

### Archer

#### Routes that trigger a GET request
* _/archer/login_ - generates a new Archer login token
* _/archer/logout_ - invalidates an Archer token
* _/archer/users_ - returns Archer users
* _/archer/users2_ - returns Archer users w/email
* _/archer/usercontacts_ - returns Archer user contacts
* _/archer/groups_ - returns Archer groups
* _/archer/roles_ - returns Archer roles 
* _/archer/roles2_ - gets Archer roles, maps them to a code object and returns the first one
* _/archer/groupmemberships_ - returns Archer group membership
* _/archer/rolememberships_ - returns Archer role membership
* _/archer/userswithemail_ - similar to /users2 (users + email)
* _/archer/applications_ - returns Archer applications
* _/archer/grouphierarchy_* - returns Archer grouphierarchy
* _/archer/levels_* - returns Archer levels
*in progress*

### Setup
Configuration options will vary based on environment requirements.
