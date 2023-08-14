# Copyright 2023 Google Inc. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Interface for authentication analyzers."""

from datetime import datetime, timezone
from typing import List, Tuple, Optional

import copy
import logging

import pandas as pd

from timesketch.lib.analyzers.interface import AnalyzerOutput

log = logging.getLogger(__name__)


def human_timestamp(timestamp: int) -> str:
    """Converts unix timestamp to string.

    Args:
        timestamp (int): Unix epoch timestamps in seconds.

    Returns:
        str: A human readable timestamp in UTC.
    """

    return (
        datetime.fromtimestamp(timestamp)
        .astimezone(tz=timezone.utc)
        .strftime("%Y-%m-%dT%H:%M:%SZ")
    )


class LoginRecord:
    """Class to record successful login data.

    Attributes:
        timestamp (int): Timestamp of successful login event in seconds.
        session_id (str): Session ID or pseudo session ID for login event.
        session_duration(int): The length of the login session in seconds.
        source_ip (str): IP address of the system system.
        source_port (int): Source port used in authentication.
        username (str): User used for authentication.
        domain (str): Only used for Windows authentication.
        source_hostname (str): The hostname of the client. Only relevant for Windows.
    """

    def __init__(
        self, source_ip: str, session_id: str, username: str, domain: str = ""
    ) -> None:
        """Initialize LoginRecord.

        Args:
            source_ip (str): IP address that successfully logged in.
            session_id (str): A session ID for the login.
            username (str): Username that logged in.
            domain (str): Optional. Domain of the logged in user account.
        """

        self.timestamp = 0
        self.session_id = session_id
        self.session_duration = -1
        self.source_ip = source_ip
        self.source_port = 0
        self.username = username
        self.domain = domain
        self.source_hostname = ""


class AuthSummary:
    """Class for storing authentication summary.

    Attributes:
        summary_type (str): The keyword used in generating summary. Valid values are
            "source_ip" or "username".
        source_ip (str): IP address of the client.
        username (str): Username used in authentication.
        domain (str): Domain name. Only relevant for Windows.
        first_seen (int): Timestamp when the IP address was first seen.
        last_seen (int): Timestamp when the IP address was last seen.
        first_auth (LoginRecord): A LoginRecord for a first successful authentication
            from a given source_ip or for a given username.
        sucess_logins (List[LoginRecord]): A list of successful login records.
        success_source_ips (set): A set containing successful IP addresses.
        success_usernames (set): A set containing successful usernames.
        summary(dict): A dictionary containing analyzer specific information.
        total_success_events (int): Count of successful login events.
        total_failed_events (int): Count of failed login events.
        distinct_source_ip_count (int): The unique number of source_ip.
        distinct_username_count (int): The unique number of username observed for a
            a given source IP.
        top_source_ips (dict): Top 10 IP addresses observed in login events.
        top_usernames (dict): Top 10 usernames observed in login events.
    """

    def __init__(self) -> None:
        """Initialize AuthSummary."""

        self.summary_type = ""
        self.source_ip = ""
        self.username = ""
        self.domain = ""

        # Timestamp when IP address were first and last seen
        self.first_seen = 0
        self.last_seen = 0

        # Successful authentication
        self.first_auth = None
        self.successful_logins = []
        self.success_source_ips = set()
        self.success_usernames = set()

        self.summary = {}

        self.distinct_source_ip_count = 0
        self.distinct_username_count = 0
        self.total_success_events = 0
        self.total_failed_events = 0

        self.top_source_ips = {}
        self.top_usernames = {}

    def to_dict(self) -> dict:
        """Convert and return dict.

        Returns:
            dict: A dictionary of selected fields in AuthSummary object.
        """

        output = {
            "summary_type": self.summary_type,
            "source_ip": self.source_ip,
            "username": self.username,
            "domain": self.domain,
            "first_seen": self.first_seen,
            "last_seen": self.last_seen,
            "first_auth": self.first_auth.__dict__ if self.first_auth else [],
            "successful_logins": [login.__dict__ for login in self.successful_logins],
            "success_source_ips": list(self.success_source_ips),
            "success_usernames": list(self.success_usernames),
            "distinct_source_ip_count": self.distinct_source_ip_count,
            "distinct_username_count": self.distinct_username_count,
            "total_success_events": self.total_success_events,
            "total_failed_events": self.total_failed_events,
            "top_source_ips": self.top_source_ips,
            "top_usernames": self.top_usernames,
        }

        output["summary"] = {}
        if "bruteforce" in self.summary:
            output["summary"]["bruteforce"] = [
                login.__dict__ for login in self.summary["bruteforce"]
            ]

        return output


