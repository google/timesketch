/*
Copyright 2022 Google Inc. All rights reserved.
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at
    http://www.apache.org/licenses/LICENSE-2.0
Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
*/

try {
    var ruleUuid = crypto.randomUUID()
} catch (e) {
    console.log('crypto.randomUUID() not supported, using a fixed value instead')
    ruleUuid = '10a4fb8c-29d5-4eb6-905f-13d6a553d470'
}

// General first part of every Sigma rule:
const SkeletonFirst = `title: SigmaRuleTemplateTitle
id: ${ruleUuid}
description: Detects suspicious activity
references:
  - https://
author: Timesketch
date: ${new Date(Date.now()).toLocaleString('en-ZA').split(',')[0]}
modified: ${new Date(Date.now()).toLocaleString('en-ZA').split(',')[0]}
status: experimental
falsepositives: unknown
level: informational
tags:
    - attack.defense_evasion`

// General last part of every Sigma rule:
const SkeletonLast = `falsepositives:
    - Unknown
status: experimental
level: medium
detection:
    keywords:
        - '*foobar*'
    condition: keywords`

// CLOUD:
const AwsText = `${SkeletonFirst}
logsource:
    product: aws
    service: cloudtrail
${SkeletonLast}
`

const AzureActivitylogsText = `${SkeletonFirst}
logsource:
    product: azure
    service: activitylogs
${SkeletonLast}
`

const AzureSigninlogsText = `${SkeletonFirst}
logsource:
    product: azure
    service: signinlogs
${SkeletonLast}
`
const GCPAuditlogsText = `${SkeletonFirst}
logsource:
    product: gcp
    service: gcp.audit
${SkeletonLast}
`

const GworkspaceText = `${SkeletonFirst}
logsource:
    product: google_workspace
    service: google_workspace.admin
${SkeletonLast}
`

const Microsoft365Text = `${SkeletonFirst}
logsource:
    product: m365
    service: threat_management
${SkeletonLast}
`

const OktaText = `${SkeletonFirst}
logsource:
    product: okta
    service: okta
${SkeletonLast}
`

// LINUX:
const LinuxFileCreateText = `${SkeletonFirst}
logsource:
    category: file_create
    product: linux
${SkeletonLast}
`

const LinuxNetworkConnectionText = `${SkeletonFirst}
logsource:
    category: network_connection
    product: linux
${SkeletonLast}
`

const LinuxProcessCreationText = `${SkeletonFirst}
logsource:
    category: process_creation
    product: linux
${SkeletonLast}
`

const LinuxAnyLogsText = `${SkeletonFirst}
logsource:
    product: linux
${SkeletonLast}
`

const LinuxAuditdText = `${SkeletonFirst}
logsource:
    category: auditd
    product: linux
${SkeletonLast}
`

const LinuxClamavText = `${SkeletonFirst}
logsource:
    category: clamav
    product: linux
${SkeletonLast}
`
const LinuxCronText = `${SkeletonFirst}
logsource:
    category: cron
    product: linux
${SkeletonLast}
`
const LinuxGuacamoleText = `${SkeletonFirst}
logsource:
    category: guacamole
    product: linux
${SkeletonLast}
`
const LinuxModsecurityText = `${SkeletonFirst}
logsource:
    category: modsecurity
    product: linux
${SkeletonLast}
`
const LinuxSudoText = `${SkeletonFirst}
logsource:
    category: sudo
    product: linux
${SkeletonLast}
`
const LinuxSshdText = `${SkeletonFirst}
logsource:
    category: sshd
    product: linux
${SkeletonLast}
`
const LinuxSyslogText = `${SkeletonFirst}
logsource:
    category: syslog
    product: linux
${SkeletonLast}
`

const LinuxVsftpdText = `${SkeletonFirst}
logsource:
    category: vsftpd
    product: linux
${SkeletonLast}
`

// MAC OS
const MacosFileeventText = `${SkeletonFirst}
logsource:
    category: file_event
    product: macos
${SkeletonLast}
`

