# Get credentials from environment variables
# $authToken = (Get-Item "env:$authToken").Value 
# Hard Coded:
$appId = ""
$authToken = ""

# Verify the credentials. Write to Powershell console
Write-Host "API appId: $appId"
Write-Host "API Token: $authToken"

#Authomize Endpoints & Parameters
$apiBase = "https://api.authomize.com/v2/apps"
$usersEndpoint = "/accounts/users"
$identitiesEndpoint = "/identities"
$groupsEndpoint = "/access/grouping"
$accountAssociationEndpoint = "/association/accounts"
$groupingAssociationEndpoint = "/association/groupings"
$headers = @{
    "Authorization" = "$authtoken"
    "Content-Type" = "application/json; charset=UTF-16"
    "Accept" = "application/json"
    "Cache-Control" = "no-cache"
}

# Create empty arrays
$accountsUserData = @()
$identitiesUserData = @()
$groupsData = @()
$userGroupAssociationsData = @()
$groupGroupAssociationsData = @()

# Define the directories
$jsonDirectory = "JSONProcessing"
$processedDirectory = "processed"

#Define Static GUID for DeterministicGUID
$namespaceGuid = [Guid]"ffa7b810-9dff-0061-7574-686f6d697a65" # Authomize Name Space - DO NOT CHANGE.

# Get all JSON files from the directory
$jsonFiles = Get-ChildItem -Path $jsonDirectory -Filter *.json

function Send-JsonToAPI {
    param(
        [Parameter(Mandatory = $true)]
        [string]$JsonData
    )

    # Define the API base URL and specific endpoint
    $apiBase = "https://api.authomize.com/v2/apps"
    $usersEndpoint = "/accounts/users"
    
    # Hard Coded application ID and Auth token
    $appId = "db9512ef-17d5-410e-b23a-46b331409099"
    $authToken = "atmzMTYzNDUwNDcwMzY2OlJQWjZUOElVSEJJMVIxVVo0VFpWU1FQVU1WWEFJWlpQTlhUQ1hLTEdJRUk="

    # Construct the full URL
    $url = "$apiBase/$appId$usersEndpoint"

    # Set up the headers with the authorization token
    $headers = @{
        'Authorization' = "Bearer $authToken"
        'Content-Type'  = 'application/json'
    }

    try {
        # Send the POST request with the JSON data
        $response = Invoke-RestMethod -Method Post -Uri $url -Headers $headers -Body $JsonData -ErrorAction SilentlyContinue

        # Write the success status code to the console
        Write-Host "Successfully sent data. Status code: $($response.StatusCode)"
        
        # Return the response status code
        return $response.StatusCode
    } catch {
        # Catch the exception and write the error code to the console
        if ($_.Exception.Response) {
            $responseStatusCode = $_.Exception.Response.StatusCode.value__
            Write-Host "Error sending data. Status code: $responseStatusCode"
            Write-Host "Error: $($_.Exception.Message)"
        } else {
            Write-Host "Error: $($_.Exception.Message)"
        }
        
        # Continue execution in case of error
        continue

        # Return the error status code if available, otherwise return the exception message
        return if ($responseStatusCode) { $responseStatusCode } else { $_.Exception.Message }
    }
}


