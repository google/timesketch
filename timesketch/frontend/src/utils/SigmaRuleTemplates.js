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
const skeleton_first = `title: Foobar
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
const skeleton_last = `falsepositives:
    - Unknown
status: experimental // stable, test, experimental, deprecated, unsupported
level: medium
detection:
    keywords:
        - '*foobar*'
    condition: keywords`

// CLOUD:
const aws_text = `${skeleton_first}
logsource:
    product: aws
    service: cloudtrail
${skeleton_last}
`

const Azure_activitylogs_text = `${skeleton_first}
logsource:
    product: azure
    service: activitylogs
${skeleton_last}
`

const Azure_signinlogs_text = `${skeleton_first}
logsource:
    product: azure
    service: signinlogs
${skeleton_last}
`
const GCP_auditlogs_text = `${skeleton_first}
logsource:
    product: gcp
    service: gcp.audit
${skeleton_last}
`

const Gworkspace_text = `${skeleton_first}
logsource:
    product: google_workspace
    service: google_workspace.admin
${skeleton_last}
`

const Microsoft365_text = `${skeleton_first}
logsource:
    product: m365
    service: threat_management
${skeleton_last}
`

const Okta_text = `${skeleton_first}
logsource:
    product: okta
    service: okta
${skeleton_last}
`

// LINUX:
const Linux_file_create_text = `${skeleton_first}
logsource:
    category: file_create
    product: linux
${skeleton_last}
`

const Linux_network_connection_text = `${skeleton_first}
logsource:
    category: network_connection
    product: linux
${skeleton_last}
`

const Linux_process_creation_text = `${skeleton_first}
logsource:
    category: process_creation
    product: linux
${skeleton_last}
`

const Linux_any_logs_text = `${skeleton_first}
logsource:
    product: linux
${skeleton_last}
`

const Linux_auditd_text = `${skeleton_first}
logsource:
    category: auditd
    product: linux
${skeleton_last}
`

const Linux_clamav_text = `${skeleton_first}
logsource:
    category: clamav
    product: linux
${skeleton_last}
`
const Linux_cron_text = `${skeleton_first}
logsource:
    category: cron
    product: linux
${skeleton_last}
`
const Linux_guacamole_text = `${skeleton_first}
logsource:
    category: guacamole
    product: linux
${skeleton_last}
`
const Linux_modsecurity_text = `${skeleton_first}
logsource:
    category: modsecurity
    product: linux
${skeleton_last}
`
const Linux_sudo_text = `${skeleton_first}
logsource:
    category: sudo
    product: linux
${skeleton_last}
`
const Linux_sshd_text = `${skeleton_first}
logsource:
    category: sshd
    product: linux
${skeleton_last}
`
const Linux_syslog_text = `${skeleton_first}
logsource:
    category: syslog
    product: linux
${skeleton_last}
`

const Linux_vsftpd_text = `${skeleton_first}
logsource:
    category: vsftpd
    product: linux
${skeleton_last}
`

// MAC OS
const Macos_file_event_text = `${skeleton_first}
logsource:
    category: file_event
    product: macos
${skeleton_last}
`

const Macos_process_creation_text = `${skeleton_first}
logsource:
    category: process_creation
    product: macos
${skeleton_last}
`

const Windows_clipboard_capture_text = `${skeleton_first}
logsource:
    category: clipboard_capture
    product: windows
${skeleton_last}
`

const Windows_create_remote_thread_text = `${skeleton_first}
logsource:
    category: create_remote_thread
    product: windows
${skeleton_last}
`

const Windows_create_stream_hash_text = `${skeleton_first}
logsource:
    category: create_stream_hash
    product: windows
${skeleton_last}
`

const Windows_dns_query_text = `${skeleton_first}
logsource:
    category: dns_query
    product: windows
${skeleton_last}
`

const Windows_driver_load_text = `${skeleton_first}
logsource:
    category: driver_load
    product: windows
${skeleton_last}
`

const Windows_file_change_text = `${skeleton_first}
logsource:
    category: file_change
    product: windows
