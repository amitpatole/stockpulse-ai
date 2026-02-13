"""
StockPulse AI v3.0 - OpenClaw WebSocket Bridge
Connects to a local OpenClaw Gateway via WebSocket for agent task delegation.
Gracefully falls back if OpenClaw is not running or websocket-client is not installed.
"""

import json
import logging
import time
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from backend.agents.base import AgentResult

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# Graceful websocket import
# ------------------------------------------------------------------
try:
    import websocket as ws_client
    WEBSOCKET_AVAILABLE = True
except ImportError:
    WEBSOCKET_AVAILABLE = False
    ws_client = None
    logger.info("websocket-client not installed -- OpenClaw bridge unavailable. "
                "Install with: pip install websocket-client")


class OpenClawBridge:
    """WebSocket bridge to the OpenClaw Gateway.

    Connects to ws://127.0.0.1:18789 (configurable via Config) and
    delegates agent tasks for execution by the OpenClaw multi-agent
    orchestration layer.

    All operations are wrapped in try/except so the rest of the
    application continues even if OpenClaw is unreachable.
    """

    def __init__(self, gateway_url: Optional[str] = None,
                 webhook_token: Optional[str] = None):
        # Read from Config if not provided
        try:
            from backend.config import Config
            self._gateway_url = gateway_url or Config.OPENCLAW_GATEWAY_URL
            self._webhook_token = webhook_token or Config.OPENCLAW_WEBHOOK_TOKEN
        except ImportError:
            self._gateway_url = gateway_url or "ws://127.0.0.1:18789"
            self._webhook_token = webhook_token or ""

        self._ws: Optional[Any] = None
        self._connected = False
        self._pending_tasks: Dict[str, Dict[str, Any]] = {}

    # ------------------------------------------------------------------
    # Connection management
    # ------------------------------------------------------------------

    def connect(self) -> bool:
        """Establish a WebSocket connection to the OpenClaw Gateway.
        Returns True on success, False otherwise."""
        if not WEBSOCKET_AVAILABLE:
            logger.warning("Cannot connect to OpenClaw: websocket-client not installed")
            return False

        if self._connected and self._ws:
            return True

        try:
            headers = {}
            if self._webhook_token:
                headers["Authorization"] = f"Bearer {self._webhook_token}"

            self._ws = ws_client.create_connection(
                self._gateway_url,
                header=headers,
                timeout=10,
            )
            self._connected = True
            logger.info(f"Connected to OpenClaw Gateway at {self._gateway_url}")
            return True
        except Exception as e:
            logger.warning(f"Failed to connect to OpenClaw Gateway: {e}")
            self._connected = False
            self._ws = None
            return False

    def disconnect(self):
        """Close the WebSocket connection."""
        if self._ws:
            try:
                self._ws.close()
            except Exception as e:
                logger.debug(f"Error closing OpenClaw WebSocket: {e}")
            finally:
                self._ws = None
                self._connected = False
                logger.info("Disconnected from OpenClaw Gateway")

    def is_available(self) -> bool:
        """Check if the OpenClaw Gateway is reachable.
        Attempts a quick connect/disconnect if not already connected."""
        if not WEBSOCKET_AVAILABLE:
            return False

        if self._connected and self._ws:
            # Verify the connection is still alive
            try:
                self._ws.ping()
                return True
            except Exception:
                self._connected = False
                self._ws = None

        # Try a quick connection test
        try:
            test_ws = ws_client.create_connection(
                self._gateway_url,
                timeout=3,
            )
            test_ws.close()
            return True
        except Exception:
            return False

    # ------------------------------------------------------------------
    # Task submission & result polling
    # ------------------------------------------------------------------

    def send_task(self, agent_name: str, task_description: str,
                  inputs: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """Send a task to the OpenClaw Gateway.

        Parameters
        ----------
        agent_name : str
            Name of the agent to execute the task.
        task_description : str
            Natural-language description of the task.
        inputs : dict, optional
            Key-value inputs for the task.

        Returns
        -------
        str or None
            A unique task_id if successful, or None on failure.
        """
        if not self._connected:
            if not self.connect():
                logger.error("Cannot send task: not connected to OpenClaw")
                return None

        task_id = str(uuid.uuid4())
        payload = {
            "jsonrpc": "2.0",
            "method": "tasks/send",
            "id": task_id,
            "params": {
                "agent_name": agent_name,
                "task_description": task_description,
                "inputs": inputs or {},
                "metadata": {
                    "source": "stockpulse-ai",
                    "timestamp": datetime.utcnow().isoformat(),
                },
            },
        }

        if self._webhook_token:
            payload["params"]["auth_token"] = self._webhook_token

        try:
            self._ws.send(json.dumps(payload))
            self._pending_tasks[task_id] = {
                "agent_name": agent_name,
                "sent_at": datetime.utcnow().isoformat(),
                "status": "sent",
            }
            logger.info(f"Sent task {task_id} to OpenClaw for agent '{agent_name}'")
            return task_id
        except Exception as e:
            logger.error(f"Failed to send task to OpenClaw: {e}")
            self._connected = False
            return None

    def poll_result(self, task_id: str, timeout: float = 60.0) -> AgentResult:
        """Poll the OpenClaw Gateway for a task result.

        Parameters
        ----------
        task_id : str
            The task ID returned by send_task().
        timeout : float
            Maximum seconds to wait for the result.

        Returns
        -------
        AgentResult
        """
        started_at = datetime.utcnow().isoformat()
        start_time = time.time()

        if not self._connected or not self._ws:
            return AgentResult(
                agent_name=self._pending_tasks.get(task_id, {}).get("agent_name", "unknown"),
                framework="openclaw",
                status="error",
                output="",
                error="Not connected to OpenClaw Gateway",
                started_at=started_at,
                completed_at=datetime.utcnow().isoformat(),
            )

        agent_name = self._pending_tasks.get(task_id, {}).get("agent_name", "unknown")

        try:
            # Set receive timeout
            self._ws.settimeout(min(timeout, 5.0))

            while time.time() - start_time < timeout:
                try:
                    raw = self._ws.recv()
                    if not raw:
                        time.sleep(0.5)
                        continue

                    message = json.loads(raw)

                    # Check if this is a response to our task
                    msg_id = message.get("id")
                    if msg_id != task_id:
                        # Not our task -- could be a heartbeat or other task
                        continue

                    # Parse the result
                    result_data = message.get("result", {})
                    error_data = message.get("error")

                    if error_data:
                        return AgentResult(
                            agent_name=agent_name,
                            framework="openclaw",
                            status="error",
                            output="",
                            error=json.dumps(error_data) if isinstance(error_data, dict) else str(error_data),
                            duration_ms=int((time.time() - start_time) * 1000),
                            started_at=started_at,
                            completed_at=datetime.utcnow().isoformat(),
                        )

                    output_text = result_data.get("output", "")
                    tokens_in = result_data.get("tokens_input", 0)
                    tokens_out = result_data.get("tokens_output", 0)

                    return AgentResult(
                        agent_name=agent_name,
                        framework="openclaw",
                        status="success",
                        output=output_text,
                        raw_output=result_data,
                        tokens_input=tokens_in,
                        tokens_output=tokens_out,
                        estimated_cost=result_data.get("estimated_cost", 0.0),
                        duration_ms=int((time.time() - start_time) * 1000),
                        started_at=started_at,
                        completed_at=datetime.utcnow().isoformat(),
                        metadata=result_data.get("metadata", {}),
                    )

                except ws_client.WebSocketTimeoutException:
                    # Timeout on recv -- loop and try again
                    continue
                except Exception as e:
                    logger.debug(f"Error receiving from OpenClaw: {e}")
                    time.sleep(0.5)

            # Timeout reached
            return AgentResult(
                agent_name=agent_name,
                framework="openclaw",
                status="error",
                output="",
                error=f"Timeout after {timeout}s waiting for OpenClaw result",
                duration_ms=int((time.time() - start_time) * 1000),
                started_at=started_at,
                completed_at=datetime.utcnow().isoformat(),
            )

        except Exception as e:
            logger.error(f"Error polling OpenClaw result: {e}")
            return AgentResult(
                agent_name=agent_name,
                framework="openclaw",
                status="error",
                output="",
                error=str(e),
                duration_ms=int((time.time() - start_time) * 1000),
                started_at=started_at,
                completed_at=datetime.utcnow().isoformat(),
            )

    # ------------------------------------------------------------------
    # Convenience: send + poll in one call
    # ------------------------------------------------------------------

    def run_task(self, agent_name: str, task_description: str,
                 inputs: Optional[Dict[str, Any]] = None,
                 timeout: float = 60.0) -> AgentResult:
        """Send a task and wait for the result.

        This is a blocking convenience method that combines send_task()
        and poll_result().
        """
        task_id = self.send_task(agent_name, task_description, inputs)
        if task_id is None:
            return AgentResult(
                agent_name=agent_name,
                framework="openclaw",
                status="error",
                output="",
                error="Failed to send task to OpenClaw (not connected or send failed)",
            )
        return self.poll_result(task_id, timeout)

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    def __del__(self):
        self.disconnect()

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
        return False
