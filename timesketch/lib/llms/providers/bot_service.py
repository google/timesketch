"""Sec-Gemini Log Analyzer Bot Service for Timesketch."""

from __future__ import annotations

import asyncio
import logging
import os
import threading
from flask import Flask, request, jsonify
import requests

# pylint: disable=import-error
from sec_gemini.byot import ByotService
from sec_gemini.logs_mcp.backends.custom import mcp as custom_mcp
from fastmcp import FastMCP
from timesketch_api_client import client as ts_client

# Setup logger
logger = logging.getLogger("timesketch.bot_service")
logging.basicConfig(level=logging.INFO)

app = Flask("timesketch_mcp_bot")

# Track active BYOT services: session_id -> ByotService
active_tunnels = {}

# Background asyncio event loop running on a separate thread
_loop = asyncio.new_event_loop()


def start_background_loop():
    asyncio.set_event_loop(_loop)
    _loop.run_forever()


threading.Thread(target=start_background_loop, daemon=True).start()


def make_bot_timesketch_mcp(timesketch_url, session_cookie, sketch_id):
    """Create a FastMCP server configured with the user's credentials."""
    mcp = FastMCP(f"timesketch-logs-{sketch_id}")

    # Set up Timesketch API Client using the forwarded session cookie
    api = ts_client.TimesketchApi(
        host_uri=timesketch_url,
        username=None,
        create_session=False,
    )
    session = requests.Session()
    session.cookies.set("session", session_cookie)
    # Perform basic CSRF setup by replicating the standard setup
    session.headers.update({"referer": timesketch_url})
    api.set_session(session)

    # Resolve the sketch resource to validate authorization
    _ = api.get_sketch(sketch_id)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    script_path = os.path.join(script_dir, "timesketch_mcp.py")
    custom_mcp.make_mcp(mcp, f"{script_path} --sketch_id {sketch_id}")

    return mcp


async def start_tunnel_async(
    session_id, api_key, timesketch_url, session_cookie, sketch_id
):
    """Start the BYOT service reverse tunnel for a session in the background loop."""
    if session_id in active_tunnels:
        try:
            await active_tunnels[session_id].stop()
        except Exception:  # pylint: disable=broad-except
            pass
        active_tunnels.pop(session_id, None)

    logger.info(
        "Starting BYOT tunnel for session %s using client name: byot-%s",
        session_id,
        session_id,
    )
    byot = ByotService(
        api_key=api_key,
        name=f"byot-{session_id}",
        max_retries=-1,
    )
    mcp = make_bot_timesketch_mcp(timesketch_url, session_cookie, sketch_id)
    await byot.start(tools=[mcp])
    await byot.wait_connected(timeout=10.0)
    active_tunnels[session_id] = byot
    logger.info(
        "BYOT tunnel for session %s successfully established and connected.",
        session_id,
    )


async def stop_tunnel_async(session_id):
    """Stop the BYOT service reverse tunnel for a session."""
    if session_id in active_tunnels:
        logger.info("Stopping BYOT tunnel for session %s", session_id)
        byot = active_tunnels.pop(session_id)
        await byot.stop()
        logger.info("BYOT tunnel for session %s stopped.", session_id)


@app.route("/tunnel/start", methods=["POST"])
def start_tunnel():
    """Endpoint to start a new active BYOT tunnel connection."""
    data = request.json or {}
    session_id = data.get("session_id")
    api_key = data.get("api_key")
    timesketch_url = data.get("timesketch_url")
    session_cookie = data.get("session_cookie")
    sketch_id = data.get("sketch_id")

    if not all([session_id, api_key, timesketch_url, session_cookie, sketch_id]):
        return (
            jsonify({"status": "error", "message": "Missing required parameters"}),
            400,
        )

    future = asyncio.run_coroutine_threadsafe(
        start_tunnel_async(
            session_id, api_key, timesketch_url, session_cookie, sketch_id
        ),
        _loop,
    )
    try:
        future.result()
        return jsonify({"status": "success", "message": "Tunnel connected"})
    except Exception as e:  # pylint: disable=broad-except
        logger.exception("Failed to start BYOT tunnel")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/tunnel/stop", methods=["POST"])
def stop_tunnel():
    """Endpoint to stop an active BYOT tunnel connection."""
    data = request.json or {}
    session_id = data.get("session_id")

    if not session_id:
        return jsonify({"status": "error", "message": "Missing session_id"}), 400

    future = asyncio.run_coroutine_threadsafe(stop_tunnel_async(session_id), _loop)
    try:
        future.result()
        return jsonify({"status": "success", "message": "Tunnel stopped"})
    except Exception as e:  # pylint: disable=broad-except
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8008)
