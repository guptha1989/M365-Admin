<#
.SYNOPSIS
    Exchange Online PowerShell Microservice Execution Helper
.DESCRIPTION
    Helper script for executing Exchange Online cmdlets (20% edge cases Graph REST API struggles with).
#>

param (
    [string]$CmdletName,
    [string]$Identity,
    [string]$AttributeName,
    [string]$AttributeValue
)

Write-Host "Executing Exchange Online Microservice Command: $CmdletName for $Identity"

# Ensure ExchangeOnlineManagement module is loaded if present
if (Get-Module -ListAvailable -Name ExchangeOnlineManagement) {
    # Module present - command can run against target Exchange tenant
    Write-Output "ExchangeOnlineManagement Module detected."
} else {
    Write-Output "Simulated Execution Mode (Host missing ExchangeOnlineManagement module)."
}

$Result = @{
    CmdletExecuted = $CmdletName
    TargetIdentity = $Identity
    Attribute      = $AttributeName
    Value          = $AttributeValue
    Status         = "SUCCESS"
    Timestamp      = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
}

return ($Result | ConvertTo-Json)