${skeleton_last}
`

const Windows_file_delete_text = `${skeleton_first}
logsource:
    category: file_delete
    product: windows
${skeleton_last}
`

const Windows_file_event_text = `${skeleton_first}
logsource:
    category: file_event
    product: windows
${skeleton_last}
`

const Windows_image_load_text = `${skeleton_first}
logsource:
    category: image_load
    product: windows
${skeleton_last}
`

const Windows_network_connection_text = `${skeleton_first}
logsource:
    category: network_connection
    product: windows
${skeleton_last}
`

const Windows_pipe_created_text = `${skeleton_first}
logsource:
    category: pipe_created
    product: windows
${skeleton_last}
`

const Windows_process_access_text = `${skeleton_first}
logsource:
    category: process_access
    product: windows
${skeleton_last}
`

const Windows_process_creation_text = `${skeleton_first}
logsource:
    category: process_creation
    product: windows
${skeleton_last}
`

const Windows_process_tampering_text = `${skeleton_first}
logsource:
    category: process_tampering
    product: windows
${skeleton_last}
`

const Windows_process_termination_text = `${skeleton_first}
logsource:
    category: process_termination
    product: windows
${skeleton_last}
`

const Windows_ps_classic_provider_start_text = `${skeleton_first}
logsource:
    category: ps_classic_provider_start
    product: windows
${skeleton_last}
`

const Windows_ps_classic_script_text = `${skeleton_first}
logsource:
    category: ps_classic_script
    product: windows
${skeleton_last}
`

const Windows_ps_classic_start_text = `${skeleton_first}
logsource:
    category: ps_classic_start
    product: windows
${skeleton_last}
`

const Windows_ps_module_text = `${skeleton_first}
logsource:
    category: ps_module
    product: windows
${skeleton_last}
`

const Windows_ps_script_text = `${skeleton_first}
logsource:
    category: ps_script
    product: windows
${skeleton_last}
`

const Windows_raw_access_thread_text = `${skeleton_first}
logsource:
    category: raw_access_thread
    product: windows
${skeleton_last}
`

const Windows_registry_add_text = `${skeleton_first}
logsource:
    category: registry_add
    product: windows
${skeleton_last}
`

const Windows_registry_delete_text = `${skeleton_first}
logsource:
    category: registry_delete
    product: windows
${skeleton_last}
`

const Windows_registry_event_text = `${skeleton_first}
logsource:
    category: registry_event
    product: windows
${skeleton_last}
`

const Windows_registry_rename_text = `${skeleton_first}
logsource:
    category: registry_rename
    product: windows
${skeleton_last}
`

const Windows_registry_set_text = `${skeleton_first}
logsource:
    category: registry_set
    product: windows
${skeleton_last}
`

const Windows_sysmon_error_text = `${skeleton_first}
logsource:
    category: sysmon_error
    product: windows
${skeleton_last}
`

const Windows_sysmon_status_text = `${skeleton_first}
logsource:
    category: sysmon_status
    product: windows
${skeleton_last}
`

const Windows_wmi_event_text = `${skeleton_first}
logsource:
    category: wmi_event
    product: windows
${skeleton_last}
`

const Windows_application_text = `${skeleton_first}
logsource:
    service: application
    product: windows
${skeleton_last}
`

const Windows_applocker_text = `${skeleton_first}
logsource:
    service: applocker
    product: windows
${skeleton_last}
`

const Windows_bitsclient_text = `${skeleton_first}
logsource:
    service: bits-client
    product: windows
${skeleton_last}
`

const Windows_codeintegrityoperational_text = `${skeleton_first}
logsource:
    service: codeintegrity-operational
    product: windows
${skeleton_last}
`
const Windows_dhcp_text = `${skeleton_first}
logsource:
    service: dhcp
    product: windows
${skeleton_last}
`
const Windows_dnsserver_text = `${skeleton_first}
logsource:
    service:  dns-server
    product: windows