class BaseAuthenticationUtils:
    """Base authentication utils class.

    Attributes:
        df (pd.DataFrame): A dataframe containing authentication events.
    """

    REQUIRED_FIELDS = [
        "timestamp",
        "source_ip",
        "source_port",
        "username",
        "domain",
        "authentication_method",
        "authentication_result",
        "session_id",
    ]

    def __init__(self) -> None:
        """Initialize analyzer."""

        self.df = pd.DataFrame()

    def set_dataframe(self, df: pd.DataFrame) -> None:
        """Set base class datafame.

        Args:
            df (pd.DataFrame): A dataframe containing authentication events to process.

        Raises:
            AttributeError: If dataframe column does not meet required column.
            TypeError: If dataframe column data type does not meet the requirements.
        """

        column_list = df.columns.tolist()
        if not self.check_required_fields(column_list):
            log.error("Dataframe does not match required column")
            raise AttributeError("Dataframe does not meet required column")

        # Check data types for columns
        for column in column_list:
            if not df[column].dtype.name in [
                "str",
                "int64",
                "float64",
                "bool",
                "object",
            ]:
                log.error(
                    "[BaseAuthenticationUtils] Column %s has invalid data type %s",
                    column,
                    df[column].dtype.name,
                )
                raise TypeError("Dataframe column type does not meet required type")

        # Fill missing value
        df.fillna("", inplace=True)

        # Sort DataFrame by timestamp
        df.sort_values("timestamp", ascending=True, inplace=True)

        self.df = df

    def check_required_fields(self, fields: List[str]) -> bool:
        """Checks the required fields.

        Args:
            fields (List[str]): A list of dataframe columns.

        Returns:
            bool: Returns true if required fields exist.
        """

        missing_fields = set(self.REQUIRED_FIELDS) - set(fields)
        if missing_fields:
            log.debug(
                "[BaseAuthenticationUtils] Missing required fields %s.",
                missing_fields,
            )
            return False
        return True

    def calculate_session_duration(self, session_id: str, timestamp: int) -> int:
        """Calculates session duration for a session ID.

        Args:
            session_id (str): Authentication session ID for which session duration is
                calculated.
            timestamp (int): Timestamp when the login event occurred.

        Returns:
            int: Length of login session or -1 if valid session start/end is not
                found.
        """

        if not session_id or timestamp == 0:
            log.debug(
                "[BaseAuthenticationUtils] Session ID (%s) or timestamp (%d) is"
                " empty",
                session_id,
                timestamp,
            )
            return -1

        if self.df.empty:
            log.debug("[BaseAuthenticationUtils] Dataframe is empty")
            return -1
        df = self.df

        session_start_timestamp = 0
        try:
            session_start_timestamp = df[
                (df["session_id"] == session_id)
                & (df["authentication_result"] == "success")
                & (df["timestamp"] >= timestamp)
            ].iloc[0]["timestamp"]
        except (KeyError, ValueError, IndexError) as e:
            log.debug(
                "[BaseAuthenticationUtils] Error getting session start timestamp for"
                " session ID %s. %s",
                session_id,
                str(e),
            )
            return -1

        session_end_timestamp = 0
        try:
            session_end_timestamp = df[
                (df["session_id"] == session_id)
                & (df["event_type"] == "disconnection")
                & (df["timestamp"] >= timestamp)
            ].iloc[0]["timestamp"]
        except (KeyError, ValueError, IndexError) as e:
            log.debug(
                "[BaseAuthenticationUtils] Error getting session end timestamp for"
                " session ID %s. %s",
                session_id,
                str(e),
            )
            return -1

        return int(session_end_timestamp - session_start_timestamp)

    def get_ip_summary(self, source_ip: str) -> Optional[AuthSummary]:
        """Gets AuthSummary for source IP.

        Args:
            source_ip (str): Generate authentication summary for the IP.

        Returns:
            AuthSummary: AuthSummary for the IP address or None.
        """

        if self.df.empty:
            log.debug("[BaseAuthenticationUtils] Dataframe is empty")
            return None

        # Find all events for IP address
        df = self.df
        ip_df = df[df["source_ip"] == source_ip]
        if ip_df.empty:
            log.debug("[BaseAuthenticationUtils] No data for the IP %s", source_ip)
            return None

        return self.get_authsummary(
            df=ip_df, summary_type="source_ip", summary_value=source_ip
        )

    def get_user_summary(
        self, username: str, domain: str = ""
    ) -> Optional[AuthSummary]:
        """Generate AuthSummary for username.

        Args:
            username (str): Generate authentication summary for matching username and
                domain.
            domain (str): Generate authentication summary for matching username and
                domain.

        Returns:
            AuthSummary: Authentication summary for the given username and domain.
            None: Returns None if checks fail.
        """

        if self.df.empty:
            log.debug(
                "[BaseAuthenticationUtils] Dataframe for %s/%s is empty",
                domain,
                username,
            )
            return None
        df = self.df

        user_df = df[(df["username"] == username) & (df["domain"] == domain)]
        if user_df.empty:
            log.debug("[BaseAuthenticationUtils] No data for %s/%s", domain, username)
            return None

        user_df = user_df.sort_values(by="timestamp", ascending=True)

        useraccount = self.to_useraccount(username, domain)

        return self.get_authsummary(
            df=user_df, summary_type="username", summary_value=useraccount
        )

    def get_authsummary(
        self, df: pd.DataFrame, summary_type: str, summary_value: str
    ) -> Optional[AuthSummary]:
        """Get AuthSummary for summary type/value.

        Args:
            df (pd.DataFrame): A dataframe containing authentication events.
            summary_type (str): The column used to filter the dataframe.
            summary_value (str): The value of the column to filter the dataframe.

        Returns:
            AuthSummary: AuthSummary or None for given filter value.
            None: Returns None if checks fail.

        Raises:
            ValueError: If params provided to the function are empty.
        """

        if df.empty:
            log.debug("[BaseAuthenticationUtils] Dataframe is empty")
            return None

        if not summary_type:
            raise ValueError("summary_type is empty")

        if not summary_value:
            raise ValueError("summary_value is empty")

        summary_df = df[df[summary_type] == summary_value]
        if summary_df.empty:
            log.debug(
                "[BaseAuthenticationUtils] No data for %s=%s",
                summary_type,
                summary_value,
            )
            return None
        summary_df = summary_df.sort_values(by="timestamp", ascending=True)

        authsummary = AuthSummary()
        authsummary.summary_type = summary_type

        if summary_type == "source_ip":
            authsummary.source_ip = summary_value
        elif summary_type == "username":
            authsummary.username = summary_value
        else:
            log.debug(
                "[BaseAuthenticationUtils] Unsupported summary_type %s and value %s",
                summary_type,
                summary_value,
            )
            return None

        # First/last time IP/username was seen
        authsummary.first_seen = int(summary_df.iloc[0]["timestamp"])
        authsummary.last_seen = int(summary_df.iloc[-1]["timestamp"])

        # Collect successful logins
        success_df = summary_df[summary_df["authentication_result"] == "success"]
        success_df = success_df.reset_index()
        if success_df.empty:
            log.debug(
                "[BaseAuthenticationUtils] No successful events for %s: %s",
                summary_type,
                summary_value,
            )
            return authsummary

        for row in success_df.itertuples():
            login_record = LoginRecord(
                source_ip=row.source_ip,
                session_id=row.session_id,
                username=row.username,
                domain=row.domain,
            )
            login_record.timestamp = row.timestamp
            login_record.source_port = row.source_port
            login_record.session_duration = self.calculate_session_duration(
                session_id=row.session_id, timestamp=row.timestamp
            )

            authsummary.successful_logins.append(login_record)

            if row.Index == 0:
                authsummary.first_auth = copy.deepcopy(login_record)

        # Success list source_ip and username
        authsummary.success_source_ips = list(set(success_df["source_ip"].to_list()))
        authsummary.success_usernames = list(set(success_df["username"].to_list()))

        # Success/failed event count
        authsummary.total_success_events = len(success_df.index)
        authsummary.total_failed_events = len(
            summary_df[summary_df["authentication_result"] == "failure"].index
        )

        # Step 5: Stats on total number of unique IPs and usernames
        authsummary.distinct_source_ip_count = len(summary_df["source_ip"].unique())
        authsummary.distinct_username_count = len(summary_df["username"].unique())

        # Top 10 IP and username
        authsummary.top_source_ips = (
            summary_df.groupby(by="source_ip")["timestamp"]
            .nunique()
            .nlargest(10)
            .to_dict()
        )
        authsummary.top_usernames = (
            summary_df.groupby(by="username")["timestamp"]
            .nunique()
            .nlargest(10)
            .to_dict()
        )

        return authsummary

    def to_useraccount(self, username: str, domain: str) -> str:
        """Converts username and domain to user account.

        Args:
            username (str): Authenticating user name.
            domain (str): Authenticating user domain.

        Returns:
            str: Authenticating user account in form <domain>/<username>.
        """

        if not domain or domain.lower() == "nan":
            return username

        return f"{domain}/{username}"

    def from_useraccount(self, useraccount: str) -> Tuple[str, str]:
        """Converts useraccount to username and domain

        Args:
            useraccount (str): Useraccount information <domain>/<username>

        Returns:
            Tuple[username (str), domain (str)]:
                username (str): Authenticating user name.
                domain (str): Authentication user domain.

        Raises:
            ValueError: If error encountered access split value.
        """

        if not useraccount:
            return "", ""

        if not "/" in useraccount:
            return useraccount, ""

        try:
            values = useraccount.split("/")
            domain = values[0].strip()
            username = values[1].strip()
            return username, domain
        except ValueError as e:
            log.debug(
                "[BaseAuthenticationUtils] Failed converting useraccount to"
                " username and domain. %s",
                str(e),
            )
            return "unknown", "unknown"

    def get_login_record(
        self, source_ip: str, session_id: str, username: str, domain: str
    ) -> Optional[LoginRecord]:
        """Returns LoginRecord

        Args:
            source_ip (str): IP address that logged in.
            session_id (str): The session ID of the authentication event.
            username (str): The user name that logged in.
            domain (str): The domain name of the user that logged in.

        Returns:
            LoginRecord: A LoginRecord object for a login event.
            None: Returns None if checks fail.
        """

        if self.df.empty:
            log.debug("[BaseAuthenticationUtils] Dataframe is empty")
            return None

        df = self.df

        ip_df = df[
            (df["source_ip"] == source_ip)
            & (df["session_id"] == session_id)
            & (df["username"] == username)
            & (df["domain"] == domain)
        ]
        if ip_df.empty:
            log.debug(
                "[BaseAuthenticationUtils] No dataframe for IP: %s, session_id %s,"
                " domain %s, username %s",
                source_ip,
                session_id,
                domain,
                username,
            )
            return None

        login_df = ip_df[ip_df["authentication_result"] == "success"]
        if login_df.empty:
            log.debug(
                "[BaseAuthenticationUtils] No data for IP %s and session ID %s",
                source_ip,
                session_id,
            )
            return None

        login_timestamp = 0
        source_port = 0

        try:
            login_timestamp = int(login_df.iloc[0]["timestamp"])
            source_port = int(login_df.iloc[0]["source_port"])
        except (IndexError, KeyError) as e:
            log.debug("Unable to get login_timestamp or source_port. %s", str(e))
            return None

        logoff_timestamp = 0
        logoff_df = ip_df[ip_df["event_type"] == "disconnection"]
        if not logoff_df.empty:
            try:
                logoff_timestamp = int(logoff_df.iloc[0]["timestamp"])
            except (IndexError, KeyError, ValueError) as e:
                log.debug(
                    "[BaseAuthenticationUtils] Error encountered getting logoff"
                    " timestamp. %s",
                    str(e),
                )

        login_record = LoginRecord(
            source_ip=source_ip, session_id=session_id, username=username, domain=domain
        )
        login_record.source_port = source_port
        login_record.timestamp = login_timestamp

        if logoff_timestamp <= 0:
            login_record.session_duration = -1
        else:
            login_record.session_duration = logoff_timestamp - login_timestamp

        log.debug(
            "[BaseAuthenticationUtils] Login session duration for %s is %d",
            login_record.session_id,
            login_record.session_duration,
        )

        return login_record


