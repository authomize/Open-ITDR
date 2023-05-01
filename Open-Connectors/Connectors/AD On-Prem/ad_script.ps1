Import-Module ActiveDirectory

# Define variables
$useCredentialManager = $true # Set this to $true to use CredentialManager, $false to use environment variables. For Security reasons using CredentialManager is preferred.
$authToken = "ENTER AUTHOMIZE TOKEN HERE" # Set as CredentialManager `Target` field or Environmental Variable Name 
$appId = "ENTER AUTHOMIZE APP ID HERE" # Replace with your App ID
$ou = "DC=authomizese,DC=com" # Replace with the OU you'd like to pull AD information from
$excludeOUs = $true # Set this variable to $true if you want to exclude a specific OU, otherwise set it to $false
$excludedOU = ".*OU=exampleOU.*" # REGEX match - The .* in this variable serves as wildcards, allowing any characters to appear before or after the OU=TST,OU=Tier 2 pattern. Use the regex | to list multiple OUs. Irrelevant if $excludeOUs = $false. 
$baseDirectory = $PSScriptRoot # Get the base directory of the script
$logFilePath = "$baseDirectory\ad_script.log" # Log file

# Decrypt Token function
function Convert-SecureStringToPlainText {
    param($secureString)

    $BSTR = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureString)
    $plainText = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR)
    [System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($BSTR)

    return $plainText
}

# Use CredentialManager or Environment variable based on boolean $useCredentialManager
function Get-Credentials ($useCredentialManager) {
    if ($useCredentialManager) {
        # Import CredentialManager module
        Import-Module -Name CredentialManager

        # Get credentials from CredentialManager
        $apiTokenCredential = Get-StoredCredential -Target "$authToken"
        $authToken = Convert-SecureStringToPlainText -secureString $apiTokenCredential.Password
        
    } else {
        # Get credentials from environment variables
        $authToken = (Get-Item "env:$authToken").Value 
    }

    return @{
        AuthToken = $authToken
    }
}

#Sets authToken
$credentials = Get-Credentials -useCredentialManager $useCredentialManager
$authToken = $credentials.AuthToken

#Authomize Endpoints & Parameters
$apiBase = "https://api.authomize.com/v2/apps"
$usersEndpoint = "/accounts/users"
$identitiesEndpoint = "/identities"
$groupsEndpoint = "/access/grouping"
$accountAssociationEndpoint = "/association/accounts"
$groupingAssociationEndpoint = "/association/groupings"
$deleteEndpoint = "/$appId/data?=modifiedBefore="
$headers = @{
    "Authorization" = $authtoken
}
$chunkSize = 1000

# Verify the credentials. Write to Powershell console
Write-Host "API appId: $appId"
Write-Host "API Token: $authToken"

# Write over Log File
$newContent = "#Log File"
Set-Content -Path $logFilePath -Value $newContent

# Get all AD users
$adUsers = Get-ADUser -Filter {objectClass -eq 'user'} -SearchBase $ou -Properties ObjectGUID, Name, Mail, Title, GivenName, Surname, Enabled, Description, Manager, LastLogonDate, City, Country, Department, EmployeeNumber

# Filter out excluded OUs if $excludeOUs is set to $true
if ($excludeOUs) {
    $adUsers = $adUsers | Where-Object { $_.DistinguishedName -notmatch $excludedOU }
}

# Get all AD groups
$adGroups = Get-ADGroup -Filter * -SearchBase $ou -Properties ObjectGUID, Name, GroupCategory, ManagedBy

# Filter out excluded OUs if $excludeOUs is set to $true
if ($excludeOUs) {
    $adGroups = $adGroups | Where-Object { $_.DistinguishedName -notmatch $excludedOU }
}

# Create empty arrays
$accountsUserData = @()
$identitiesUserData = @()
$groupsData = @()
$userGroupAssociationsData = @()
$groupGroupAssociationsData = @()

