"""
Threaded sync runner + JS callback bridge.

A :class:`SyncProgressRunner` owns one or more background sync tasks.
Each task is given an ``emit`` callable; whatever it emits gets
serialized as JSON and pushed into the frontend via
``window.evaluate_js("window.granolaSync.onSyncProgress(<json>)")``.

Cancellation is cooperative: tasks are passed an ``is_cancelled``
callable they should poll.
"""

from __future__ import annotations

import json
import threading
import uuid
from typing import Callable


_JS_HANDLER = "window.granolaSync && window.granolaSync.onSyncProgress"


class SyncProgressRunner:
    def __init__(self, window):
        self._window = window
        self._cancel_flags: dict[str, threading.Event] = {}
        self._lock = threading.Lock()

    def start(
        self,
        task: Callable[..., None],
    ) -> str:
        """
        Kick off ``task`` in a background daemon thread.

        ``task`` is invoked as either ``task(emit)`` or
        ``task(emit, is_cancelled=...)`` (it can declare the second
        positional arg if it wants cancellation support).

        Returns a unique ``sync_id``.
        """
        sync_id = uuid.uuid4().hex
        cancel = threading.Event()
        with self._lock:
            self._cancel_flags[sync_id] = cancel

        def emit(event: dict) -> None:
            payload = json.dumps(event)
            # JS guard so we don't crash if window.granolaSync isn't set up yet
            self._window.evaluate_js(
                f"if ({_JS_HANDLER}) {_JS_HANDLER}({payload});"
            )

        def runner_target():
            try:
                # Pass is_cancelled only if the task asks for it
                import inspect
                params = inspect.signature(task).parameters
                if "is_cancelled" in params:
                    task(emit, is_cancelled=cancel.is_set)
                else:
                    task(emit)
            except Exception as exc:
                emit({"type": "error", "sync_id": sync_id, "message": str(exc)})
            finally:
                with self._lock:
                    self._cancel_flags.pop(sync_id, None)

        threading.Thread(target=runner_target, daemon=True).start()
        return sync_id

    def cancel(self, sync_id: str) -> bool:
        """Signal cancellation. Returns True if the sync was active."""
        with self._lock:
            flag = self._cancel_flags.get(sync_id)
        if flag is None:
            return False
        flag.set()
        return True