${skeleton_last}
`
const Windows_driverframework_text = `${skeleton_first}
logsource:
    service: driver-framework
    product: windows
${skeleton_last}
`
const Windows_firewallas_text = `${skeleton_first}
logsource:
    service: firewall-as
    product: windows
${skeleton_last}
`
const Windows_ldap_debug_text = `${skeleton_first}
logsource:
    service:  ldap_debug
    product: windows
${skeleton_last}
`
const Windows_microsoftservicebusclient_text = `${skeleton_first}
logsource:
    service: microsoft-servicebus-client
    product: windows
${skeleton_last}
`
const Windows_msexchangemanagement_text = `${skeleton_first}
logsource:
    service: msexchange-management
    product: windows
${skeleton_last}
`
const Windows_ntlm_text = `${skeleton_first}
logsource:
    service: ntlm
    product: windows
${skeleton_last}
`
const Windows_powershell_text = `${skeleton_first}
logsource:
    service: powershell
    product: windows
${skeleton_last}
`
const Windows_powershellclassic_text = `${skeleton_first}
logsource:
    service: powershell-classic
    product: windows
${skeleton_last}
`
const Windows_printserviceadmin_text = `${skeleton_first}
logsource:
    service: printservice-admin
    product: windows
${skeleton_last}
`
const Windows_printserviceoperational_text = `${skeleton_first}
logsource:
    service: printservice-operational
    product: windows
${skeleton_last}
`
const Windows_security_text = `${skeleton_first}
logsource:
    service: security
    product: windows
${skeleton_last}
`
const Windows_securitymitigations_text = `${skeleton_first}
logsource:
    service: security-mitigations
    product: windows
${skeleton_last}
`
const Windows_smbclientsecurity_text = `${skeleton_first}
logsource:
    service: smbclient-security
    product: windows
${skeleton_last}
`
const Windows_sysmon_text = `${skeleton_first}
logsource:
    service: sysmon
    product: windows
${skeleton_last}
`
const Windows_system_text = `${skeleton_first}
logsource:
    service: system
    product: windows
${skeleton_last}
`
const Windows_taskscheduler_text = `${skeleton_first}
logsource:
    service: taskscheduler
    product: windows
${skeleton_last}
`
const Windows_terminalservices_text = `${skeleton_first}
logsource:
    service: terminalservices
    product: windows
${skeleton_last}
`
const Windows_windefend_text = `${skeleton_first}
logsource:
    service: windefend
    product: windows
${skeleton_last}
`
const Windows_wmi_text = `${skeleton_first}
logsource:
    service: wmi
    product: windows
${skeleton_last}
`

const SigmaTemplates = [
    { "os": "Cloud: AWS", "text": aws_text },
    { "os": "Cloud: Azure_activitylogs", "text": Azure_activitylogs_text },
    { "os": "Cloud: Azure_signinlogs", "text": Azure_signinlogs_text },
    { "os": "Cloud: GCP Audit logs", "text": GCP_auditlogs_text },
    { "os": "Cloud: GWorkspace", "text": Gworkspace_text },
    { "os": "Cloud: Microsoft 365", "text": Microsoft365_text },
    { "os": "Cloud: Okta", "text": Okta_text },
    { "os": "Linux: File create", "text": Linux_file_create_text },
    { "os": "Linux: Network connection", "text": Linux_network_connection_text },
    { "os": "Linux: Process creation", "text": Linux_process_creation_text },
    { "os": "Linux: Any logs", "text": Linux_any_logs_text },
    { "os": "Linux: AuditD", "text": Linux_auditd_text },
    { "os": "Linux: ClamAV", "text": Linux_clamav_text },
    { "os": "Linux: CRON", "text": Linux_cron_text },
    { "os": "Linux: Guacamole", "text": Linux_guacamole_text },
    { "os": "Linux: Modseurity", "text": Linux_modsecurity_text },
    { "os": "Linux: sudo", "text": Linux_sudo_text },
    { "os": "Linux: sshd", "text": Linux_sshd_text },
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