# Loop through AD users
foreach ($adUser in $adUsers) {
    $status = switch ($adUser.Enabled) {
        $true { "Enabled" }
        $false { "Disabled" }
        default { "Unknown" }
    }

    $accountsUserObject = @{
        uniqueId     = $adUser.ObjectGUID
        originId     = $adUser.ObjectGUID
        name         = $adUser.Name
        email        = $adUser.Mail
        firstName    = $adUser.GivenName
        lastName     = $adUser.Surname
        status       = $status
        description  = $adUser.Description
        lastLoginAt  = if ($adUser.LastLogonDate) { (Get-Date $adUser.LastLogonDate -Format "yyyy-MM-ddTHH:mm:ssZ") } else { $null }
    }

    $identitiesUserObject = @{
    uniqueId       = $adUser.ObjectGUID
    originId       = $adUser.ObjectGUID
    name           = $adUser.Name
    email          = $adUser.Mail
    managerId      = if ($adUser.Manager) {
                        $manager = Get-ADUser -Identity $adUser.Manager -Properties DistinguishedName, ObjectGUID
                        if ($excludeOUs -and ($manager.DistinguishedName -match $excludedOU)) {
                            $null
                        } else {
                            $manager.ObjectGUID
                        }
                    } else {
                        $null
                    }
    title          = $adUser.Title
    firstName      = $adUser.GivenName
    lastName       = $adUser.Surname
    status         = $status
    description    = $adUser.Description
    city           = $adUser.City
    country        = $adUser.Country
    department     = $adUser.Department
    employeeNumber = $adUser.EmployeeNumber
}

    $accountsUserData += $accountsUserObject
    $identitiesUserData += $identitiesUserObject
 

    # Get the groups the current user is a member of
    $userGroups = Get-ADPrincipalGroupMembership -Identity $adUser | Where-Object { $_.DistinguishedName -like "*$ou" }

    # Filter out excluded OUs if $excludeOUs is set to $true
    if ($excludeOUs) {
        $userGroups = $userGroups | Where-Object { $_.DistinguishedName -notmatch $excludedOU }
    }

    # Add group membership to $userGroupAssociationsData
    $userGroups | Select-Object -ExpandProperty ObjectGUID | ForEach-Object {
        $userGroupMembership = @{
            sourceId = $adUser.ObjectGUID
            targetId = $_.Guid
        }
        $userGroupAssociationsData += $userGroupMembership
    }
}

# Loop through AD groups
foreach ($adGroup in $adGroups) {
    $groupObject = @{
    uniqueId             = $adGroup.ObjectGUID
    originId             = $adGroup.ObjectGUID
    name                 = $adGroup.Name
    originType           = $adGroup.GroupCategory.ToString()
    type                 = "Group"
    alternativeName      = if ($adGroup.Description.Length -gt 256) { $adGroup.Description.Substring(0, 256) } else { $adGroup.Description }
    owner                = if ($adGroup.ManagedBy) { 
                                $object = Get-ADObject -Identity $adGroup.ManagedBy
                                if($object.ObjectClass -eq 'user') {
                                    $user = Get-ADUser -Identity $adGroup.ManagedBy
                                    if($excludeOUs -and ($user.DistinguishedName -match $excludedOU)) {
                                        $null
                                    } else {
                                        $user.ObjectGUID
                                    }
                                } else {
                                    $null
                                }
                          } else { 
                                $null 
                          }
} 

    $groupsData += $groupObject

    # Get the groups the current group is a member of
    $groupMemberships = Get-ADPrincipalGroupMembership -Identity $adGroup | Where-Object { $_.DistinguishedName -like "*$ou" } | Where-Object { $_.ObjectClass -eq 'Group' }

    # Filter out excluded OUs if $excludeOUs is set to $true
    if ($excludeOUs) {
        $groupMemberships = $groupMemberships | Where-Object { $_.DistinguishedName -notmatch $excludedOU }
    }

    # Add group memberships to $groupGroupAssociationsData
    $groupMemberships | Select-Object -ExpandProperty ObjectGUID | ForEach-Object {
        $groupGroupMembership = @{
            sourceId = $adGroup.ObjectGUID
            targetId = $_.Guid
        }
        $groupGroupAssociationsData += $groupGroupMembership
    }
}

# Function to post data in chunks and write response to a log file
function PostDataInChunks ($url, $jsonData, $token, $logFilePath) {
    $headers = @{
        "Authorization" = "$token"
    }
    $acceptedTimestampList = @()
    $index = 0
    
    while ($index -lt $jsonData.data.Count) {
        $chunk = @{
            data = $jsonData.data[$index..($index + $chunkSize - 1)]
        } | ConvertTo-Json

        try {
            $Response = Invoke-RestMethod -Method POST -Uri $url -Body $chunk -ContentType "application/json" -Headers $headers -ErrorAction Stop
            if ($Response) {
                $acceptedTimestampList += $Response.acceptedTimestamp
                # Write response JSON to log file
                Add-Content -Path $logFilePath -Value ("`n" + (Get-Date -Format "yyyy-MM-dd HH:mm:ss") + " - API request to $url at index $index with chunk size $($chunkSize): $($Response | ConvertTo-Json -Compress)")
            }
        } catch {
            Add-Content -Path $logFilePath -Value ("`n" + (Get-Date -Format "yyyy-MM-dd HH:mm:ss") + " - Error during API request to $url at index $index with chunk size $($chunkSize). Exception Message: $($_.Exception.Message)")
        }
        $index += $chunkSize
    }
    
    return $acceptedTimestampList
}

