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

// General first part of every Sigma rule:
const SkeletonFirst = `title: Foobar
id: ${crypto.randomUUID()}
description: Detects suspicious FOOBAR
references:
  - https://
author: 
date: ${new Date(Date.now()).toLocaleString('en-ZA').split(',')[0]}
modified: ${new Date(Date.now()).toLocaleString('en-ZA').split(',')[0]}
tags:
    -`

// General last part of every Sigma rule:
const SkeletonLast = `falsepositives:
    - Unknown
status: experimental // stable, test, experimental, deprecated, unsupported
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

const Okta_text = `${SkeletonFirst}
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
const Linux_syslog_text = `${SkeletonFirst}
logsource:
    category: syslog
    product: linux
${SkeletonLast}
`

const Linux_vsftpd_text = `${SkeletonFirst}
logsource:
    category: vsftpd
    product: linux
${SkeletonLast}
`

// MAC OS
const Macos_file_event_text = `${SkeletonFirst}
logsource:
    category: file_event
    product: macos
${SkeletonLast}
`

const Macos_process_creation_text = `${SkeletonFirst}
logsource:
    category: process_creation
    product: macos
${SkeletonLast}
`

const Windows_clipboard_capture_text = `${SkeletonFirst}
logsource:
    category: clipboard_capture
    product: windows
${SkeletonLast}
`

const Windows_create_remote_thread_text = `${SkeletonFirst}
logsource:
    category: create_remote_thread
    product: windows
${SkeletonLast}
`

const Windows_create_stream_hash_text = `${SkeletonFirst}
logsource:
    category: create_stream_hash
    product: windows
${SkeletonLast}
`

const Windows_dns_query_text = `${SkeletonFirst}
logsource:
    category: dns_query
    product: windows
${SkeletonLast}
`

const Windows_driver_load_text = `${SkeletonFirst}
logsource:
    category: driver_load
    product: windows
${SkeletonLast}
`

const Windows_file_change_text = `${SkeletonFirst}
logsource:
    category: file_change
    product: windows
${SkeletonLast}
`

const Windows_file_delete_text = `${SkeletonFirst}
logsource:
    category: file_delete
    product: windows
${SkeletonLast}
`

const Windows_file_event_text = `${SkeletonFirst}
logsource:
    category: file_event
    product: windows
${SkeletonLast}
`

const Windows_image_load_text = `${SkeletonFirst}
logsource:
    category: image_load
    product: windows
${SkeletonLast}
`

const Windows_network_connection_text = `${SkeletonFirst}
logsource:
    category: network_connection
    product: windows
${SkeletonLast}
`

const Windows_pipe_created_text = `${SkeletonFirst}
logsource:
    category: pipe_created
    product: windows
${SkeletonLast}
`

const Windows_process_access_text = `${SkeletonFirst}
logsource:
    category: process_access
    product: windows
${SkeletonLast}
`

const Windows_process_creation_text = `${SkeletonFirst}
logsource:
    category: process_creation
    product: windows
${SkeletonLast}
`

const Windows_process_tampering_text = `${SkeletonFirst}
logsource:
    category: process_tampering
    product: windows
${SkeletonLast}
`

const Windows_process_termination_text = `${SkeletonFirst}
logsource:
    category: process_termination
    product: windows
${SkeletonLast}
`

const Windows_ps_classic_provider_start_text = `${SkeletonFirst}
logsource:
    category: ps_classic_provider_start
    product: windows
${SkeletonLast}
`

const Windows_ps_classic_script_text = `${SkeletonFirst}
logsource:
    category: ps_classic_script
    product: windows
${SkeletonLast}
`

const Windows_ps_classic_start_text = `${SkeletonFirst}
logsource:
    category: ps_classic_start
    product: windows
${SkeletonLast}
`

const Windows_ps_module_text = `${SkeletonFirst}
logsource:
    category: ps_module
    product: windows
${SkeletonLast}
`

const Windows_ps_script_text = `${SkeletonFirst}
logsource:
    category: ps_script
    product: windows
${SkeletonLast}
`

const Windows_raw_access_thread_text = `${SkeletonFirst}
logsource:
    category: raw_access_thread
    product: windows
${SkeletonLast}
`

const Windows_registry_add_text = `${SkeletonFirst}
logsource:
    category: registry_add
    product: windows
${SkeletonLast}
`

const Windows_registry_delete_text = `${SkeletonFirst}
logsource:
    category: registry_delete
    product: windows
${SkeletonLast}
`

const Windows_registry_event_text = `${SkeletonFirst}
logsource:
    category: registry_event
    product: windows
${SkeletonLast}
`

const Windows_registry_rename_text = `${SkeletonFirst}
logsource:
    category: registry_rename
    product: windows
${SkeletonLast}
`

const Windows_registry_set_text = `${SkeletonFirst}
logsource:
    category: registry_set
    product: windows
${SkeletonLast}
`

