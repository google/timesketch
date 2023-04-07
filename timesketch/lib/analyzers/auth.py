# -*- coding: utf-8 -*-
# Copyright 2023 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#            http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Base authentication analyzer"""

from datetime import datetime, timezone
from typing import List, Tuple

import copy
import logging

import pandas as pd

from timesketch.lib.analyzers.analyzer_output import AnalyzerOutput
from timesketch.lib.analyzers.analyzer_output import Priority

log = logging.getLogger("timesketch")


class LoginRecord:
    """Successful login record.

    Attributes:
        timestamp (int): Timestamp of successful login event in seconds.
        session_id (str): Session ID or pseudo session ID for login event.
        session_duration (int): The length of the login session in seconds.
        source_hostname (str): The hostname of the source system. Only available
                on Windows for certain login events.
        source_ip (src): Source IP address observed in the login event.
        source_port (int): Source port observed in the login event.
        domain (str): Domain name observed in the login event. Only available on
                Windows login events.
        username (str): Username observed in the login event.
    """

    def __init__(self, source_ip: str, domain: str, username: str,
                 session_id: str) -> None:
        self.timestamp = None
        self.session_id = session_id
        self.session_duration = None
        self.source_ip = source_ip
        self.source_hostname = ""
        self.source_port = None
        self.domain = domain
        self.username = username


class AuthSummaryData:
    """Authentication summary data.

    Attributes:
        summary_type (str): The keyword used in generating summary. Valid values
                are source_ip and username.
        source_ip (str): Source IP used in logon events.
        domain (str): Domain name used in logon events. Only applicable to
                Windows logon events.
        username (str): Username used in logon events.
        first_seen (int): Time in seconds when user or source_ip was first seen.
        last_seen (int): Time in seconds when user or source_ip was last seen.
        first_auth (LoginRecord): Login record for the first successful login.
                This does not have to be a brute force login.
        brute_forces (List[LoginRecord]): A list of successful brute force logins.
        successful_logins (List[LoginRecord]): A list of successful LoginRecord.
                This includes brute force logon events.
        success_source_ip_list (List[str]): List of IP addresses that
                successfully logged on to the system.
        total_success_events (int): Count of successful logon events.
        total_failed_events (int): Count of failed logon events.
        distinct_source_ip_count (int): Distinct count of source IP addresses.
        distinct_username_count (int): Distinct count of usernames.
        top_source_ip (dict): Top 10 source IP addresses observed in logon
                events. This includes successful and failed logon events.
        top_username (dict): Top 10 username observed in logon events. This
                includes successful and failed logon events.
    """

    def __init__(self):
        # Summary information for source_ip or username
        self.summary_type = None
        self.source_ip = ""
        self.domain = ""
        self.username = ""

        # The first time the source_ip or username is observed in auth events.
        # This can be a successful or failed login event.
        self.first_seen = 0

        # The last time the source_ip or username was observed in auth events.
        # This can be a successful or failed login event.
        self.last_seen = 0

        # The first time the source_ip or username successfully logged in.
        self.first_auth = None

        # Successful bruteforce records
        self.brute_forces = []

        # Successful logins records
        self.successful_logins = []

        # The list of IP addresses that successfully authenticated to the
        # system. This is used when summary_type is a username.
        self.success_source_ip_list = []
        self.success_username_list = []

        self.total_success_events = 0
        self.total_failed_events = 0

        # The total number of unique IP addresses observed in the log.
        self.distinct_source_ip_count = 0
        self.distinct_username_count = 0

        self.top_source_ips = {}
        self.top_usernames = {}

    def to_dict(self) -> dict:
        """Returns AuthSummaryData as dict.

        Returns:
                dict: A dictionary of AuthSummaryData.
        """
        obj = copy.deepcopy(self)
        output = obj.__dict__

        if self.first_auth:
            output["first_auth"] = self.first_auth.__dict__

        logins = []
        for login in self.successful_logins:
            logins.append(login.__dict__)
        if logins:
            output["successful_logins"] = logins

        bruteforces = []
        for bruteforce in self.brute_forces:
            bruteforces.append(bruteforce.__dict__)
        if bruteforces:
            output["brute_forces"] = bruteforces
        return output