# Counts of Data Arrays
$accountsUserCount = $accountsUserData.Count
$identitiesUserCount = $identitiesUserData.Count
$groupsCount = $groupsData.Count
$userGroupAssociationsCount = $userGroupAssociationsData.Count
$groupGroupAssociationsCount = $groupGroupAssociationsData.Count

# Write Array Counts to log file
Add-Content -Path $logFilePath -Value ("`n" + (Get-Date -Format "yyyy-MM-dd HH:mm:ss") + " - Accounts User Count: $accountsUserCount")
Add-Content -Path $logFilePath -Value ((Get-Date -Format "yyyy-MM-dd HH:mm:ss") + " - Identities User Count: $identitiesUserCount")
Add-Content -Path $logFilePath -Value ((Get-Date -Format "yyyy-MM-dd HH:mm:ss") + " - Groups Count: $groupsCount")
Add-Content -Path $logFilePath -Value ((Get-Date -Format "yyyy-MM-dd HH:mm:ss") + " - User Group Associations Count: $userGroupAssociationsCount")
Add-Content -Path $logFilePath -Value ((Get-Date -Format "yyyy-MM-dd HH:mm:ss") + " - Group Group Associations Count: $groupGroupAssociationsCount")

# Define variables for the POST requests
$accountsUsersUrl = "$apiBase/$appId$usersEndpoint"
$identitiesUrl = "$apiBase/$appId$identitiesEndpoint"
$groupsUrl = "$apiBase/$appId$groupsEndpoint"
$accountAssociationUrl = "$apiBase/$appId$accountAssociationEndpoint"
$groupingAssociationUrl = "$apiBase/$appId$groupingAssociationEndpoint"

# Convert user data to JSON and write json to files
$accountsJsonData = @{
    data = $accountsUserData
}
$accountsjson = $accountsJsonData | ConvertTo-Json
Set-Content -Path "$baseDirectory\accounts.json" -Value $accountsjson

$identitiesJsonData = @{
    data = $identitiesUserData
}
$identitiesjson = $identitiesJsonData | ConvertTo-Json
Set-Content -Path "$baseDirectory\identities.json" -Value $identitiesjson

$groupsJsonData = @{
    data = $groupsData
}
$groupsjson = $groupsJsonData | ConvertTo-Json
Set-Content -Path "$baseDirectory\groups.json" -Value $groupsjson

$userGroupAssociationsJsonData = @{
    data = $userGroupAssociationsData
}
$userGroupAssociationsjson = $userGroupAssociationsJsonData | ConvertTo-Json
Set-Content -Path "$baseDirectory\userGroupAssociations.json" -Value $userGroupAssociationsjson

$groupGroupAssociationsJsonData = @{
    data = $groupGroupAssociationsData
}
$groupGroupAssociationsjson = $groupGroupAssociationsJsonData | ConvertTo-Json
Set-Content -Path "$baseDirectory\groupGroupAssociations.json" -Value $groupGroupAssociationsjson

# POST data to the API endpoints in chunks 
$timestamps = PostDataInChunks $accountsUsersUrl $accountsJsonData $authToken $logFilePath
PostDataInChunks $identitiesUrl $identitiesJsonData $authToken $logFilePath
PostDataInChunks $groupsUrl $groupsJsonData $authToken $logFilePath
PostDataInChunks $accountAssociationUrl $userGroupAssociationsJsonData $authToken $logFilePath
PostDataInChunks $groupingAssociationUrl $groupGroupAssociationsJsonData $authToken $logFilePath

#save first POST accepted timestamp
$firstposttimestamp = $timestamps[0]

# Delete data older than the first POST
$Response = Invoke-RestMethod -Method Delete -Uri $apiBase$deleteEndpoint$firstposttimestamp -ContentType "application/json" -Headers $headers

# Write response to log file
Add-Content -Path $logFilePath -Value ("`n" + (Get-Date -Format "yyyy-MM-dd HH:mm:ss") + " - Delete data for $apiBase$deleteEndpoint$firstposttimestamp Response: $($Response | ConvertTo-Json -Compress)") 