Function New-DeterministicGuid {
    [CmdletBinding()]
    param (
        [Parameter(Mandatory)]
        [string]$Name,

        [Parameter(Mandatory)]
        [Guid]$Namespace
    )

    # Convert the namespace UUID to a byte array
    $namespaceBytes = $Namespace.ToByteArray()
    # Swap the bytes of the GUID to match the RFC 4122 order
    [Array]::Reverse($namespaceBytes[0..3])
    [Array]::Reverse($namespaceBytes[4..5])
    [Array]::Reverse($namespaceBytes[6..7])

    # Convert the name to a byte array
    $nameBytes = [Text.Encoding]::UTF8.GetBytes($Name)

    # Concatenate the namespace and name bytes
    $contentBytes = $namespaceBytes + $nameBytes

    # Compute the SHA-1 hash of the content
    $hash = [Security.Cryptography.SHA1]::Create().ComputeHash($contentBytes)

    # Create a new byte array for the GUID that includes parts of the hash
    $guidBytes = $hash[0..15]

    # Overwrite the version and variant bits according to RFC 4122 for version 5 UUIDs
    $guidBytes[6] = ($guidBytes[6] -band 0x0F) -bor 0x50
    $guidBytes[8] = ($guidBytes[8] -band 0x3F) -bor 0x80

    # Reverse the byte order to match RFC 4122 for certain segments
    # For GUIDs, the first 4-byte block and the following 2-blocks (2 bytes each) are in reverse order
    $byteOrder = [byte[]]@(6,7,4,5,0,1,2,3,8,9,10,11,12,13,14,15)
    $orderedGuidBytes = $byteOrder | ForEach-Object { $guidBytes[$_] }

    # Convert the ordered bytes to a hex string and format as a GUID string
    $hexString = ($orderedGuidBytes | ForEach-Object { $_.ToString("X2") }) -join ''
    $guidString = $hexString.Insert(20, "-").Insert(16, "-").Insert(12, "-").Insert(8, "-")

    # Now create the Guid from the string
    try {
        return [Guid]::new($guidString)
    } catch {
        Write-Output "Failed to create GUID from string. GUID String: $guidString"
        throw
    }

}

function Add-MembersToGlobalList {
    param(
        [Parameter(Mandatory = $true)]
        [System.Collections.ArrayList]$membersList
    )

    # Utilize the global variable within the function
    $global:accountsUserData += $membersList
    Write-Host "Adding data to: $($global:accountsUserData)"
    Write-Host "The memberlist: $($membersList)"
}

