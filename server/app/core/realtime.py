import anyio
import asyncio
import json
import secrets
from datetime import datetime, timezone

from fastapi import WebSocket, WebSocketDisconnect

from .security import COOKIE, lookup


class EventHub:
    """Single-process delivery. Modules pass DB-derived recipients, never browser subscriptions."""
    def __init__(self):
        self.connections = {}

    async def publish(self, event_type, data, recipient_ids):
        if event_type not in {'submission.updated', 'exam.updated', 'session.updated'}:
            raise ValueError('Unsupported event type')
        event = {'event_id': secrets.token_urlsafe(16), 'type': event_type,
                 'occurred_at': datetime.now(timezone.utc).isoformat(), 'data': data}
        for websocket, (user_id, queue) in list(self.connections.items()):
            if user_id in recipient_ids:
                try:
                    queue.put_nowait(event)
                except asyncio.QueueFull:
                    # Client must reconnect and fetch REST state if it cannot keep up.
                    await websocket.close(1013)


async def websocket_endpoint(ws: WebSocket):
    app = ws.app
    user = await asyncio.to_thread(lookup, app, ws.cookies.get(COOKIE))
    if ws.headers.get('origin') not in app.state.settings.allowed_origins or not user or user.must_change_password:
        await ws.close(1008)
        return
    await ws.accept()
    from ..services.notifications import touch
    await asyncio.to_thread(touch, app, user.user_id)
    queue = asyncio.Queue(maxsize=100)
    app.state.hub.connections[ws] = (user.user_id, queue)
    heartbeat_id = None
    deadline = asyncio.get_running_loop().time() + app.state.settings.heartbeat_seconds
    receive = asyncio.create_task(ws.receive_text())
    outgoing = asyncio.create_task(queue.get())
    try:
        while True:
            remaining = max(0, deadline - asyncio.get_running_loop().time())
            done, _ = await asyncio.wait([receive, outgoing], timeout=remaining, return_when=asyncio.FIRST_COMPLETED)
            fresh = await asyncio.to_thread(lookup, app, ws.cookies.get(COOKIE))
            if not fresh or fresh.must_change_password:
                await ws.close(1008)
                return
            if receive in done:
                raw = receive.result()
                if len(raw.encode()) > 4096:
                    await ws.close(1009)
                    return
                try:
                    message = json.loads(raw)
                except (ValueError, TypeError):
                    await ws.close(1008)
                    return
                if not isinstance(message, dict) or not heartbeat_id or message.get('type') != 'heartbeat.ack' or message.get('id') != heartbeat_id:
                    await ws.close(1008)
                    return
                await asyncio.to_thread(touch, app, user.user_id)
                heartbeat_id = None
                deadline = asyncio.get_running_loop().time() + app.state.settings.heartbeat_seconds
                receive = asyncio.create_task(ws.receive_text())
            if outgoing in done:
                await ws.send_json(outgoing.result())
                outgoing = asyncio.create_task(queue.get())
            if asyncio.get_running_loop().time() >= deadline:
                if heartbeat_id:
                    await ws.close(1008)
                    return
                heartbeat_id = secrets.token_urlsafe(12)
                await ws.send_json({'type': 'heartbeat', 'id': heartbeat_id})
                deadline = asyncio.get_running_loop().time() + app.state.settings.heartbeat_timeout
    except (WebSocketDisconnect, asyncio.CancelledError):
        # Peer closure / ASGI shutdown may cancel a heartbeat DB touch in flight.
        pass
    except (RuntimeError, OSError):
        pass
    finally:
        app.state.hub.connections.pop(ws, None)
        for task in (receive, outgoing):
            task.cancel()
        with anyio.CancelScope(shield=True):
            await asyncio.gather(receive, outgoing, return_exceptions=True)
