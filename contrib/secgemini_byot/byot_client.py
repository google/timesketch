# Copyright 2026 Google Inc. All rights reserved.
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
"""Entrypoint script for the client-side SecGemini BYOT container."""

import asyncio
import inspect
import logging
import os
import sys

from fastmcp import FastMCP
from mcp.types import ToolAnnotations
from sec_gemini.byot import ByotService
from sec_gemini.logs_mcp.backends.sqlite import multi_db_tools
from timesketch_api_client import client as ts_client

from timesketch_logstore import DynamicLogStoreMap

# Setup logging to stdout
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("timesketch.byot.client")


def get_required_env(name: str) -> str:
    val = os.getenv(name)
    if not val:
        logger.error("Missing required environment variable: %s", name)
        sys.exit(1)
    return val


async def main():
    """Main execution function for the BYOT client container."""
    # Read configuration from environment
    timesketch_url = get_required_env("TIMESKETCH_URL")
    username = get_required_env("TIMESKETCH_USERNAME")
    password = get_required_env("TIMESKETCH_PASSWORD")
    secgemini_api_key = get_required_env("SEC_GEMINI_API_KEY")
    tunnel_name = os.getenv("TUNNEL_NAME", "byot-sec-gemini-bot")

    logger.info("Initializing Timesketch API client for %s...", timesketch_url)
    try:
        api = ts_client.TimesketchApi(
            host_uri=timesketch_url,
            username=username,
            password=password,
        )
        # Attempt to fetch list of sketches to verify connection/credentials
        sketches = list(api.list_sketches(scope="all"))
        logger.info(
            "Successfully authenticated. User has access to %d sketches.",
            len(sketches),
        )
    except Exception:  # pylint: disable=broad-exception-caught
        logger.exception("Failed to authenticate to Timesketch API")
        sys.exit(1)

    logger.info("Configuring LogStore map...")
    # Monkeypatch the SQLite multi_db_tools LOG_STORES map with our API
    # client-backed version.
    multi_db_tools.LOG_STORES = DynamicLogStoreMap(api)

    # Initialize FastMCP server
    logger.info("Setting up FastMCP server: %s", tunnel_name)
    mcp = FastMCP(tunnel_name)

    # Register the tools from multi_db_tools
    mcp.tool(
        description=inspect.getdoc(multi_db_tools.describe_available_logs),
        annotations=ToolAnnotations(readOnlyHint=True),
    )(multi_db_tools.describe_available_logs)

    mcp.tool(
        description=inspect.getdoc(multi_db_tools.search_logs),
        annotations=ToolAnnotations(readOnlyHint=True),
    )(multi_db_tools.search_logs)

    secgemini_host = os.getenv("SEC_GEMINI_HOST")

    # Initialize and start BYOT Tunnel Service
    logger.info("Starting BYOT reverse tunnel connection to SecGemini...")
    byot_kwargs = {
        "api_key": secgemini_api_key,
        "name": tunnel_name,
        "max_retries": -1,
    }
    if secgemini_host:
        logger.info("Using custom SecGemini Hub host: %s", secgemini_host)
        byot_kwargs["hub_url"] = secgemini_host

    byot = ByotService(**byot_kwargs)

    try:
        await byot.start(tools=[mcp])
        logger.info("Waiting for tunnel connection to establish...")
        await byot.wait_connected()
        logger.info("Tunnel connected successfully! Listening for tool calls...")

        # Keep running until terminated
        while True:
            await asyncio.sleep(3600)
    except asyncio.CancelledError:
        logger.info("Shutting down BYOT client...")
    except Exception:  # pylint: disable=broad-exception-caught
        logger.exception("BYOT service encountered an error")
    finally:
        await byot.stop()
        logger.info("BYOT client stopped.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Execution interrupted by user.")