const MacosProcessCreationText = `${SkeletonFirst}
logsource:
    category: process_creation
    product: macos
${SkeletonLast}
`

const WindowsClipboardCaptureText = `${SkeletonFirst}
logsource:
    category: clipboard_capture
    product: windows
${SkeletonLast}
`

const WindowsCreateRemoteThreadText = `${SkeletonFirst}
logsource:
    category: create_remote_thread
    product: windows
${SkeletonLast}
`

const WindowsCreateStreamHashText = `${SkeletonFirst}
logsource:
    category: create_stream_hash
    product: windows
${SkeletonLast}
`

const WindowsDnsQueryText = `${SkeletonFirst}
logsource:
    category: dns_query
    product: windows
${SkeletonLast}
`

const WindowsDriverLoadText = `${SkeletonFirst}
logsource:
    category: driver_load
    product: windows
${SkeletonLast}
`

const WindowsFileChangeText = `${SkeletonFirst}
logsource:
    category: file_change
    product: windows
${SkeletonLast}
`

const WindowsFileDeleteText = `${SkeletonFirst}
logsource:
    category: file_delete
    product: windows
${SkeletonLast}
`

const WindowsFileEventText = `${SkeletonFirst}
logsource:
    category: file_event
    product: windows
${SkeletonLast}
`

const WindowsImageLoadText = `${SkeletonFirst}
logsource:
    category: image_load
    product: windows
${SkeletonLast}
`

const WindowsNetworkConnectionText = `${SkeletonFirst}
logsource:
    category: network_connection
    product: windows
${SkeletonLast}
`

const WindowsPipeCreatedText = `${SkeletonFirst}
logsource:
    category: pipe_created
    product: windows
${SkeletonLast}
`

const WindowsProcessAccessText = `${SkeletonFirst}
logsource:
    category: process_access
    product: windows
${SkeletonLast}
`

const WindowsProcessCreationText = `${SkeletonFirst}
logsource:
    category: process_creation
    product: windows
${SkeletonLast}
`

const WindowsProcessTamperingText = `${SkeletonFirst}
logsource:
    category: process_tampering
    product: windows
${SkeletonLast}
`

const WindowsProcessTerminationText = `${SkeletonFirst}
logsource:
    category: process_termination
    product: windows
${SkeletonLast}
`

const WindowsPsClassicProviderStartText = `${SkeletonFirst}
logsource:
    category: ps_classic_provider_start
    product: windows
${SkeletonLast}
`

const WindowsPsClassicScriptText = `${SkeletonFirst}
logsource:
    category: ps_classic_script
    product: windows
${SkeletonLast}
`

const WindowsPsClassicStartText = `${SkeletonFirst}
logsource:
    category: ps_classic_start
    product: windows
${SkeletonLast}
`

const WindowsPsModuleText = `${SkeletonFirst}
logsource:
    category: ps_module
    product: windows
${SkeletonLast}
`

const WindowsPsScriptText = `${SkeletonFirst}
logsource:
    category: ps_script
    product: windows
${SkeletonLast}
`

const WindowsRawAccessThreadText = `${SkeletonFirst}
logsource:
    category: raw_access_thread
    product: windows
${SkeletonLast}
`

const WindowsRegistryAddText = `${SkeletonFirst}
logsource:
    category: registry_add
    product: windows
${SkeletonLast}
`

const WindowsRegistryDeleteText = `${SkeletonFirst}
logsource:
    category: registry_delete
    product: windows
${SkeletonLast}
`

const WindowsRegistryEventText = `${SkeletonFirst}
logsource:
    category: registry_event
    product: windows
${SkeletonLast}
`

const WindowsRegistryRenameText = `${SkeletonFirst}
logsource:
    category: registry_rename
    product: windows
${SkeletonLast}
`

const WindowsRegistrySetText = `${SkeletonFirst}
logsource:
    category: registry_set
    product: windows
${SkeletonLast}
`

