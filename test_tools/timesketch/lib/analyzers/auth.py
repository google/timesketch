# -*- coding: utf-8 -*-
# Copyright 2022 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Base authentication analyzer"""

import logging
from datetime import datetime
from typing import List
import pandas as pd


log = logging.getLogger("turbinia")


class AuthSummaryData:
    """Authentication summary data."""

    def __init__(self):
        # Summary information for source_ip or username
        self.summary_type = None
        self.source_ip = ""
        self.domain = ""
        self.username = ""

        # The first time the source_ip or username observed in auth events.
        # This can be a successful or failed login event.
        self.first_seen = 0

        # The last time the source_ip or username was observed in auth events.
        # This can be a successful or failed login event.
        self.last_seen = 0

        # The first time the source_ip or username successfully login.
        self.first_auth_timestamp = 0
        self.first_auth_ip = ""
        self.first_auth_username = ""

        # The list of IP addresses that successfully authenticated to the system.
        # This is used when summary_type is username.
        self.success_source_ip_list = []
        self.success_username_list = []

        self.total_success_events = 0
        self.total_failed_events = 0

        # The total number of unique IP addresses observed in the log
        self.distinct_source_ip_count = 0
        self.distinct_username_count = 0

        self.top_source_ips = {}
        self.top_usernames = {}

    def report(self):
        return {
            "summary_type": self.summary_type,
            "source_ip": self.source_ip,
            "domain": self.domain,
            "username": self.username,
            "first_seen": self.first_seen,
            "last_seen": self.last_seen,
            "first_auth_timestamp": self.first_auth_timestamp,
            "first_auth_ip": self.first_auth_ip,
            "first_auth_username": self.first_auth_username,
            "total_success_events": self.total_success_events,
            "total_failed_events": self.total_failed_events,
            "success_source_ip_list": self.success_source_ip_list,
            "success_username_list": self.success_username_list,
            "distinct_source_ip_count": self.distinct_source_ip_count,
            "distinct_username_count": self.distinct_username_count,
            "top_source_ips": self.top_source_ips,
            "top_usernames": self.top_usernames,
        }