class BruteForceUtils(BaseAuthenticationUtils):
    """Class for BruteForceUtils.

    Attributes:
        success_threshold (int): A number of successful events to confirm successful
            brute force activity.
        brute_force_window (int): The time duration before a successful login to
            evaluate for brute force activity.
        brute_force_min_failed_event (int): The minimum number of failed events
            that must occur to be considered for brute force activity.
        brute_force_min_access_window (int): The minimum duration where an attacker
            accessed the host after a successful brute force login would be
            considered as an interactive access.
    """

    # The time duration before a successful login to evaluate for brute force activity.
    BRUTE_FORCE_WINDOW = 3600

    # The minimum number of failed events that must occur to be considered for brute
    # force activity.
    BRUTE_FORCE_MIN_FAILED_EVENT = 20

    # The minimum duration where an attacker accessed the host after a successful
    # brute force login would be considered as an interactive access.
    BRUTE_FORCE_MIN_ACCESS_WINDOW = 300

    def __init__(
        self,
        brute_force_window: int = 3600,
        brute_force_min_failed_event: int = 20,
        brute_force_min_access_window: int = 300,
    ) -> None:
        """Initialize BruteForceUtils class.

        Args:
            brute_force_window (int): Duration of brute force window to check.
            brute_force_min_failed_event (int): Minimum failed events required to be a
                brute force activity.
            brute_force_min_access_window (int): Minimum session duration in seconds
                required to be interactive activity.
        """

        super().__init__()
        self.success_threshold = 1
        self.BRUTE_FORCE_WINDOW = brute_force_window
        self.BRUTE_FORCE_MIN_FAILED_EVENT = brute_force_min_failed_event
        self.BRUTE_FORCE_MIN_ACCESS_WINDOW = brute_force_min_access_window

    def set_success_threshold(self, threshold: int = 1) -> None:
        """Set a successful threshold.

        Args:
            threshold (int): A successful login threshold for events for brute force
                activity.
        """

        self.success_threshold = threshold

    def start_bruteforce_analysis(
        self, output: AnalyzerOutput
    ) -> Optional[AnalyzerOutput]:
        """Starts brute force analysis

        Returns:
            AnalyzerOutput: An AnalyzerOutput object containing brute force analyzer
                output.
            None: Returns None if checks fail.
        """

        df = self.df
        if df.empty:
            return None

        success_ips = []
        try:
            success_ips = df[df["authentication_result"] == "success"][
                "source_ip"
            ].unique()
        except KeyError as e:
            log.debug(
                "[BruteForceUtils] Missing required fields in dataframe. %s", str(e)
            )
            return None

        # Store list of AuthSummary
        authsummaries = []
        for source_ip in success_ips:
            log.debug(
                "[BruteForceUtils] Checking bruteforce activity from %s", source_ip
            )
            authsummary = self.ip_bruteforce_check(source_ip=source_ip)

            if not authsummary:
                log.debug("[BruteForceUtils] No bruteforce activity from %s", source_ip)
                continue

            authsummaries.append(authsummary)

        return self.generate_analyzer_output(authsummaries=authsummaries, output=output)

    def ip_bruteforce_check(self, source_ip: str) -> Optional[AuthSummary]:
        """Checks bruteforce activity for a given IP.

        Args:
            source_ip (str): Perform bruteforce checks from the IP address.

        Returns:
            AuthSummary: Authentication summary for IP address.
            None: Returns None if checks fail.
        """

        if not source_ip:
            log.debug("[BruteForceUtils] IP address not provided")
            return None

        if self.df.empty:
            log.debug("[BruteForceUtils] Dataframe is empty")
            return None
        df = self.df

        # Get the dataframe for the given IP address
        ip_df = df[df["source_ip"] == source_ip]
        if ip_df.empty:
            log.debug("[BruteForceUtils] No records for %s in dataframe", source_ip)
            return None

        # Get the successful events for the given IP address
        success_df = ip_df[ip_df["authentication_result"] == "success"]
        if success_df.empty:
            log.debug(
                "[BruteForceUtils] No successful authentication events for %s",
                source_ip,
            )
            return None

        bruteforce_logins = []

        for _, row in success_df.iterrows():
            login_ts = int(row.get("timestamp", 0))
            session_id = row.get("session_id", "")

            if login_ts == 0:
                log.warning(
                    "[BruteForceUtils] Unable to get timestamp for session %s",
                    session_id,
                )
                continue

            # Get the brute force window start and end timestamp
            bruteforce_window_start = login_ts - self.BRUTE_FORCE_WINDOW
            bruteforce_window_end = login_ts

            # Get the dataframe for the brute force window
            bruteforce_window_df = ip_df[
                (ip_df["timestamp"] >= bruteforce_window_start)
                & (ip_df["timestamp"] <= bruteforce_window_end)
                & (ip_df["source_ip"] == source_ip)
            ]

            log.debug(
                "[BruteForceUtils] %d records for %s between %s and %s",
                len(bruteforce_window_df.index),
                source_ip,
                human_timestamp(bruteforce_window_start),
                human_timestamp(bruteforce_window_end),
            )

            if bruteforce_window_df.empty:
                continue

            # Get the number of failed and successful authentication events in the brute
            # force window
            failure_count = len(
                bruteforce_window_df[
                    bruteforce_window_df["authentication_result"] == "failure"
                ].index
            )
            success_count = len(
                bruteforce_window_df[
                    bruteforce_window_df["authentication_result"] == "success"
                ].index
            )
            log.debug(
                "[BruteForceUtils] success_count: %d, failure_count: %d for %s",
                success_count,
                failure_count,
                source_ip,
            )

            if (
                0 < success_count <= self.success_threshold
                and failure_count >= self.BRUTE_FORCE_MIN_FAILED_EVENT
            ):
                login = self.get_login_record(
                    source_ip=source_ip,
                    username=row.get("username", ""),
                    domain=row.get("domain", ""),
                    session_id=row.get("session_id", ""),
                )
                if login:
                    login.source_hostname = row.get("source_hostname", "")
                    bruteforce_logins.append(login)

        if not bruteforce_logins:
            log.debug("[BruteForceUtils] No brute force activity from %s", source_ip)
            return None

        # Get authentication summary for the given IP address and update it to include
        # brute force logins.
        authsummary = self.get_ip_summary(source_ip=source_ip)
        if not authsummary:
            log.debug(
                "[BruteForceUtils] Unable to get authentication summary for %s",
                source_ip,
            )
            return None

        if not authsummary.summary:
            authsummary.summary = {}
        authsummary.summary["bruteforce"] = bruteforce_logins

        return authsummary

    def generate_analyzer_output(
        self, authsummaries: List[AuthSummary], output: AnalyzerOutput
    ) -> Optional[AnalyzerOutput]:
        """Generates analyzer output.

        Args:
            authsummaries (List[AuthSummary]): A list of AuthSummary objects.

        Returns:
            AnalyzerOutput: An AnalyzerOutput object containing brute for analyzer
                output.
            None: Returns None if authsummaries is empty.
        """

        if not authsummaries and not isinstance(authsummaries, list):
            return None

        authsummaries_count = len(authsummaries)
        if authsummaries_count == 0:
            output.result_priority = "NOTE"
            output.result_status = "SUCCESS"
            output.result_summary = "No bruteforce activity"
            output.result_markdown = (
                "\n### Brute Force Analyzer\nBrute force not detected"
            )
            return output

        # Check if any of the authsummaries have a session duration greater than the
        # the minimum access window.
        # If so, set the output's result priority to "HIGH".
        for authsummary in authsummaries:
            for login in authsummary.successful_logins:
                if login.session_duration >= self.BRUTE_FORCE_MIN_ACCESS_WINDOW:
                    output.result_priority = "HIGH"
                    break

        # Generate summary and markdown summary.
        result_summaries = []
        markdown_summaries = []

        for authsummary in authsummaries:
            bruteforce_logins = authsummary.summary.get("bruteforce", None)
            if not bruteforce_logins:
                continue

            result_summaries.append(
                f"{len(bruteforce_logins)} brute force from {authsummary.source_ip}"
            )

            markdown_summaries.append(
                f"\n### Brute Force Summary for {authsummary.source_ip}"
            )
            for login in bruteforce_logins:
                if login.session_duration >= self.BRUTE_FORCE_MIN_ACCESS_WINDOW:
                    markdown_summaries.append(
                        f"\n- Potentially actor activity - long active session"
                        f" {login.session_duration} seconds"
                    )
                markdown_summaries.append(
                    f"- Successful brute force on {human_timestamp(login.timestamp)}"
                    f" as {login.username}"
                )

                markdown_summaries.append(f"\n#### {authsummary.source_ip} Summary")
                markdown_summaries.append(
                    f"- IP first seen on {human_timestamp(authsummary.first_seen)}"
                )
                markdown_summaries.append(
                    f"- IP last seen on {human_timestamp(authsummary.last_seen)}"
                )

                if authsummary.first_auth:
                    markdown_summaries.append(
                        f"- First successful authentication on"
                        f" {human_timestamp(authsummary.first_auth.timestamp)}"
                    )
                    markdown_summaries.append(
                        f"- First successful login from"
                        f" {authsummary.first_auth.source_ip}"
                    )
                    markdown_summaries.append(
                        f"- First successful login as {authsummary.first_auth.username}"
                    )

                if authsummary.top_usernames:
                    markdown_summaries.append("\n#### Top Usernames")
                    for username, count in authsummary.top_usernames.items():
                        markdown_summaries.append(f"- {username}: {count}")

        if result_summaries:
            output.result_summary = ", ".join(result_summaries)
            output.result_priority = "HIGH"

        if markdown_summaries:
            markdown_summaries.insert(0, "\n### Brute Force Analyzer")
            output.result_markdown = "\n".join(markdown_summaries)

        output.result_status = "SUCCESS"
        output.result_attributes = {"bruteforce": authsummaries}

        return output