foreach ($file in $jsonFiles) {
    # Write the name of the file being processed to the screen
    Write-Host "Processing file: $($file.Name)"

    # Extract the server name from the file name
    $serverName = ($file.BaseName -split '-', 3)[-1]

    # Get the Server GUID from AD
    $computerObjectID = Get-ADComputer -Identity $serverName -Properties ObjectGUID

    # Read the content of the JSON file
    $jsonData = Get-Content -Path $file.FullName | ConvertFrom-Json

    # Group json data by GroupComponent
    $groupedData = $jsonData | Group-Object -Property GroupComponent

    # Process each group
    foreach ($group in $groupedData) {
        # Extract Group Name and Domain
        $groupDomain = ($group.Name -split 'Domain = "')[-1].Split('"')[0]
        $groupName = ($group.Name -split 'Name = "')[-1].Split('"')[0]
        $membersList = @()
        $isLocalGroup = $groupDomain -eq $serverName
        $groupObjectId = $null

        foreach ($item in $group.Group) {
            # It's a user account or group, process accordingly
            $partDomain = ($item.PartComponent -split 'Domain = "')[-1].Split('"')[0]
            $partName = ($item.PartComponent -split 'Name = "')[-1].Split('"')[0]
            $isLocalUserOrGroup = $partDomain -eq $serverName

            if ($item.PartComponent -like '*Win32_UserAccount*') {
                if ($isLocalUserOrGroup) {
                    # This is a local user, generate a GUID and create an entry
                    $combinedName = $serverName + $partName
                    # Generate the deterministic GUID
                    $deterministicGuid = New-DeterministicGuid -Name $combinedName -Namespace $namespaceGuid
                    $guid = [guid]$deterministicGuid
                    $membersList += [PSCustomObject]@{
                        uniqueId = $guid
                        originId = $guid
                        name = $partName
                        email = $null
                        description = "Local account" # Static description, adjust as needed
                        firstName = $partName # Assuming you have a GivenName attribute
                        lastName = $null # Assuming you have a Surname attribute
                        tags = "LocalUser"
                    }

                } else {
                    # Collect user details from Active Directory
                    $userDetails = Get-ADUser -Filter "SamAccountName -eq '$partName'" -Properties DisplayName, Mail, ObjectGUID -ErrorAction SilentlyContinue
                    if ($userDetails) {
                        $membersList += [PSCustomObject]@{
                            uniqueId = $userDetails.ObjectGUID
                            originId = $userDetails.ObjectGUID
                            name = $userDetails.SamAccountName
                            email = $userDetails.Mail
                            description = "User account" # Static description, adjust as needed
                            firstName = $userDetails.GivenName # Assuming you have a GivenName attribute
                            lastName = $userDetails.Surname # Assuming you have a Surname attribute
                            tags = "Users"
                        }
                    } else {
                        # Add basic details with null values for properties we can't get since Get-ADUser failed
                        $membersList += [PSCustomObject]@{
                            uniqueId = $partName
                            originId = $partName
                            name = $partName
                            email = $null
                            description = "No AD" # Static description, adjust as needed
                            firstName = $null 
                            lastName = $null  
                            tags = "Users"
                        }
                    }
                    
                }
                

            } elseif ($item.PartComponent -like '*Win32_Group*') {
                if ($isLocalUserOrGroup) {
                    $combinedName = $serverName + $partName
                    # Generate the deterministic GUID
                    $deterministicGuid = New-DeterministicGuid -Name $combinedName -Namespace $namespaceGuid
                    $guid = [guid]$deterministicGuid
                    $membersList += [PSCustomObject]@{
                            uniqueId = $guid
                            originId = $guid
                            name = $partName
                            type = 'Group'
                            tags = 'LocalGroup'
                    }
                } else {
                    # Find group in Active Directory
                    $adGroupMember = Get-ADGroup -Filter "Name -eq '$partName'" -Properties ObjectGUID -ErrorAction SilentlyContinue
                    if ($adGroupMember) {
                        $membersList += [PSCustomObject]@{
                            ObjectGUID = $adGroupMember.ObjectGUID
                            uniqueId = $adGroupMember.ObjectGUID
                            originId = $adGroupMember.ObjectGUID
                            name = $adGroupMember.Name
                            type = 'Group'
                            tags = 'Group'
                        }
                    }
                }
            }
        }

        # If the group is a local group, generate a  GUID
        if ($isLocalGroup) {
            $combinedName = $serverName + $groupName
            # Generate the deterministic GUID
            $deterministicGuid = New-DeterministicGuid -Name $combinedName -Namespace $namespaceGuid
            $groupObjectId = [guid]$deterministicGuid
        }
        # If the group is a domain group, get its ObjectGUID
        if (-not $isLocalGroup) {
            $groupObjectId = (Get-ADGroup -Filter "Name -eq '$groupName'" -Properties ObjectGUID -ErrorAction SilentlyContinue).ObjectGUID
        }

        # Construct the output object
        $output = [PSCustomObject]@{
            ServerName = $serverName
            ServerObjectGUID = $computerObjectID.ObjectGUID
            GroupDomain = $groupDomain
            GroupName = $groupName
            GroupObjectId = $groupObjectId
            alternativeName =  $null
            name = $groupName
            type = "Group"
            originId = $groupObjectId
            originType =  "Local"
            uniqueId = $groupObjectId
            Members = $membersList
        }



        #=========================================================================
        Write-Host "Working USER ACCOUNTS"
        #!!!!!WORKING THROUGH USER ACCOUNTS!!!!
        # Construct the final object with 'data' as the root property
        $UserAccounts = [PSCustomObject]@{
            data = @($output.Members)
        }

        # Convert the final object to JSON (Ready to call API)
        $UserAccountsjsonOutput = $UserAccounts | ConvertTo-Json -Depth 3 # Adjust the depth as necessary

        # Output the JSON string to the screen
        # Write-Output $UserAccountsjsonOutput

        # Output the object to the screen
        Write-Output $output


        # Initialize an array to hold the group memberships
        $UserAccMemberships = @()

        # Iterate through each member
        foreach ($member in $output.Members) {
            # Check if the member's type is NOT 'Group' before processing
            if ($member.type -ne 'Group') {
                # Member is not of type 'Group', process as needed
                $UserAccMembership = [PSCustomObject]@{
                    uniqueId    = $member.uniqueId
                    originId    = $member.originId
                    name        = $member.name
                    email       = $member.email
                    description = $member.description
                    firstName   = $member.firstName
                    lastName    = $member.lastName
                    tags        = $member.tags
                }
                # Add the new custom object to the array
                $UserAccMemberships += $UserAccMembership
            }
            # If the member is of type 'Group', it will be skipped and not included in the $groupMemberships array
        }

        $UserAccData = [PSCustomObject]@{
            data = @($UserAccMemberships)
        }

        # Convert the group memberships array to JSON
        $jsonOutput = $UserAccData | ConvertTo-Json -Depth 3

        # Output the JSON string to the screen or a file - This is the Accounts to go create API
        Write-Output $jsonOutput

        #=========================================================================
        #!!!!!WORKING THROUGH CREATING GROUP!!!!
        # Construct the final object with 'data' as the root property
        Write-Host "Working CREATING GROUP"
        
        # Construct a new object with only the desired properties
        $selectedProperties = [PSCustomObject]@{  
            alternativeName = $null
            name = $output.GroupName
            type = "Group"
            originId = $output.GroupObjectId
            originType = "Local"
            uniqueId = $output.GroupObjectId
        }
        
        $GroupData = [PSCustomObject]@{
            data = @($selectedProperties)
        }

        # Convert the new object to a JSON string
        $GroupDatajsonOutput = $GroupData | ConvertTo-Json -Depth 3

        # Output the JSON string to the console
        Write-Output $GroupDatajsonOutput

         #=========================================================================
        #!!!!!USER GROUP ASSOCIATION!!!!
        # Construct the final object with 'data' as the root property
        # Iterate through each member
        Write-Host "Working USER GROUP ASSOCIATION"

        # Initialize an array to hold the relationships
        $UserGrpAssociations = @()
        
        foreach ($member in $output.Members) {
            # Check if the member's type is NOT 'Group' before processing
            if ($member.type -ne 'Group') {
                # Member is not of type 'Group', process as needed
                $UserGrpAssociation = [PSCustomObject]@{
                    sourceId    = $member.originId
                    targetId    = $output.GroupObjectId
                }
                # Add the new custom object to the array
                $UserGrpAssociations += $UserGrpAssociation
            }
            # If the member is of type 'Group', it will be skipped and not included in the $groupMemberships array
        }
        $UserGrpData = [PSCustomObject]@{
            data = @($UserGrpAssociations)
        }

        # Convert the group memberships array to JSON
        $jsonOutput = $UserGrpData | ConvertTo-Json -Depth 3

        # Output the JSON string to the screen or a file - This is the Accounts to go create API
        
        Write-Output $jsonOutput


        #=========================================================================
        #!!!!!WORKING THROUGH ASSOCIATING GROUP WITH GROUP ACCOUNT!!!!
        # Convert JSON string back to object
        Write-Host "Working ASSOCIATING GROUP WITH GROUP"
        # Initialize an array to hold the relationships
        $groupMemberships = @()
        
        foreach ($member in $output.Members) {
            # Check if the member's type is NOT 'Group' before processing
            if ($member.type -eq 'Group') {
                # Member is of type 'Group', process as needed
                $groupMembership = [PSCustomObject]@{
                    sourceId    = $member.originId
                    targetId    = $output.GroupObjectId
                }
                # Add the new custom object to the array
                $groupMemberships += $groupMembership
            }
            # If the member is of type 'Group', it will be skipped and not included in the $groupMemberships array
        }
        $GrpMbrData = [PSCustomObject]@{
            data = @($groupMemberships)
        }
        # Convert the group memberships array to JSON
        $jsonOutput = $GrpMbrData | ConvertTo-Json -Depth 3

        # Output the JSON string to the screen or a file - This is the Accounts to go create API
        
        Write-Output $jsonOutput


        #=========================================================================
        #!!!!!MAKE API CALLS FOR EACH FILE!!!!

        # Convert JSON string back to object
        # API Calls after this point.
        # Prepare your JSON data
        #$jsonData = "your JSON string here"

        # Call the function to send the JSON to the API
        #$statusCode = Send-JsonToAPI -JsonData $jsonData

        # Output the status code (whether success or error)
        #Write-Host "API call finished with status code: $statusCode"
        



    }

    # Move the processed file to the 'processed' directory
    Move-Item -Path $file.FullName -Destination $processedDirectory
}