const WindowsSysmonErrorText = `${SkeletonFirst}
logsource:
    category: sysmon_error
    product: windows
${SkeletonLast}
`

const WindowsSysmonStatusText = `${SkeletonFirst}
logsource:
    category: sysmon_status
    product: windows
${SkeletonLast}
`

const WindowsWmiEventText = `${SkeletonFirst}
logsource:
    category: wmi_event
    product: windows
${SkeletonLast}
`

const WindowsApplicationText = `${SkeletonFirst}
logsource:
    service: application
    product: windows
${SkeletonLast}
`

const WindowsApplockerText = `${SkeletonFirst}
logsource:
    service: applocker
    product: windows
${SkeletonLast}
`

const WindowsBitsclientText = `${SkeletonFirst}
logsource:
    service: bits-client
    product: windows
${SkeletonLast}
`

const WindowsCodeintegrityoperationalText = `${SkeletonFirst}
logsource:
    service: codeintegrity-operational
    product: windows
${SkeletonLast}
`
const WindowsDhcpText = `${SkeletonFirst}
logsource:
    service: dhcp
    product: windows
${SkeletonLast}
`
const WindowsDnsserverText = `${SkeletonFirst}
logsource:
    service:  dns-server
    product: windows
${SkeletonLast}
`
const WindowsDriverframeworkText = `${SkeletonFirst}
logsource:
    service: driver-framework
    product: windows
${SkeletonLast}
`
const WindowsFirewallasText = `${SkeletonFirst}
logsource:
    service: firewall-as
    product: windows
${SkeletonLast}
`
const WindowsLdapDebugText = `${SkeletonFirst}
logsource:
    service:  ldap_debug
    product: windows
${SkeletonLast}
`
const WindowsMicrosoftservicebusclientText = `${SkeletonFirst}
logsource:
    service: microsoft-servicebus-client
    product: windows
${SkeletonLast}
`
const WindowsMsexchangemanagementText = `${SkeletonFirst}
logsource:
    service: msexchange-management
    product: windows
${SkeletonLast}
`
const WindowsNtlmText = `${SkeletonFirst}
logsource:
    service: ntlm
    product: windows
${SkeletonLast}
`
const WindowsPowershellText = `${SkeletonFirst}
logsource:
    service: powershell
    product: windows
${SkeletonLast}
`
const WindowsPowershellclassicText = `${SkeletonFirst}
logsource:
    service: powershell-classic
    product: windows
${SkeletonLast}
`
const WindowsPrintserviceadminText = `${SkeletonFirst}
logsource:
    service: printservice-admin
    product: windows
${SkeletonLast}
`
const WindowsPrintserviceoperationalText = `${SkeletonFirst}
logsource:
    service: printservice-operational
    product: windows
${SkeletonLast}
`
const WindowsSecurityText = `${SkeletonFirst}
logsource:
    service: security
    product: windows
${SkeletonLast}
`
const WindowsSecuritymitigationsText = `${SkeletonFirst}
logsource:
    service: security-mitigations
    product: windows
${SkeletonLast}
`
const WindowsSmbclientsecurityText = `${SkeletonFirst}
logsource:
    service: smbclient-security
    product: windows
${SkeletonLast}
`
const WindowsSysmonText = `${SkeletonFirst}
logsource:
    service: sysmon
    product: windows
${SkeletonLast}
`
const WindowsSystemText = `${SkeletonFirst}
logsource:
    service: system
    product: windows
${SkeletonLast}
`
const WindowsTaskschedulerText = `${SkeletonFirst}
logsource:
    service: taskscheduler
    product: windows
${SkeletonLast}
`
const WindowsTerminalservicesText = `${SkeletonFirst}
logsource:
    service: terminalservices
    product: windows
${SkeletonLast}
`
const WindowsWindefendText = `${SkeletonFirst}
logsource:
    service: windefend
    product: windows
${SkeletonLast}
`
const WindowsWmiText = `${SkeletonFirst}
logsource:
    service: wmi
    product: windows
${SkeletonLast}
`