const Windows_sysmon_error_text = `${SkeletonFirst}
logsource:
    category: sysmon_error
    product: windows
${SkeletonLast}
`

const Windows_sysmon_status_text = `${SkeletonFirst}
logsource:
    category: sysmon_status
    product: windows
${SkeletonLast}
`

const Windows_wmi_event_text = `${SkeletonFirst}
logsource:
    category: wmi_event
    product: windows
${SkeletonLast}
`

const Windows_application_text = `${SkeletonFirst}
logsource:
    service: application
    product: windows
${SkeletonLast}
`

const Windows_applocker_text = `${SkeletonFirst}
logsource:
    service: applocker
    product: windows
${SkeletonLast}
`

const Windows_bitsclient_text = `${SkeletonFirst}
logsource:
    service: bits-client
    product: windows
${SkeletonLast}
`

const Windows_codeintegrityoperational_text = `${SkeletonFirst}
logsource:
    service: codeintegrity-operational
    product: windows
${SkeletonLast}
`
const Windows_dhcp_text = `${SkeletonFirst}
logsource:
    service: dhcp
    product: windows
${SkeletonLast}
`
const Windows_dnsserver_text = `${SkeletonFirst}
logsource:
    service:  dns-server
    product: windows
${SkeletonLast}
`
const Windows_driverframework_text = `${SkeletonFirst}
logsource:
    service: driver-framework
    product: windows
${SkeletonLast}
`
const Windows_firewallas_text = `${SkeletonFirst}
logsource:
    service: firewall-as
    product: windows
${SkeletonLast}
`
const Windows_ldap_debug_text = `${SkeletonFirst}
logsource:
    service:  ldap_debug
    product: windows
${SkeletonLast}
`
const Windows_microsoftservicebusclient_text = `${SkeletonFirst}
logsource:
    service: microsoft-servicebus-client
    product: windows
${SkeletonLast}
`
const Windows_msexchangemanagement_text = `${SkeletonFirst}
logsource:
    service: msexchange-management
    product: windows
${SkeletonLast}
`
const Windows_ntlm_text = `${SkeletonFirst}
logsource:
    service: ntlm
    product: windows
${SkeletonLast}
`
const Windows_powershell_text = `${SkeletonFirst}
logsource:
    service: powershell
    product: windows
${SkeletonLast}
`
const Windows_powershellclassic_text = `${SkeletonFirst}
logsource:
    service: powershell-classic
    product: windows
${SkeletonLast}
`
const Windows_printserviceadmin_text = `${SkeletonFirst}
logsource:
    service: printservice-admin
    product: windows
${SkeletonLast}
`
const Windows_printserviceoperational_text = `${SkeletonFirst}
logsource:
    service: printservice-operational
    product: windows
${SkeletonLast}
`
const Windows_security_text = `${SkeletonFirst}
logsource:
    service: security
    product: windows
${SkeletonLast}
`
const Windows_securitymitigations_text = `${SkeletonFirst}
logsource:
    service: security-mitigations
    product: windows
${SkeletonLast}
`
const Windows_smbclientsecurity_text = `${SkeletonFirst}
logsource:
    service: smbclient-security
    product: windows
${SkeletonLast}
`
const Windows_sysmon_text = `${SkeletonFirst}
logsource:
    service: sysmon
    product: windows
${SkeletonLast}
`
const Windows_system_text = `${SkeletonFirst}
logsource:
    service: system
    product: windows
${SkeletonLast}
`
const Windows_taskscheduler_text = `${SkeletonFirst}
logsource:
    service: taskscheduler
    product: windows
${SkeletonLast}
`
const Windows_terminalservices_text = `${SkeletonFirst}
logsource:
    service: terminalservices
    product: windows
${SkeletonLast}
`
const Windows_windefend_text = `${SkeletonFirst}
logsource:
    service: windefend
    product: windows
${SkeletonLast}
`
const Windows_wmi_text = `${SkeletonFirst}
logsource:
    service: wmi
    product: windows
${SkeletonLast}
`