class AuthAnalyzerException(Exception):
    """Authentication Analyzer Exception"""

class AuthAnalyzer:
    """Analyzer for authentication analysis.

    Attributes:
        name (str): Analyzer short name
        display_name (str): Display name of the analyzer
        description (str): Brief description about the analyzer
        df (pd.DataFrame): Authentication dataframe
    """
    NAME = "AuthAnalyzer"

    REQUIRED_ATTRIBUTES = [
            "timestamp", "event_type", "auth_method", "auth_result", "hostname",
            "source_ip", "source_port", "source_hostname", "domain", "username",
            "session_id"
    ]

    def __init__(self, name: str, display_name: str, description: str) -> None:
        """Initialization of authentication analyzer.

        Args:
            name (str): Analyzer short name
            display_name (str): Analyzer display name
            description (str): Brief description of the analyzer
        """
        if not name:
            raise AuthAnalyzerException("Analyzer name is required")
        if not display_name:
            raise AuthAnalyzerException("Analyzer display name is required")

        self.name = name
        self.display_name = display_name
        self.description = description
        self.df = pd.DataFrame()

    def set_dataframe(self, df: pd.DataFrame) -> bool:
        """Validates dataframe columns and sets dataframe.

        Validates dataframe has required columns for authentication analysis and
        sets the dataframe.

        Args:
            df (pd.DataFrame): Dataframe containing authentication events.

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
        """Checks the required fields in the dataframe.

        Args:
            fields (List[str]): List of columns name in dataframe

        Returns:
            bool: Returns true if required fields exist
        """

        for req_field in self.REQUIRED_ATTRIBUTES:
            if req_field not in fields:
                log.error("Missing required field %s", req_field)
                return False
        return True

    def session_duration(self, session_id: str, timestamp: int) -> int:
        """Calculates session duration for a session ID.

        Args:
            session_id (str): Authentication event session ID.
            timestamp (int): Authentication event timestamp.

        Returns:
            int: Length of login session or -1 if no valid session start time
                    or end time is found.
        """
        if not session_id or timestamp == 0:
            log.info("[%s] Session ID (%s) or timestamp (%d) is empty.",
                     self.NAME, session_id, timestamp)
            return -1

        if self.df.empty:
            log.info("[%s] Dataframe is empty", self.NAME)
            return -1
        df = self.df

        session_start_ts = 0
        try:
            session_start_ts = df[(df["session_id"] == session_id)
                    & (df["auth_result"] == "success")
                    & (df["timestamp"] >= timestamp)].iloc[0]["timestamp"]
        except (KeyError, ValueError, IndexError) as e:
            log.error("[%s] Error getting session start time for %s. %s",
                      self.NAME, session_id, str(e))
            return -1

        session_end_ts = 0
        try:
            session_end_ts = df[(df["session_id"] == session_id)
                    & (df["event_type"] == "disconnection")
                    & (df["timestamp"] >= timestamp)].iloc[0]["timestamp"]
        except (KeyError, ValueError, IndexError) as e:
            log.error("[%s] Error getting session end time for %s. %s",
                      self.NAME, session_id, str(e))
            return -1

        return int(session_end_ts - session_start_ts)

    def get_ip_summary(self, source_ip: str) -> AuthSummaryData:
        """Returns AuthSummaryData for a source IP.

        Args:
            source_ip (str): Source IP address whose summary will be generated.

        Returns:
            AuthSummaryData: AuthSummaryData object for source IP or None.
        """
        if self.df.empty:
            log.info("Source data frame is empty")
            return None
        df = self.df

        srcip_df = df[df["source_ip"] == source_ip]
        if srcip_df.empty:
            log.info("No data for source ip %s", source_ip)
            return None
        return self.get_auth_summary(
                df=srcip_df, summary_type="source_ip", value=source_ip)

    def get_user_summary(self, domain: str, username: str) -> AuthSummaryData:
        """Returns AuthSummaryData for a given domain/username.

        Args:
            domain (str): Filter dataframe using domain.
            username (str): Filter dataframe using username.

        Returns:
            AuthSummaryData: AuthSummaryData object for username or None.
        """
        if self.df.empty:
            log.info("[%s] Source data frame is empty", self.NAME)
            return None
        df = self.df

        username_df = df[(df["domain"] == domain) & (df["username"] == username)]
        if username_df.empty:
            log.info(
                "[%s] User summary dataframe for domain %s and username %s is empty",
                self.NAME, domain, username)
            return None

        username_df.sort_values(by="timestamp", ascending=True)

        useraccount = self.to_useraccount(domain, username)
        return self.get_auth_summary(
                df=username_df, summary_type="username", value=useraccount)

    def get_auth_summary(
            self, df: pd.DataFrame, summary_type: str, value: str) -> AuthSummaryData:
        """Returns AuthSummaryData for the given attribute/value pair.

        Args:
            summary_type (str): Summary type to filter source_ip or username.
            value (str): Value for the summary_type i.e. username or IP address.

        Returns:
            AuthSummaryData: AuthSummaryData or None for the given key-value.
        """
        log.debug(
                "[%s] Checking auth summary for %s:%s", self.NAME, summary_type, value)

        if df.empty:
            log.info("[%s] Dataframe is empty", self.NAME)
            return None

        if not summary_type:
            raise AuthAnalyzerException("[{self.NAME}] Summary type is empty")
        if not value:
            raise AuthAnalyzerException(
                f"[{self.NAME}] Value for summary type {summary_type} is empty")

        auth_summary_df = df[df[summary_type] == value]
        if auth_summary_df.empty:
            log.info("No dataframe for %s: %s", summary_type, value)
            return None
        auth_summary_df.sort_values(by="timestamp", ascending=True)

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
            return None

        # Step 1: First and last authentication event for IP address or useraccount
        summary.first_seen = int(auth_summary_df.iloc[0]["timestamp"])
        summary.last_seen = int(auth_summary_df.iloc[-1]["timestamp"])

        # Step 2: Collect details about successful login events.
        success_df = auth_summary_df[auth_summary_df["auth_result"] == "success"]
        success_df = success_df.reset_index()
        if success_df.empty:
            log.info(
                    "[%s] No successful events for %s: %s", self.NAME, summary_type,
                    value)
            return summary

        for i, row in success_df.iterrows():
            row_timestamp = int(row.get("timestamp", 0))
            row_source_ip = row.get("source_ip", "")
            row_domain = row.get("domain", "")
            row_username = row.get("username", "")
            row_session_id = row.get("session_id", "")

            login_record = LoginRecord(
                    source_ip=row_source_ip, domain=row_domain, username=row_username,
                    session_id=row_session_id)
            login_record.timestamp = row_timestamp
            login_record.source_port = int(row.get("source_port", 0))
            login_record.session_duration = self.session_duration(
                    row_session_id, row_timestamp)

            # Populating successful login
            summary.successful_logins.append(login_record)

            # Collect information about first login event
            if i == 0:
                summary.first_auth = copy.deepcopy(login_record)

        # Step 3: Successful IP address and usernames
        summary.success_source_ip_list = list(
                set(success_df["source_ip"].to_list()))
        summary.success_username_list = list(set(success_df["username"].to_list()))

        # Step 4: Stats on success and failed events
        summary.total_success_events = len(success_df.index)
        summary.total_failed_events = len(
                auth_summary_df[auth_summary_df["auth_result"] == "failure"].index)

        # Step 5: Stats on total number of unique IPs and usernames
        summary.distinct_source_ip_count = len(
                auth_summary_df["source_ip"].unique())
        summary.distinct_username_count = len(auth_summary_df["username"].unique())

        # Step 6: Top 10 IP addresses and usernames observed
        summary.top_source_ips = auth_summary_df.groupby(
                by="source_ip")["timestamp"].nunique().nlargest(10).to_dict()
        summary.top_usernames = auth_summary_df.groupby(
                by="username")["timestamp"].nunique().nlargest(10).to_dict()

        return summary

    def to_useraccount(self, domain: str, username: str) -> str:
        """Converts domain and username to useraccount.

        Args:
            domain (str): Domain name if available.
            username (str): Username of the account.

        Returns:
            str: Returns useraccount in format DOMAIN\\USERNAME.
        """
        # Pandas dataframe value check: NaN (Not a Number)
        if not domain or domain.lower() == "nan":
            return username
        return f"{domain}\\{username}"

    def from_useraccount(self, useraccount: str) -> Tuple[str, str]:
        """Splits useraccount into domain and username.

        Args:
            useraccount (str): Useraccount as DOMAIN\\USERNAME.

        Returns:
            Tuple[str, str]: Returns domain and username.
        """
        if not useraccount:
            return "", ""

        if not "\\" in useraccount:
            return "", useraccount

        val = useraccount.split("\\")
        try:
            domain = val[0].strip()
            username = val[1].strip()
            return domain, username
        except ValueError:
            return "", useraccount

    def human_timestamp(self, timestamp: int) -> str:
        """Converts epoch timestamp to human readable date/time.

        Args:
            timestamp (int): Timestamp in seconds.

        Returns:
            str: String timestamp in format YYYY-MM-DD HH:MM:SS.
        """
        return datetime.fromtimestamp(timestamp).astimezone(
                tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    def get_login_session(
            self, source_ip: str, domain: str, username: str,
            session_id: str) -> LoginRecord:
        """Returns LoginRecord as per parameter.

        Args:
            source_ip (str): Source IP address used in collecting login sessions.
            domain (str): Domain of the login user.
            username (str): Username of the login user.
            session_id (str): Pseudo session ID for the login event.

        Returns:
            LoginRecord: Login details as LoginRecord object or None.
        """
        NAME = "get_login_session"

        if self.df.empty:
            log.debug("[%s] Source data frame is empty.", NAME)
            return None
        df = self.df

        log.debug(
                "[%s] Checking login session for %s, domain %s, username %s, and "
                "session %s", self.NAME, source_ip, domain, username, session_id)

        ip_df = df[(df["source_ip"] == source_ip)
                             & (df["domain"] == domain)
                             & (df["username"] == username)
                             & (df["session_id"] == session_id)]
        if ip_df.empty:
            log.debug(
                    "[%s] No dataframe for source_ip: %s, domain: %s, username: %s, "
                    "session_id: %s", NAME, source_ip, domain, username, session_id)
            return None

        login_df = ip_df[ip_df["auth_result"] == "success"]
        if login_df.empty:
            log.debug(
                    "[%s] No successful login for IP %s and session ID %s", NAME,
                    source_ip, session_id)
            return None

        login_ts = 0
        source_port = 0
        try:
            login_ts = int(login_df.iloc[0]["timestamp"])
            source_port = int(login_df.iloc[0]["source_port"])
        except (IndexError, KeyError) as exception:
            log.error(
                    "[%s] Error getting login timestamp for session ID %s. %s", NAME,
                    session_id, str(exception))
            return None

        # Calculating logoff timestamp
        logoff_ts = 0

        logoff_df = ip_df[ip_df["event_type"] == "disconnection"]
        if logoff_df.empty:
            log.debug(
                    "[%s] No disconnect event for session ID for %s", NAME, session_id)
        else:
            try:
                logoff_ts = int(logoff_df.iloc[0]["timestamp"])
            except (IndexError, KeyError, ValueError) as exception:
                log.error(
                    "[%s] Error getting logoff timestamp for session ID %s. %s",
                    NAME, session_id, str(exception))

        login_session = LoginRecord(
                source_ip=source_ip, domain=domain, username=username,
                session_id=session_id)
        login_session.source_port = source_port

        login_session.timestamp = login_ts
        if logoff_ts <= 0:
            login_session.session_duration = -1
        else:
            login_session.session_duration = logoff_ts - login_ts

        log.debug(
                "[%s] Login session duration for %s is %d", self.NAME,
                login_session.session_id, login_session.session_duration)
        return login_session


class BruteForceAnalyzer(AuthAnalyzer):
    """Analyzer for brute force authentication."""

    NAME = "bruteforce.auth.analyzer"
    DISPLAY_NAME = "Brute Force Analyzer"
    DESCRIPTION = "This analyzer identifies brute force authentication"

    # The time duration before a successful login event to evaluate for
    # brute force activity.
    BRUTE_FORCE_WINDOW = 3600

    # The minimum number of failed events that must occur to be considered
    # for brute force activity.
    BRUTE_FORCE_MIN_FAILED_EVENT = 20

    # The time duration, in seconds, between successive authentication
    # events to be considered for brute force activity.
    BRUTE_FORCE_NEXT_LOGIN_DELTA = 10

    # The minimum duration where the attacker accessed the host after
    # a successful brute for login to be considered for interactive access.
    BRUTE_FORCE_MIN_ACCESS_DURATION = 300

    def __init__(self):
        """Initialize brute force analyzer."""
        super().__init__(self.NAME, self.DISPLAY_NAME, self.DESCRIPTION)

    def login_analysis(self, source_ip: str) -> AuthSummaryData:
        """Performs brute force analysis for the given source IP.

        Args:
            source_ip (str): Check brute force activity from source_ip

        Returns:
            AuthSummaryData: An object of AuthSummaryData or None
        """
        if not source_ip:
            log.info("[%s] Source IP is empty", self.NAME)
            return None

        if self.df.empty:
            log.info("[%s] Source data frame is empty", self.NAME)
            return None
        df = self.df

        source_df = df[(df["source_ip"] == source_ip)]
        if source_df.empty:
            log.info(
                "[%s] Login analysis dataframe for %s is empty", self.NAME,
                source_ip)
            return None

        success_df = source_df[source_df["auth_result"] == "success"]
        if success_df.empty:
            log.info("[%s] No successful login data for %s", self.NAME, source_ip)
            return None

        authsummarydata = None

        for _, row in success_df.iterrows():
            # Successful login timestamp
            login_ts = row["timestamp"]
            log.debug(
                    "[%s] Successful login for %s at %s", self.NAME, source_ip,
                    self.human_timestamp(login_ts))

            # Calculating time window for brute for analysis before login.
            start_timestamp = login_ts - self.BRUTE_FORCE_WINDOW
            end_timestamp = login_ts
            log.debug(
                    "[%s] Checking brute force from %s between %s and %s", self.NAME,
                    source_ip, self.human_timestamp(start_timestamp),
                    self.human_timestamp(end_timestamp))

            # Calculating number of successful and failed events for source_ip
            bruteforce_window_df = source_df[
                    (source_df["timestamp"] >= start_timestamp)
                    & (source_df["timestamp"] <= end_timestamp) &
                    (source_df["source_ip"] == source_ip)]
            bf_stat_df = bruteforce_window_df.groupby(
                    by="auth_result")["timestamp"].count()

            success_count = 0
            try:
                success_count = bf_stat_df["success"]
            except KeyError:
                # NOTE: KeyError occurs if there is no successful event in the
                #  dataframe.
                log.info(
                        "[%s] No successful login events from source IP %s", self.NAME,
                        source_ip)

            failed_count = 0
            try:
                failed_count = bf_stat_df["failure"]
            except KeyError:
                # NOTE: KeyError occurs if there is no failed event in the dataframe.
                log.info("[%s] No failed login events for %s.", self.NAME, source_ip)

            log.debug(
                    "[%s] Login events distribution from %s:"
                    " successful %d, failure %d", self.NAME, source_ip, success_count,
                    failed_count)

            # The success_count calculates the number of successful login before
            # the most recent login. For a bruteforce login, success_count MUST
            #  be one and failed_count MUST be greater than equal to
            # BRUTE_FORCE_MIN_FAILED_EVENT.
            #
            # This code block checks for condition that does not meet brute force
            # requirements.
            if (success_count != 1 or
                    failed_count < self.BRUTE_FORCE_MIN_FAILED_EVENT):
                log.debug(
                        "[%s] Brute force threshold not met. success_count: %d, "
                        "failed_count: %d", self.NAME, success_count, failed_count)
                continue

            if not authsummarydata:
                authsummarydata = self.get_ip_summary(source_ip=source_ip)

            # Collect information related to successful brute force
            row_domain = row.get("domain", "")
            row_username = row.get("username", "")
            row_session_id = row.get("session_id", "")

            login_record = self.get_login_session(
                    source_ip=source_ip, domain=row_domain, username=row_username,
                    session_id=row_session_id)

            authsummarydata.brute_forces.append(login_record)

        return authsummarydata

    def generate_analyzer_output(self, summaries: List[AuthSummaryData],
                                 analyzer_success: bool) -> AnalyzerOutput:
        """Generates brute force analyzer output.

        Args:
            summaries (List[AuthSummaryData]): List of summary information about
                    brute force IP.
            analyzer_success (bool): Indicate if the analyzer executed
                    successfully.

        Returns:
            AnalyzerOutput: An object of AnalyzerOuput.
        """
        output = AnalyzerOutput(
                analyzer_id=self.NAME,
                analyzer_name=self.DISPLAY_NAME,
        )

        if not analyzer_success:
            output.result_status = "Failed"
            output.result_summary = "Unable to complete analysis"
            return output

        summary_count = len(summaries)
        if summary_count == 0:
            output.result_summary = "No brute force activity"
            output.result_markdown = (
                    "\n#### Brute Force Analyzer\nNo brute force detected")
            return output

        result_summaries = []
        markdown_summaries = []

        priority = Priority.LOW

        for summary in summaries:
            result_summaries.append(
                    f"{len(summary.brute_forces)} brute force from {summary.source_ip}")

            for login in summary.successful_logins:
                if login.session_duration >= self.BRUTE_FORCE_MIN_ACCESS_DURATION:
                    if priority > Priority.CRITICAL:
                        priority = Priority.CRITICAL

            # Markdown report generation
            markdown_summaries.append(
                    f"\n##### Brute Force Summary for {summary.source_ip}")
            for login in summary.brute_forces:
                if login.session_duration >= self.BRUTE_FORCE_MIN_ACCESS_DURATION:
                    markdown_summaries.append(
                        f"\n**Potential actor activity**: Long login session"
                        f"{login.session_duration}\n")

                markdown_summaries.append(
                    f"- Successful brute force on "
                    f"{self.human_timestamp(login.timestamp)} as {login.username}")

                markdown_summaries.append(f"\n###### {summary.source_ip} Summary")
                markdown_summaries.append(
                    f"- IP first seen on {self.human_timestamp(summary.first_seen)}")
                markdown_summaries.append(
                    f"- IP last seen on {self.human_timestamp(summary.last_seen)}")

                if summary.first_auth:
                    markdown_summaries.append(
                        f"- First successful auth on "
                        f"{self.human_timestamp(summary.first_auth.timestamp)}")
                    markdown_summaries.append(
                        f"- First successful source IP: {summary.first_auth.source_ip}")
                    markdown_summaries.append(
                        f"- First successful username: {summary.first_auth.username}")

                if summary.top_usernames:
                    markdown_summaries.append("\n###### Top Usernames")
                    for username, count in summary.top_usernames.items():
                        markdown_summaries.append(f"- {username}: {count}")

        if result_summaries:
            output.result_summary = ", ".join(result_summaries)
            if priority > Priority.HIGH:
                priority = Priority.HIGH

        if markdown_summaries:
            markdown_summaries.insert(0, "\n#### Brute Force Analyzer")
            output.result_markdown = "\n".join(markdown_summaries)

        output.result_priority = priority.name
        output.attributes = summaries

        output.validate()
        return output

    def run(self, df: pd.DataFrame) -> AnalyzerOutput:
        """Entry point for the analyzer.

        Args:
            df (pd.DataFrame): Panda dataframe with authentication data

        Returns:
            AnalyzerOutput: AnalyzerOutput object or None.
        """
        if df.empty:
            raise AuthAnalyzerException("[{self.NAME}] Dataframe is empty")

        if not self.set_dataframe(df):
            log.error(
                    "[%s] Dataframe does not match the columns requirements", self.NAME)
            return None
        df = self.df

        try:
            success_ips = df[df["auth_result"] == "success"]["source_ip"].unique()
            log.debug(
                    "[%s] Successful source IP addresses %s", self.NAME,
                    ", ".join(success_ips))
        except KeyError as exception:
            log.error("Error generating success IP address: %s", str(exception))
            return None

        reports = []

        for source_ip in success_ips:
            log.info("[%s] Checking for successful auth for %s", self.NAME, source_ip)
            report = self.login_analysis(source_ip=source_ip)
            if not report:
                log.debug("[%s] No report for source IP %s", self.NAME, source_ip)
                continue
            reports.append(report)

        if not reports:
            return None
        return self.generate_analyzer_output(
                summaries=reports, analyzer_success=True)
