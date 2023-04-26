#### Authomize Active Directory Connector (Release - .9.1 Beta)

### Getting Started

## Download the Open-ITDR GitHub Repo & ensure the AD On-Prem folder is in the desired working directory. 
- Clone the repository into a working directory, by using git clone like the following - 
`gh repo clone authomize/Open-ITDR` https://github.com/authomize/Open-ITDR

## Required Permissions: 
- Active Directory permissions: The script needs permissions to query and read users and group data from the Active Directory. To achieve this, the account running the script should have at least "Read" permission on the OU (Organizational Units) being queried.
- Filesystem permissions: The script writes logs to a file ($logFilePath). The account running the script should have permission to create and write to the specified log file.
- PowerShell execution policy: To run the script, the PowerShell execution policy on the machine should be configured to allow running scripts. 

## Ensure you have RSAT Tools Installed
- RSAT Tools is Optional in some Installations
- Install RSAT Tools via PowerShell `Install-WindowsFeature -Name "RSAT-AD-PowerShell" -IncludeAllSubFeature`

## Install ActiveDirectory PowerShell Module
- Via Powershell `Install-Module -Name ActiveDirectory`

## Install CredentialManager 
- Via Powershell `Install-Module -Name CredentialManager`
- Store your token in CredentialManager:
	`New-StoredCredential -Target "AuthomizeApiToken" -UserName "token" -Password "<ENTER_AUTHOMIZE_TOKEN_HERE>" -Persist LocalMachine`
- More info about CredentialManager can be found here: https://www.powershellgallery.com/packages/CredentialManager/2.0
- Alternatively, you can use set your Token as a Windows Environment Variable. This is however less secure: https://kb.wisc.edu/cae/page.php?id=24500

## Define variables in ad_script.ps1
- Further variable details are in ad_script.ps1

## Use Windows Task Scheduler to Schedule ad_script.ps1
- Set the script to run on a 12 hour schedule
- For help with this refer to: https://learn.microsoft.com/en-us/windows/win32/taskschd/using-the-task-scheduler

## The Script Gathers the Below Information from Active Directory
- Users (objectclass = "user")
- Groups
- Users that are a memberOf each Group
- Groups that are a membersOf each Group

## Hints & other info:
- The created JSON files are only used for troubleshooting purposes. These can be safely commented out of the script if desired.
- The log file overwrites itself on every run. This is to keep the file small and easy to read.

