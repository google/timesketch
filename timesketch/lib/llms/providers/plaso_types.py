"""Utilities for working with Plaso logs and log source descriptions."""

# List of data types that are supported by Plaso.
PLASO_DATA_TYPE_DESCRIPTIONS = {
    "android:app_usage": "Android application usage event data.",
    "android:event:battery": "Android turbo battery event data.",
    "android:event:call": "Android Call event data.",
    "android:logcat": "Android logcat event data.",
    "android:messaging:hangouts": "Google Hangouts Message event data.",
    "android:messaging:sms": "Android SMS event data.",
    "android:sqlite:app_usage": "Android app usage event data.",
    "android:tango:contact": "Tango on Android contact event data.",
    "android:tango:conversation": "Tango on Android conversation event data.",
    "android:tango:message": "Tango on Android message event data.",
    "android:twitter:contact": "Twitter on Android contact event data.",
    "android:twitter:search": "Twitter on Android search event data.",
    "android:twitter:status": "Twitter on Android status event data.",
    "android:webview:cookie": "Android WebView cookie event data.",
    "android:webviewcache": "Android WebViewCache event data.",
    "apache:access_log:entry": "Apache access log event data.",
    "av:defender:detection_history": (
        "Windows Defender scan DetectionHistory event data."
    ),
    "av:mcafee:accessprotectionlog": "McAfee AV Log event data.",
    "av:symantec:scanlog": "Symantec event data.",
    "av:trendmicro:scan": "Trend Micro AV Log event data.",
    "av:trendmicro:webrep": "Trend Micro Web Reputation Log event data.",
    "aws:cloudtrail:entry": "AWS CloudTrail log event data.",
    "aws:elb:access": "AWS Elastic Load Balancer access log event data.",
    "azure:activitylog:entry": "Azure activity log event data.",
    "azure:application_gateway_access:entry": (
        "Azure application gateway access log event data."
    ),
    "bash:history:entry": "Bash history log event data.",
    "bsm:entry": "Basic Security Module (BSM) audit event data.",
    "ccleaner:configuration": "CCleaner configuration event data.",
    "ccleaner:update": "CCleaner update event data.",
    "chrome:autofill:entry": "Chrome Autofill event data.",
    "chrome:cache:entry": "Chrome Cache event data.",
    "chrome:cookie:entry": "Chrome Cookie event data.",
    "chrome:extension_activity:activity_log": ("Chrome Extension Activity event data."),
    "chrome:history:file_downloaded": ("Chrome History file downloaded event data."),
    "chrome:history:page_visited": "Chrome History page visited event data.",
    "chrome:preferences:content_settings:exceptions": (
        "Chrome content settings exceptions event data."
    ),
    "chrome:preferences:extension_installation": "Chrome extension event data.",
    "chrome:preferences:extensions_autoupdater": (
        "Chrome Extension Autoupdater event data."
    ),
    "confluence:access": "Confluence access event data.",
    "cookie:google:analytics:utma": ("Google analytics __utma cookie event data."),
    "cookie:google:analytics:utmb": ("Google analytics __utmb cookie event data."),
    "cookie:google:analytics:utmt": ("Google analytics __utmt cookie event data."),
    "cookie:google:analytics:utmz": ("Google analytics __utmz cookie event data."),
    "cri:container:log:entry": "CRI log event data.",
    "cups:ipp:event": "CUPS IPP event data.",
    "docker:container:configuration": ("Docker container configuration event data."),
    "docker:container:log:entry": "Docker container log event data.",
    "docker:layer:configuration": "Docker layer configuration event data.",
    "docker:json:container:log": "Docker Container Logs.",
    "docker:json:container": "Docker Container Logs.",
    "dropbox:sync_history:entry": "Dropbox Sync History Database event data.",
    "edge:resources:load_statistics": (
        "Microsoft Edge load statistics resource event data."
    ),
    "event": "Formatter for events that do not have any defined formatter.",
    "file_entry": "File entry event source.",
    "firefox:cache:record": "Firefox cache event data.",
    "firefox:cookie:entry": "Firefox Cookie event data.",
    "firefox:downloads:download": "Firefox download event data.",
    "firefox:places:bookmark": "Firefox bookmark event data.",
    "firefox:places:bookmark_annotation": ("Firefox bookmark annotation event data."),
    "firefox:places:bookmark_folder": "Firefox bookmark folder event data.",
    "firefox:places:page_visited": "Firefox page visited event data.",
    "fish:history:entry": "Fish history log event data.",
    "fs:bodyfile:entry": "Bodyfile event data.",
    "fs:ntfs:usn_change": "NTFS USN change event data.",
    "fs:stat": "File system stat event data.",
    "fs:stat:ntfs": "NTFS file system stat event data.",
    "gcp:log:entry": "Google Cloud (GCP) log event data.",
    "gcp:log:json": "Google Cloud (GCP) json data.",
    "gdrive:snapshot:cloud_entry": ("Google Drive snapshot cloud entry event data."),
    "gdrive:snapshot:local_entry": ("Google Drive snapshot local entry event data."),
    "google_drive_sync_log:entry": "Google Drive Sync log event data.",
    "googlelog:log": "Google-formatted log file event data.",
    "iis:log:line": "IIS log event data.",
    "imessage:event:chat": "iMessage and SMS event data.",
    "ios:app_privacy:access": ("iOS application privacy report event of type access."),
    "ios:app_privacy:network": (
        "iOS application privacy report event of type network activity."
    ),
    "ios:carplay:history:entry": ("Apple iOS Car Play application history event data."),
    "ios:datausage:event": "iOS datausage event data.",
    "ios:idstatuscache:lookup": ("iOS identity services status cache event data."),
    "ios:kik:messaging": "Kik message event data.",
    "ios:lockdownd_log:entry": ("iOS lockdown daemon (lockdownd) log event data."),
    "ios:netusage:process": "iOS netusage process event data.",
    "ios:netusage:route": "iOS netusage connection event data.",
    "ios:powerlog:application_usage": (
        "iOS powerlog file application usage event data."
    ),
    "ios:screentime:event": "iOS Screen Time file usage event data.",
    "ios:sysdiag_log:entry": "iOS sysdiagnose log event data.",
    "ios:sysdiagnose:logd:line": "iOS sysdiagnose logd event data.",
    "ios:twitter:contact": "Twitter on iOS 8+ contact event data.",
    "ios:twitter:status": "Parent class for Twitter on iOS 8+ status events.",
    "ipod:device:entry": "iPod plist event data.",
    "java:download:idx": "Java IDX cache file event data.",
    "kodi:videos:viewing": "Kodi video event data.",
    "linux:apt_history_log:entry": "APT History log event data.",
    "linux:dpkg_log:entry": "Dpkg event data.",
    "linux:locate_database:entry": ("Linux locate database (updatedb) event data."),
    "linux:popularity_contest_log:entry": "Popularity Contest event data.",
    "linux:popularity_contest_log:session": ("Popularity Contest session event data."),
    "linux:utmp:event": "Linux libc6 utmp event data.",
    "mackeeper:cache": "MacKeeper Cache event data.",
    "macos:airport:entry": "MacOS airport event data.",
    "macos:appfirewall_log:entry": (
        "MacOS Application firewall log (appfirewall.log) file event data."
    ),
    "macos:apple_account:entry": "Apple account event data.",
    "macos:application_usage:entry": "MacOS application usage event data.",
    "macos:asl:entry": "Apple System Log (ASL) event data.",
    "macos:asl:file": "Apple System Log (ASL) file event data.",
    "macos:background_items:entry": "Mac OS background item event data.",
    "macos:bluetooth:entry": "MacOS Bluetooth event data.",
    "macos:document_versions:file": "MacOS document revision event data.",
    "macos:fseventsd:record": "MacOS file system event (fseventsd) event data.",
    "macos:install_history:entry": "MacOS install history event data.",
    "macos:keychain:application": (
        "MacOS keychain application password record event data."
    ),
    "macos:keychain:internet": "MacOS keychain internet record event data.",
    "macos:knowledgec:application": ("KnowledgeC application execution event data."),
    "macos:knowledgec:safari": (
        "MacOS Duet/KnowledgeC database event data for Safari."
    ),
    "macos:launchd:entry": "MacOS launchd event data.",
    "macos:launchd_log:entry": "Mac OS launchd log event data.",
    "macos:login_items:entry": "Mac OS login item event data.",
    "macos:login_window:entry": "Mac OS login window event data.",
    "macos:login_window:managed_login_item": (
        "Mac OS login window managed login item event data."
    ),
    "macos:lsquarantine:entry": "MacOS launch services quarantine event data.",
    "macos:notes:entry": "MacOS Notes event data.",
    "macos:notification_center:entry": "MacOS NotificationCenter event data.",
    "macos:securityd_log:entry": "MacOS securityd log event data.",
    "macos:software_updata:entry": "MacOS software update event data.",
    "macos:startup_item:entry": "Mac OS startup item event data.",
    "macos:tcc_entry": "MacOS TCC event data.",
    "macos:time_machine:backup": "MacOS TimeMachine backup event data.",
    "macos:unified_logging:event": "Apple Unified Logging (AUL) event data.",
    "macos:user:entry": "MacOS user event data.",
    "macos:utmpx:entry": "MacOS utmpx event data.",
    "macos:wifi_log:entry": "MacOS Wi-Fi log event data.",
    "microsoft365:audit_log:entry": ("Microsoft (Office) 365 audit log event data."),
    "msie:webcache:container": "MSIE WebCache Container table event data.",
    "msie:webcache:containers": "MSIE WebCache Containers table event data.",
    "msie:webcache:cookie": "MSIE WebCache Container table event data.",
    "msie:webcache:leak_file": "MSIE WebCache LeakFiles event data.",
    "msie:webcache:partitions": "MSIE WebCache Partitions table event data.",
    "msiecf:leak": "MSIECF leak event data.",
    "msiecf:redirected": "MSIECF redirected event data.",
    "msiecf:url": "MSIECF URL event data.",
    "networkminer:fileinfos:file": "NetworkMiner event Data.",
    "olecf:dest_list:entry": (".automaticDestinations-ms DestList entry event data."),
    "olecf:document_summary_info": ("OLECF document summary information event data."),
    "olecf:item": "OLECF item event data.",
    "olecf:summary_info": "OLECF summary information event data.",
    "openxml:metadata": "OXML event data.",
    "opera:history:entry": "Opera global history entry data.",
    "opera:history:typed_entry": "Opera typed history entry data.",
    "p2p:bittorrent:transmission": "Transmission BitTorrent event data.",
    "p2p:bittorrent:utorrent": "UTorrent active torrent event data.",
    "pe_coff:dll_import": "Portable Executable (PE) DLL import event data.",
    "pe_coff:file": "Portable Executable (PE) file event data.",
    "pe_coff:resource": "Portable Executable (PE) resource event data.",
    "olecf:dest_list": ".automaticDestinations-ms DestList entry event data.",
    "plist:key": "Plist event data attribute container.",
    "pls_recall:entry": "PL/SQL Recall event data.",
    "postgresql:application_log:entry": "PostgreSQL application log data.",
    "powershell:transcript_log:entry": "PowerShell transcript log event data.",
    "safari:cookie:entry": "Safari binary cookie event data.",
    "safari:downloads:entry": "Safari download event data.",
    "safari:history:visit": "Safari history event data.",
    "safari:history:visit_sqlite": "Safari history event data.",
    "santa:diskmount": "Santa mount event data.",
    "santa:execution": "Santa execution event data.",
    "santa:file_system_event": "Santa file system event data.",
    "santa:process_exit": "Santa process exit event data.",
    "sccm_log:entry": "SCCM log event data.",
    "selinux:line": "SELinux log event data.",
    "setupapi:log:line": "SetupAPI log event data.",
    "shell:zsh:history": "ZSH history event data.",
    "skydrive:log:entry": "SkyDrive log event data.",
    "skype:event:account": "Skype account event data.",
    "skype:event:call": "Skype call event data.",
    "skype:event:chat": "Skype chat event data.",
    "skype:event:sms": "Skype SMS event data.",
    "skype:event:transferfile": "Skype file transfer event data.",
    "snort:fastlog:alert": "Snort3/Suricata fast-log alert event data.",
    "sophos:av:log": "Sophos anti-virus log event data.",
    "spotlight:metadata_item": (
        "Apple Spotlight store database metadata item event data."
    ),
    "spotlight_searched_terms:entry": "Spotlight searched terms event data.",
    "spotlight_volume_configuration:store": (
        "Spotlight volume configuration event data."
    ),
    "syslog:comment": "Syslog comment event data.",
    "syslog:cron:task_run": "Syslog cron task run event data.",
    "syslog:line": "Syslog line event data.",
    "syslog:ssh:failed_connection": "SSH failed connection event data.",
    "syslog:ssh:login": "SSH login event data.",
    "syslog:ssh:opened_connection": "SSH opened connection event data.",
    "systemd:journal": "Systemd journal event data.",
    "task_scheduler:task_cache:entry": "Task Cache event data.",
    "teamviewer:application_log:entry": ("TeamViewer application log event data."),
    "teamviewer:connections_incoming:entry": (
        "TeamViewer incoming connection log event data."
    ),
    "teamviewer:connections_outgoing:entry": (
        "TeamViewer outgoing connection log event data."
    ),
    "viminfo:history": "VimInfo event data.",
    "vsftpd:log": "Vsftpd log event data.",
    "wincc:simatic_s7:entry": "SIMATIC S7 event data.",
    "wincc:sys_log:entry": "WinCC Sys Log event data.",
    "windows:diagnosis:eventtranscript": (
        "Windows diagnosis EventTranscript event data."
    ),
    "windows:distributed_link_tracking:creation": (
        "Windows distributed link event data attribute container."
    ),
    "windows:evt:record": "Windows EventLog (EVT) record event data.",
    "windows:evtx:record": "Windows XML EventLog (EVTX) record event data.",
    "windows:file_history:namespace": ("File history namespace table event data."),
    "windows:firewall_log:entry": "Windows Firewall event data.",
    "windows:lnk:link": "Windows Shortcut (LNK) link event data.",
    "windows:metadata:deleted_item": "Windows Recycle Bin event data.",
    "windows:onedrive:log": "OneDrive log event data.",
    "windows:pca_log:entry": (
        "Windows PCA (Program Compatibility Assistant) event data."
    ),
    "windows:prefetch:execution": "Windows Prefetch event data.",
    "windows:registry:amcache": "AMCache file event data.",
    "windows:registry:amcache:programs": "AMCache programs event data.",
    "windows:registry:appcompatcache": ("Application Compatibility Cache event data."),
    "windows:registry:bagmru": (
        "BagMRU (or ShellBags) event data attribute container."
    ),
    "windows:registry:bam": "Background Activity Moderator event data.",
    "windows:registry:boot_execute": (
        "Windows Boot Execute event data attribute container."
    ),
    "windows:registry:boot_verification": (
        "Windows Boot Verification event data attribute container."
    ),
    "windows:registry:explorer:programcache": (
        "Explorer ProgramsCache event data attribute container."
    ),
    "windows:registry:installation": (
        "Windows installation event data attribute container."
    ),
    "windows:registry:key_value": ("Windows Registry event data attribute container."),
    "windows:registry:motherboard_info": (
        "Windows Motherboard Info event data attribute container."
    ),
    "windows:registry:mount_points2": (
        "Windows MountPoints2 event data attribute container."
    ),
    "windows:registry:mrulist": "MRUList event data attribute container.",
    "windows:registry:mrulistex": "MRUListEx event data attribute container.",
    "windows:registry:msie_zone_settings": (
        "MSIE zone settings event data attribute container."
    ),
    "windows:registry:mstsc:connection": (
        "Terminal Server client connection event data attribute container."
    ),
    "windows:registry:mstsc:mru": (
        "Terminal Server client MRU event data attribute container."
    ),
    "windows:registry:network": "Windows NetworkList event data.",
    "windows:registry:network_drive": ("Network drive event data attribute container."),
    "windows:registry:office_mru": (
        "Microsoft Office MRU Windows Registry event data."
    ),
    "windows:registry:office_mru_list": (
        "Microsoft Office MRU list Windows Registry event data."
    ),
    "windows:registry:outlook_search_mru": (
        "Outlook search MRU event data attribute container."
    ),
    "windows:registry:run": "Run/RunOnce key event data attribute container.",
    "windows:registry:sam_users": (
        "Class that defines SAM users Windows Registry event data."
    ),
    "windows:registry:service": (
        "Windows Registry driver or service event data attribute container."
    ),
    "windows:registry:shutdown": "Shutdown Windows Registry event data.",
    "windows:registry:timezone": ("Timezone settings event data attribute container."),
    "windows:registry:typedurls": "Typed URLs event data attribute container.",
    "windows:registry:usb": ("Windows USB device event data attribute container."),
    "windows:registry:usbstor:instance": (
        "USBStor device instance event data attribute container."
    ),
    "windows:registry:userassist": "UserAssist Windows Registry event data.",
    "windows:registry:winlogon": "Winlogon event data attribute container.",
    "windows:restore_point:info": "Windows Restore Point event data.",
    "windows:shell_item:file_entry": (
        "Windows shell item file entry event data attribute container."
    ),
    "windows:srum:application_usage": ("SRUM application resource usage event data."),
    "windows:srum:network_connectivity": (
        "SRUM network connectivity usage event data."
    ),
    "windows:srum:network_usage": "SRUM network data usage event data.",
    "windows:tasks:job": "Windows Scheduled Task event data.",
    "windows:tasks:trigger": "Windows Scheduled Task trigger event data.",
    "windows:timeline:generic": ("Windows 10 timeline database generic event data."),
    "windows:timeline:user_engaged": (
        "Windows 10 timeline database User Engaged event data."
    ),
    "windows:user_access_logging:clients": (
        "Windows User Access Logging CLIENTS table event data."
    ),
    "windows:user_access_logging:dns": (
        "Windows User Access Logging DNS table event data."
    ),
    "windows:user_access_logging:role_access": (
        "Windows User Access Logging ROLE_ACCESS table event data."
    ),
    "windows:user_access_logging:system_identity": (
        "Windows User Access Logging SYSTEM_IDENTITY table event data."
    ),
    "windows:user_access_logging:virtual_machines": (
        "Windows User Access Logging VIRTUALMACHINES table event data."
    ),
    "windows:volume:creation": "Windows volume event data attribute container.",
    "windows:wpndatabase:notification": "Windows push notification event data.",
    "windows:wpndatabase:notification_handler": (
        "Windows push notification handler event data."
    ),
    "winrar:history": "WinRAR history event data attribute container.",
    "xchat:log:line": "XChat Log event data.",
    "xchat:scrollback:line": "XChat Scrollback line event data.",
    "zeitgeist:activity": "Zeitgeist activity event data.",
    "linux:locate": "Linux locate database (updatedb) event data.",
    "bash:history:command": "Bash history log event data.",
    "PLSRecall:event": "PL/SQL Recall event data.",
    "fs:mactime:line": "Mactime filesystem event data.",
    "dpkg:line": "Dpkg event data.",
    "apt:history:line": "APT History log event data.",
    "pe": "Portable Executable (PE).",
}