class AuthAnalyzer:
    """Analyzer for authentication analysis.

    Attributes:
      name (str): Analyzer short name
      display_name (str): Display name of the analyzer
      description (str): Brief description about the analyzer
      df (pd.DataFrame): Authentication dataframe
    """

    REQUIRED_ATTRIBUTES = [
        "timestamp",
        "event_type",
        "auth_method",
        "auth_result",
        "hostname",
        "source_ip",
        "source_port",
        "source_hostname",
        "domain",
        "username",
        "session_id",
    ]

    def __init__(self, name: str, display_name: str, description: str) -> None:
        """Initialization of authentication analyzer.

        Args:
          name (str): Analyzer short name
          display_name (str): Analyzer display name
          description (str): Brief description of the analyzer
        """
        if not name:
            raise Exception("Analyzer name is required")
        if not display_name:
            raise Exception("Analyzer display name is required")

        self.name = name
        self.display_name = display_name
        self.description = description
        self.df = pd.DataFrame()

    def set_dataframe(self, df: pd.DataFrame) -> bool:
        """Sets dataframe.

        Args:
          df (pd.DataFrame): Authentication dataframe

        Returns:
          bool: Returns True if successfully set.
        """
        # We only want to proceed further if the panda dataframe
        # matches the required fields
        column_list = df.columns.tolist()
        if not self.check_required_fields(column_list):
            log.error("Dataframe does not match required columns")
            return False

        df.fillna("", inplace=True)
        self.df = df
        self.df.sort_values("timestamp", ascending=True)
        return True

    def check_required_fields(self, fields: list) -> bool:
        """Checks the required fields in the data frame.

        Args:
          fields (list): List of columns name in dataframe

        Returns:
          bool: Returns true if required fields exist
        """

        for req_field in self.REQUIRED_ATTRIBUTES:
            if req_field not in fields:
                log.error("Missing required field %s", req_field)
                return False
        return True

    def get_ip_summary(self, source_ip: str) -> AuthSummaryData:
        """Source IP stats in the data frame.

        Args:
          source_ip (str): Source IP address whose summary will be generated.

        Returns:
          dict: IP summary information as a dictionary
        """

        if self.df.empty:
            log.info("Source dataframe is empty")
            return {}
        df = self.df

        df1 = df[df["source_ip"] == source_ip]
        if df1.empty:
            log.info("%s: no data for source ip", source_ip)
            return {}
        return self.get_auth_summary(df1=df1, summary_type="source_ip", value=source_ip)

    def get_user_summary(self, domain: str, username: str) -> AuthSummaryData:
        """Username stats in the dataframe.

        Args:
          domain (str): Filter dataframe using domain
          username (str): Filter dataframe using username

        Returns:
          dict: user summary information as dictionary
        """
        if self.df.empty:
            log.info("Source dataframe is empty")
            return {}
        df = self.df

        df1 = df[(df["domain"] == domain) & (df["username"] == username)]
        if df1.empty:
            log.info("User summary dataframe is empty")
            return {}

        df1.sort_values(by="timestamp", ascending=True)

        useraccount = self.to_useraccount(domain, username)
        return self.get_auth_summary(
            df1=df1, summary_type="username", value=useraccount
        )

    def get_auth_summary(
        self, df1: pd.DataFrame, summary_type: str, value: str
    ) -> AuthSummaryData:
        """Returns authentication summary information."""
        df1.sort_values(by="timestamp", ascending=True)

        summary = AuthSummaryData()

        if summary_type == "source_ip":
            summary.summary_type = "source_ip"
            summary.source_ip = value
        elif summary_type == "username":
            domain, username = self.from_useraccount(value)
            summary.summary_type = "username"
            summary.domain = domain
            summary.username = username
        else:
            log.error("Unsupported summary_type value %s", summary_type)
            return summary

        # First and last time the brute forcing IP address was observed
        summary.first_seen = int(df1.iloc[0]["timestamp"])
        summary.last_seen = int(df1.iloc[-1]["timestamp"])

        # The list of successful source_ip addresses and usernames.
        # summary['usernames'] = list(
        #    set(df1[df1['auth_result'] == 'success']['username'].to_list()))
        summary.success_source_ip_list = list(
            set(df1[df1["auth_result"] == "success"]["source_ip"].to_list())
        )
        summary.success_username_list = list(
            set(df1[df1["auth_result"] == "success"]["username"].to_list())
        )

        # Authentication events
        df_success = df1[df1["auth_result"] == "success"]
        if not df_success.empty:
            summary.first_auth_timestamp = int(df_success.iloc[0]["timestamp"])
            summary.first_auth_ip = df_success.iloc[0]["source_ip"]
            summary.first_auth_username = df_success.iloc[0]["username"]

        # Total number of successful and failed login events
        summary.total_success_events = len(df_success.index)
        df_failure = df1[df1["auth_result"] == "failure"]
        summary.total_failed_events = len(df_failure.index)

        # Total number of unique ip and username attempted
        # summary['unique_username_count'] = len(df1['username'].unique())
        summary.distinct_source_ip_count = len(df1["source_ip"].unique())
        summary.distinct_username_count = len(df1["username"].unique())

        # Top 10 ip and username attempted
        # summary['top_usernames'] = df1.groupby(
        #    by='username')['timestamp'].nunique().nlargest(10).to_dict()
        summary.top_source_ips = (
            df1.groupby(by="source_ip")["timestamp"].nunique().nlargest(10).to_dict()
        )
        summary.top_usernames = (
            df1.groupby(by="username")["timestamp"].nunique().nlargest(10).to_dict()
        )

        return summary

    def to_useraccount(self, domain: str, username: str) -> str:
        """Convert domain and username to useraccount."""

        if not username or username.lower() == "nan":
            return username
        return f"{domain}\\{username}"

    def from_useraccount(self, useraccount: str):
        """Split useraccount into domain and username."""

        if not "\\" in useraccount:
            return "", useraccount

        val = useraccount.split("\\")
        try:
            domain = val[0].strip()
            username = val[1].strip()
            return domain, username
        except ValueError:
            return "", username

    def human_timestamp(self, timestamp: int) -> str:
        """Convert epoch timestamp to humand readable date/time."""
        return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")

    def get_login_session(
        self, source_ip: str, domain: str, username: str, session_id: str
    ) -> dict:
        """Get loging session details."""
        login_session = {
            "source_ip": source_ip,
            "domain": domain,
            "username": username,
            "session_id": session_id,
            "login_timestamp": 0,
            "logout_timestamp": 0,
            "session_duration": 0,
        }

        if self.df.empty:
            log.debug("Source dataframe is empty")
            return login_session
        df = self.df
        try:
            df_session = df[
                (df["source_ip"] == source_ip)
                & (df["username"] == username)
                & (df["session_id"] == session_id)
            ]
            login_ts = int(
                df_session[df_session["auth_result"] == "success"].iloc[0]["timestamp"]
            )
            logout_ts = int(
                df_session[df_session["event_type"] == "disconnection"].iloc[0][
                    "timestamp"
                ]
            )
            session_duration = logout_ts - login_ts
            login_session["login_timestamp"] = login_ts
            login_session["logout_timestamp"] = logout_ts
            login_session["session_duration"] = session_duration
        except KeyError as exception:
            log.error(
                "Session duration calculation failed due to key error: %s",
                str(exception),
            )
        except IndexError as exception:
            log.error(
                "Session duration calculation failed due to index error: %s",
                str(exception),
            )
        finally:
            return login_session