const defaultSigmaPlaceholder = `${SkeletonFirst}
${SkeletonLast}
`

const SigmaTemplates = [
    { "os": "General", "title": "Default template", "text": defaultSigmaPlaceholder },
    { "os": "Cloud", "title": "Cloud: AWS", "text": AwsText },
    { "os": "Cloud", "title": "Cloud: Azure_activitylogs", "text": AzureActivitylogsText },
    { "os": "Cloud", "title": "Cloud: Azure_signinlogs", "text": AzureSigninlogsText },
    { "os": "Cloud", "title": "Cloud: GCP Audit logs", "text": GCPAuditlogsText },
    { "os": "Cloud", "title": "Cloud: GWorkspace", "text": GworkspaceText },
    { "os": "Cloud", "title": "Cloud: Microsoft 365", "text": Microsoft365Text },
    { "os": "Cloud", "title": "Cloud: Okta", "text": OktaText },
    { "os": "Linux", "title": "Linux: File create", "text": LinuxFileCreateText },
    { "os": "Linux", "title": "Linux: Network connection", "text": LinuxNetworkConnectionText },
    { "os": "Linux", "title": "Linux: Process creation", "text": LinuxProcessCreationText },
    { "os": "Linux", "title": "Linux: Any logs", "text": LinuxAnyLogsText },
    { "os": "Linux", "title": "Linux: AuditD", "text": LinuxAuditdText },
    { "os": "Linux", "title": "Linux: ClamAV", "text": LinuxClamavText },
    { "os": "Linux", "title": "Linux: CRON", "text": LinuxCronText },
    { "os": "Linux", "title": "Linux: Guacamole", "text": LinuxGuacamoleText },
    { "os": "Linux", "title": "Linux: Modseurity", "text": LinuxModsecurityText },
    { "os": "Linux", "title": "Linux: sudo", "text": LinuxSudoText },
    { "os": "Linux", "title": "Linux: sshd", "text": LinuxSshdText },
    { "os": "Linux", "title": "Linux: syslog", "text": LinuxSyslogText },
    { "os": "Linux", "title": "Linux: VSFTPD", "text": LinuxVsftpdText },
    { "os": "MacOS", "title": "MacOS: file_event", "text": MacosFileeventText },
    { "os": "MacOS", "title": "MacOS: process_creation", "text": MacosProcessCreationText },
    { "os": "Windows", "title": "Windows: clipboard_capture", "text": WindowsClipboardCaptureText },
    { "os": "Windows", "title": "Windows: create_remote_thread", "text": WindowsCreateRemoteThreadText }, // 54
    { "os": "Windows", "title": "Windows: create_stream_hash", "text": WindowsCreateStreamHashText },
    { "os": "Windows", "title": "Windows: dns_query", "text": WindowsDnsQueryText },
    {
        "os": "Windows", "title": "Windows: driver_load", "text": WindowsDriverLoadText
    },
    { "os": "Windows", "title": "Windows: file_change", "text": WindowsFileChangeText },
    { "os": "Windows", "title": "Windows: file_delete", "text": WindowsFileDeleteText },
    { "os": "Windows", "title": "Windows: file_event", "text": WindowsFileEventText },
    { "os": "Windows", "title": "Windows: image_load", "text": WindowsImageLoadText },
    { "os": "Windows", "title": "Windows: network_connection", "text": WindowsNetworkConnectionText },
    { "os": "Windows", "title": "Windows: pipe_created", "text": WindowsPipeCreatedText },
    { "os": "Windows", "title": "Windows: process_access", "text": WindowsProcessAccessText },
    { "os": "Windows", "title": "Windows: process_creation", "text": WindowsProcessCreationText },
    { "os": "Windows", "title": "Windows: process_tampering", "text": WindowsProcessTamperingText },
    { "os": "Windows", "title": "Windows: process_termination", "text": WindowsProcessTerminationText },
    { "os": "Windows", "title": "Windows: ps_classic_provider_start", "text": WindowsPsClassicProviderStartText },
    { "os": "Windows", "title": "Windows: ps_classic_script", "text": WindowsPsClassicScriptText },
    { "os": "Windows", "title": "Windows: ps_classic_start", "text": WindowsPsClassicStartText },
    { "os": "Windows", "title": "Windows: ps_module", "text": WindowsPsModuleText },
    { "os": "Windows", "title": "Windows: ps_script", "text": WindowsPsScriptText },
    { "os": "Windows", "title": "Windows: raw_access_thread", "text": WindowsRawAccessThreadText },
    { "os": "Windows", "title": "Windows: registry_add", "text": WindowsRegistryAddText },
    { "os": "Windows", "title": "Windows: registry_delete", "text": WindowsRegistryDeleteText },
    { "os": "Windows", "title": "Windows: registry_event", "text": WindowsRegistryEventText },
    { "os": "Windows", "title": "Windows: registry_rename", "text": WindowsRegistryRenameText },
    { "os": "Windows", "title": "Windows: registry_set", "text": WindowsRegistrySetText },
    { "os": "Windows", "title": "Windows: sysmon_error", "text": WindowsSysmonErrorText },
    { "os": "Windows", "title": "Windows: sysmon_status", "text": WindowsSysmonStatusText },
    { "os": "Windows", "title": "Windows: wmi_event", "text": WindowsWmiEventText },
    { "os": "Windows", "title": "Windows: application", "text": WindowsApplicationText },
    { "os": "Windows", "title": "Windows: applocker", "text": WindowsApplockerText },
    { "os": "Windows", "title": "Windows: bits-client", "text": WindowsBitsclientText },
    { "os": "Windows", "title": "Windows: codeintegrity-operational", "text": WindowsCodeintegrityoperationalText },
    { "os": "Windows", "title": "Windows: dhcp", "text": WindowsDhcpText },
    { "os": "Windows", "title": "Windows: dns-server", "text": WindowsDnsserverText },
    { "os": "Windows", "title": "Windows: driver-framework", "text": WindowsDriverframeworkText },
    { "os": "Windows", "title": "Windows: firewall-as", "text": WindowsFirewallasText },
    { "os": "Windows", "title": "Windows: ldap_debug", "text": WindowsLdapDebugText },
    { "os": "Windows", "title": "Windows: microsoft-servicebus-client", "text": WindowsMicrosoftservicebusclientText },
    { "os": "Windows", "title": "Windows: msexchange-management", "text": WindowsMsexchangemanagementText },
    { "os": "Windows", "title": "Windows: ntlm", "text": WindowsNtlmText },
    { "os": "Windows", "title": "Windows: powershell", "text": WindowsPowershellText },
    { "os": "Windows", "title": "Windows: powershell-classic", "text": WindowsPowershellclassicText },
    { "os": "Windows", "title": "Windows: printservice-admin", "text": WindowsPrintserviceadminText },
    { "os": "Windows", "title": "Windows: printservice-operational", "text": WindowsPrintserviceoperationalText },
    { "os": "Windows", "title": "Windows: security", "text": WindowsSecurityText },
    { "os": "Windows", "title": "Windows: security-mitigations", "text": WindowsSecuritymitigationsText },
    { "os": "Windows", "title": "Windows: smbclient-security", "text": WindowsSmbclientsecurityText },
    { "os": "Windows", "title": "Windows: sysmon", "text": WindowsSysmonText },
    { "os": "Windows", "title": "Windows: system", "text": WindowsSystemText },
    { "os": "Windows", "title": "Windows: taskscheduler", "text": WindowsTaskschedulerText },
    { "os": "Windows", "title": "Windows: terminalservices", "text": WindowsTerminalservicesText },
    { "os": "Windows", "title": "Windows: windefend", "text": WindowsWindefendText },
    { "os": "Windows", "title": "Windows: wmi", "text": WindowsWmiText },


]


export { SigmaTemplates, defaultSigmaPlaceholder }