const SigmaTemplates = [
    { "os": "Cloud: AWS", "text": AwsText },
    { "os": "Cloud: Azure_activitylogs", "text": AzureActivitylogsText },
    { "os": "Cloud: Azure_signinlogs", "text": AzureSigninlogsText },
    { "os": "Cloud: GCP Audit logs", "text": GCPAuditlogsText },
    { "os": "Cloud: GWorkspace", "text": GworkspaceText },
    { "os": "Cloud: Microsoft 365", "text": Microsoft365Text },
    { "os": "Cloud: Okta", "text": Okta_text },
    { "os": "Linux: File create", "text": LinuxFileCreateText },
    { "os": "Linux: Network connection", "text": LinuxNetworkConnectionText },
    { "os": "Linux: Process creation", "text": LinuxProcessCreationText },
    { "os": "Linux: Any logs", "text": LinuxAnyLogsText },
    { "os": "Linux: AuditD", "text": LinuxAuditdText },
    { "os": "Linux: ClamAV", "text": LinuxClamavText },
    { "os": "Linux: CRON", "text": LinuxCronText },
    { "os": "Linux: Guacamole", "text": LinuxGuacamoleText },
    { "os": "Linux: Modseurity", "text": LinuxModsecurityText },
    { "os": "Linux: sudo", "text": LinuxSudoText },
    { "os": "Linux: sshd", "text": LinuxSshdText },
    { "os": "Linux: syslog", "text": Linux_syslog_text },
    { "os": "Linux: VSFTPD", "text": Linux_vsftpd_text },
    { "os": "MacOS: file_event", "text": Macos_file_event_text },
    { "os": "MacOS: process_creation", "text": Macos_process_creation_text },
    { "os": "Windows: clipboard_capture", "text": Windows_clipboard_capture_text },
    { "os": "Windows: create_remote_thread", "text": Windows_create_remote_thread_text }, // 54
    { "os": "Windows: create_stream_hash", "text": Windows_create_stream_hash_text },
    { "os": "Windows: dns_query", "text": Windows_dns_query_text },
    { "os": "Windows: driver_load", "text": Windows_driver_load_text },
    { "os": "Windows: file_change", "text": Windows_file_change_text },
    { "os": "Windows: file_delete", "text": Windows_file_delete_text },
    { "os": "Windows: file_event", "text": Windows_file_event_text },
    { "os": "Windows: image_load", "text": Windows_image_load_text },
    { "os": "Windows: network_connection", "text": Windows_network_connection_text },
    { "os": "Windows: pipe_created", "text": Windows_pipe_created_text },
    { "os": "Windows: process_access", "text": Windows_process_access_text },
    { "os": "Windows: process_creation", "text": Windows_process_creation_text },
    { "os": "Windows: process_tampering", "text": Windows_process_tampering_text },
    { "os": "Windows: process_termination", "text": Windows_process_termination_text },
    { "os": "Windows: ps_classic_provider_start", "text": Windows_ps_classic_provider_start_text },
    { "os": "Windows: ps_classic_script", "text": Windows_ps_classic_script_text },
    { "os": "Windows: ps_classic_start", "text": Windows_ps_classic_start_text },
    { "os": "Windows: ps_module", "text": Windows_ps_module_text },
    { "os": "Windows: ps_script", "text": Windows_ps_script_text },
    { "os": "Windows: raw_access_thread", "text": Windows_raw_access_thread_text },
    { "os": "Windows: registry_add", "text": Windows_registry_add_text },
    { "os": "Windows: registry_delete", "text": Windows_registry_delete_text },
    { "os": "Windows: registry_event", "text": Windows_registry_event_text },
    { "os": "Windows: registry_rename", "text": Windows_registry_rename_text },
    { "os": "Windows: registry_set", "text": Windows_registry_set_text },
    { "os": "Windows: sysmon_error", "text": Windows_sysmon_error_text },
    { "os": "Windows: sysmon_status", "text": Windows_sysmon_status_text },
    { "os": "Windows: wmi_event", "text": Windows_wmi_event_text },
    { "os": "Windows: application", "text": Windows_application_text },
    { "os": "Windows: applocker", "text": Windows_applocker_text },
    { "os": "Windows: bits-client", "text": Windows_bitsclient_text },
    { "os": "Windows: codeintegrity-operational", "text": Windows_codeintegrityoperational_text },
    { "os": "Windows: dhcp", "text": Windows_dhcp_text },
    { "os": "Windows: dns-server", "text": Windows_dnsserver_text },
    { "os": "Windows: driver-framework", "text": Windows_driverframework_text },
    { "os": "Windows: firewall-as", "text": Windows_firewallas_text },
    { "os": "Windows: ldap_debug", "text": Windows_ldap_debug_text },
    { "os": "Windows: msexchange-management", "text": Windows_msexchangemanagement_text },
    { "os": "Windows: ntlm", "text": Windows_ntlm_text },
    { "os": "Windows: powershell", "text": Windows_powershell_text },
    { "os": "Windows: powershell-classic", "text": Windows_powershellclassic_text },
    { "os": "Windows: printservice-admin", "text": Windows_printserviceadmin_text },
    { "os": "Windows: printservice-operational", "text": Windows_printserviceoperational_text },
    { "os": "Windows: security", "text": Windows_security_text },
    { "os": "Windows: security-mitigations", "text": Windows_securitymitigations_text },
    { "os": "Windows: smbclient-security", "text": Windows_smbclientsecurity_text },
    { "os": "Windows: sysmon", "text": Windows_sysmon_text },
    { "os": "Windows: system", "text": Windows_system_text },
    { "os": "Windows: taskscheduler", "text": Windows_taskscheduler_text },
    { "os": "Windows: terminalservices", "text": Windows_terminalservices_text },
    { "os": "Windows: windefend", "text": Windows_windefend_text },
    { "os": "Windows: wmi", "text": Windows_wmi_text },


]


export { SigmaTemplates }