class BruteForceAnalyzer(AuthAnalyzer):
    """Analyzer for brute force authentication."""

    NAME = "bruteforce.auth.analyzer"
    DISPLAY_NAME = "Brute Force Analyzer"
    DESCRIPTION = "This analyzer identifies brute force authentication"

    # The time duration before a successful login event to evalute for
    # brute force activity.
    BRUTE_FORCE_WINDOW = 3600

    # The minimum number of failed events that must occure to be considered
    # for brute force activity.
    BRUTE_FORCE_MIN_FAILED_EVENT = 20

    # The time duration, in seconds, between successive authentication
    # events to be considered for brute force activity.
    BRUTE_FORCE_NEXT_LOGIN_DELTA = 10

    # The minimum duration where the attacker accessed the host after
    # a successful brute for login.
    BRUTE_FORCE_MIN_ACCESS_DURATION = 600

    def __init__(self):
        """Initialize brute force analyzer."""
        super().__init__(self.NAME, self.DISPLAY_NAME, self.DESCRIPTION)

    def login_analysis(self, source_ip: str) -> dict:
        """Perform authentication analysis per souce IP"""

        if self.df.empty:
            log.info("[%s] Source dataframe is empty", self.NAME)
            return {}
        df = self.df

        source_df = df[(df["source_ip"] == source_ip)]
        if source_df.empty:
            log.info(
                "[%s] Login analysis dataframe for %s is empty", self.NAME, source_ip
            )
            return {}

        success_df = source_df[source_df["auth_result"] == "success"]
        if success_df.empty:
            log.info("[%s] No successful login data for %s", self.NAME, source_ip)
            return {}

        # Same IP address can perform multiple brute force attempts
        # and have successful login.
        #
        # We need to capture that.
        brute_force_records = []

        for _, row in success_df.iterrows():
            # Successful login timestamp
            login_ts = row["timestamp"]

            # Time boundary for authentication events check
            start_timestamp = login_ts - self.BRUTE_FORCE_WINDOW
            end_timestamp = login_ts
            log.info(
                "[%s] Checking brute force from %s between %s and %s",
                self.NAME,
                source_ip,
                self.human_timestamp(start_timestamp),
                self.human_timestamp(end_timestamp),
            )

            df1 = source_df[
                (source_df["timestamp"] >= start_timestamp)
                & (source_df["timestamp"] < end_timestamp)
                & (source_df["source_ip"] == source_ip)
            ]
            df2 = df1.groupby(by="auth_result")["timestamp"].count()

            try:
                success_count = df2["success"]
            except KeyError:
                log.info(
                    "[%s] No successful login events for %s."
                    " Setting success_count to zero",
                    self.NAME,
                    source_ip,
                )
                success_count = 0

            try:
                failed_count = df2["failure"]
            except KeyError:
                log.info(
                    "[%s] No failed login events for %s."
                    " Setting failed_count to zero",
                    self.NAME,
                    source_ip,
                )
                failed_count = 0

            log.debug(
                "[%s] Login events distribution from %s: successful %d, failure %d",
                self.NAME,
                source_ip,
                success_count,
                failed_count,
            )

            if success_count == 0 and failed_count >= self.BRUTE_FORCE_MIN_FAILED_EVENT:
                # TODO(rmaskey): Evaluate event timestamps
                row_session_id = row.get("session_id") or ""
                row_domain = row.get("domain")
                row_username = row.get("username")

                brute_force_records.append(
                    self.get_login_session(
                        source_ip=source_ip,
                        domain=row_domain,
                        username=row_username,
                        session_id=row_session_id,
                    )
                )

        # We only need to add enrichment steps if we have successful brute force.
        log.debug(
            "[%s] Total number of brute force records from %s is %d",
            self.NAME,
            source_ip,
            len(brute_force_records),
        )
        if not brute_force_records:
            return {}

        # Enrich successful brute force records with statistical data.
        # Statistical data about the source_ip and the username
        ip_summaries = []
        username_summaries = []

        ip_summary = self.get_ip_summary(source_ip=source_ip)
        if not ip_summary:
            log.info("[%s] No IP summary for %s", self.NAME, source_ip)
        else:
            ip_summaries.append(ip_summary.report())

        # username summaries
        # There could be more than one username that was successfully
        # brute forced. We need to capture gather statistical information
        # about those usernames.
        #
        # We are checking for combination of domain and username to
        # cover brute force for Windows environment with multiple domains with
        # the same username.

        # checked_user_accounts contains DOMAIN_USERNAME to reduce duplicate
        # username statistical data collection.
        checked_user_accounts = []

        for record in brute_force_records:
            domain = record.get("domain")
            username = record.get("username")
            user_account = f"{domain}_{username}"

            log.debug(
                "[%s] Checking for domain: %s, username: %s",
                self.NAME,
                domain,
                username,
            )
            if user_account in checked_user_accounts:
                log.debug(
                    "[%s] Skipping user account %s. User account already checked",
                    self.NAME,
                    user_account,
                )
                continue

            user_summary = self.get_user_summary(domain=domain, username=username)
            if not user_summary:
                log.info(
                    "[%s] No user summary for domain: %s, username: %s",
                    self.NAME,
                    domain,
                    username,
                )
                continue
            username_summaries.append(user_summary.report())

        # Analysis report on the source_ip.
        ip_analysis_report = {
            "source_ip": source_ip,
            "brute_force_logins": brute_force_records,
            "ip_summaries": ip_summaries,
            "user_summaries": username_summaries,
        }

        return ip_analysis_report

    def generate_analyzer_output(self, reports: List, success: bool) -> dict:
        """Generate analyzer output"""

        analyzer_output = {
            "platform": "turbinia",
            "analyzer_identifier": self.NAME,
            "analyzer_name": self.DISPLAY_NAME,
            "result_status": "failure",
            "dfiq_question_id": "",
            "dfiq_question_conclusion": "",
            "result_priority": "LOW",
            "result_summary": "",
            "result_markdown": "",
            "references": [],
            "attributes": reports,
        }

        if not success:
            return analyzer_output
        analyzer_output["result_status"] = "success"

        # Generating result_summary and result_priority
        # result_priority is set to MEDIUM for any successful brute force detection
        reports_count = len(reports)
        if reports_count > 0:
            analyzer_output[
                "result_summary"
            ] = f"Brute force from {reports_count} IP addresses"
            analyzer_output["result_priority"] = "MEDIUM"
        else:
            analyzer_output["result_summary"] = "No brute force detected"

        # Generate result_markdown
        markdown = []

        for report in reports:
            markdown.append(f'### Brute Force from {report["source_ip"]}\n')

            for brute_force_login in report["brute_force_logins"]:
                markdown.append(
                    f'- Successful brute force from {brute_force_login["source_ip"]} as'
                    f' {brute_force_login["username"]} at'
                    f' {self.human_timestamp(brute_force_login["login_timestamp"])}'
                    f' (duration={brute_force_login["session_duration"]})'
                )

                if brute_force_login["session_duration"] > 600:
                    markdown.append(
                        "**NOTE**: Long login duration (>10 minutes)."
                        " Potentially human activity"
                    )

            markdown.append("\n#### IP Summaries\n")
            for ip_summary in report["ip_summaries"]:
                markdown.append(f'- Source IP: {ip_summary["source_ip"]}')
                markdown.append(
                    f"- Brute forcing IP first seen:"
                    f' {self.human_timestamp(ip_summary["first_seen"])}'
                )
                markdown.append(
                    f"- Brute forcing IP last seen:"
                    f' {self.human_timestamp(ip_summary["last_seen"])}'
                )
                markdown.append("- First successful login for brute forcing IP")
                markdown.append(f'    - IP: {ip_summary["first_auth_ip"]}')
                markdown.append(
                    f"    - Login timestamp:"
                    f' {self.human_timestamp(ip_summary["first_auth_timestamp"])}'
                )
                markdown.append(f'    - Username: {ip_summary["first_auth_username"]}')
                markdown.append(
                    f"- Total successful login from IP:"
                    f' {ip_summary["total_success_events"]}'
                )
                markdown.append(
                    f"- Total failed login attempts:"
                    f' {ip_summary["total_failed_events"]}'
                )

                success_ip = ", ".join(ip_summary["success_source_ip_list"])
                markdown.append(
                    f"- IP addresses that successfully logged in: {success_ip}"
                )

                success_usernames = ", ".join(ip_summary["success_username_list"])
                markdown.append(
                    f"- Usernames that successfully logged in: {success_usernames}"
                )
                markdown.append(
                    f"- Total number of unique username attempted:"
                    f' {ip_summary["distinct_username_count"]}'
                )
                markdown.append("- Top 10 username attempted")
                for username, count in ip_summary["top_usernames"].items():
                    markdown.append(f"    - {username}: {count}")

        if markdown:
            markdown.insert(0, "## Brute Force Analysis\n")
            markdown.append("")
            analyzer_output["result_markdown"] = "\n".join(markdown)
        else:
            analyzer_output["result_markdown"] = analyzer_output["result_summary"]
        return analyzer_output

    def run(self, df: pd.DataFrame) -> dict:
        """Entry point for the analyzer.

        Args:
          df (pd.DataFrame): Panda dataframe with authentication data

        Returns:
          AnalyzerResult: Result as AnalyzerResult object.
        """
        if df.empty:
            raise Exception("[{self.NAME}] Dataframe is empty")

        if not self.set_dataframe(df):
            log.error(
                "[%s] Dataframe does not match the columns requirements", self.NAME
            )
            return {}

        ip_reports = []

        try:
            df = self.df
            success_ips = df[df["auth_result"] == "success"]["source_ip"].unique()
            log.info(
                "[%s] Successful source IP addresses [%s]",
                self.NAME,
                " ".join(success_ips),
            )

            for source_ip in success_ips:
                log.info(
                    "[%s] Checking for successful auth for %s", self.NAME, source_ip
                )
                ip_report = self.login_analysis(source_ip=source_ip)
                if ip_report:
                    ip_reports.append(ip_report)
        except KeyError as exception:
            log.error("Error generating success IP address: %s", exception)
            return self.generate_analyzer_output(reports=ip_report, success=False)

        return self.generate_analyzer_output(reports=ip_reports, success=True)
