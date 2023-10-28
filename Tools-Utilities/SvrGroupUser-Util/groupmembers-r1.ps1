# Wriiten by Authomize
# email: support@authomize.com for additional help or information
# 
#
#Get Administrative Groups and Users
#Global Variable
$global:extractedUserDomain = ""

# Input parameters for API - TBD
# $authomizeToken = "YOUR_AUTHOMIZE_TOKEN" # will be used when we implement API
# $connectorID = "YOUR_CONNECTOR_ID" # will be used when we implement API

# Read server names from a file (comma-delimited)
# List of servers to collect data from
$serversFilePath = "ServerNames.txt" # Update with your file path
$servers = (Get-Content $serversFilePath) -split "," | ForEach-Object { $_.Trim() }

# Log file path
$logFilePath = Join-Path -Path $PSScriptRoot -ChildPath "CollectionLog.txt"

#Check subdirectory exists for JSON processing
$subDirectory = "JSONProcessing"
if (-not (Test-Path $subDirectory)) {
    New-Item -Path $subDirectory -ItemType Directory
}

# Fuction to log messages
function LogMessage {
    param (
        [string]$message,
        [bool]$success = $true
    )
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] $($message)"
    if ($success) {
        Write-Output $logEntry
    } else {
        Write-Error $logEntry
    }
    Add-Content -Path $logFilePath -Value $logEntry
}


# Function to collect group members data
function CollectGroupMembers {
    param (
        [string]$computerName,
        [string]$theFilter
    )

    $dataset = @()

    # Use Get-CimInstance instead of Get-WmiObject
    $groupMembers = Get-CimInstance -ComputerName $computerName -ClassName Win32_GroupUser -Filter $theFilter


        foreach ($member in $groupMembers) {
            # Parse the Group information
            $groupInfo = $member.GroupComponent -match 'Win32_Group \(Domain = "(.+)", Name = "(.+)"\)'
            $groupDomain = $matches[1]
            $groupName = $matches[2]

            # Try to parse as UserAccount first
            $userInfo = $member.PartComponent -match 'Win32_UserAccount \(Domain = "(.+)", Name = "(.+)"\)'
    
            if ($userInfo) {
                $userDomain = $matches[1]
                $userName = $matches[2]
                $partComponentString = "Win32_UserAccount (Domain = `"$userDomain`", Name = `"$userName`")"
            } else {
                # If not a UserAccount, try to parse as Group
                $groupInfo = $member.PartComponent -match 'Win32_Group \(Domain = "(.+)", Name = "(.+)"\)'
                if ($groupInfo) {
                    $userDomain = $matches[1]
                    $userName = $matches[2]
                    $partComponentString = "Win32_Group (Domain = `"$userDomain`", Name = `"$userName`")"
                } else {
                    # Default to a placeholder if neither match
                    $partComponentString = "Unknown"
                }
            }

            # Create a custom object
            $obj = [PSCustomObject]@{
                GroupComponent = "Win32_Group (Domain = `"$groupDomain`", Name = `"$groupName`")"
                PartComponent  = $partComponentString
                PSComputerName = $member.PSComputerName
            }

            # Check if the PartComponent's Name is "Domain Admins"
            if ($obj.PartComponent -like '*Name = "Domain Admins"*') {
                # Extract the domain
                if ($obj.PartComponent -match 'Domain = "(.+?)",') {
                    # Store the domain in a global variable
                    $global:extractedUserDomain = $matches[1]
                }
            }

            # Add the custom object to the dataset
            $dataset += $obj

    }

    return $dataset

} #Function End


# Loop through each server and collect data
foreach ($remoteServer in $servers) {
    try {
        # First call
        $groupFilter1 = "GroupComponent=""Win32_Group.Domain='$($remoteServer)',Name='Administrators'"""
        $groupMembers1 = CollectGroupMembers -computerName $remoteServer -theFilter $groupFilter1

        # Second call
        $groupFilter2 = "GroupComponent=""Win32_Group.Domain='$($global:extractedUserDomain)',Name='Domain Admins'"""
        $groupMembers2 = CollectGroupMembers -computerName $remoteServer -theFilter $groupFilter2

        # Combine the results
        $allGroupMembers = $groupMembers1 + $groupMembers2

        if ($allGroupMembers.Count -gt 0) {            
            # Write combined data to JSON file
            $jsonData = $allGroupMembers | ConvertTo-Json
            $timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
            $pathWithSubDir = Join-Path -Path $PSScriptRoot -ChildPath $subDirectory
            $jsonFileName = "$timestamp-$remoteServer.json"
            $jsonFilePath = Join-Path -Path $pathWithSubDir -ChildPath $jsonFileName
            $jsonData | Set-Content -Path $jsonFilePath

            # Data Written
            LogMessage "Group members data collected from server $remoteServer"
        } else {
            # No group members data found
            LogMessage "No group members data found on server $remoteServer" -success $false
        }
    } catch [Microsoft.Management.Infrastructure.CimException] {
        # Handle error related to CIM cmdlets
        LogMessage "CIM error on server $remoteServer. Error: $($_.Exception.Message)" -success $false
    } catch [System.Management.Automation.Remoting.PSRemotingTransportException] {
        # Handle specific error related to WinRM connection
        LogMessage "Failed to connect to server $remoteServer. Error: $($_.Exception.Message)" -success $false
    } catch {
        # Handle other errors
        LogMessage "Error: $($_.Exception.Message)" -success $false
    }
}





# Save the collected data to a JSON rest point or blob
# Example of how to send data to a REST endpoint using Invoke-RestMethod:
# $uri = "https://authomize.com/restAPI"
# $headers = @{
#     "Authorization" = "Bearer $authomizeToken"
# }
# Invoke-RestMethod -Uri $uri -Method Post -Headers $headers -ContentType "application/json" -Body $jsonData
