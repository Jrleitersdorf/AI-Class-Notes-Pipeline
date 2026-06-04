"""Tests for src/granola_sync/progress.py — threaded sync + JS callbacks."""
import json
import threading
import time
from unittest.mock import MagicMock

import pytest

from granola_sync.progress import SyncProgressRunner


@pytest.fixture
def fake_window():
    return MagicMock()


def _wait_for(predicate, timeout=2.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if predicate():
            return True
        time.sleep(0.02)
    return False


def test_runner_emits_done_event_on_empty_sync(fake_window):
    runner = SyncProgressRunner(fake_window)
    sync_id = runner.start(lambda emit: emit({"type": "done", "sync_id": "x",
                                              "written": 0, "skipped": 0,
                                              "errors": 0, "elapsed_ms": 0}))
    assert sync_id

    assert _wait_for(lambda: fake_window.evaluate_js.called)
    call_arg = fake_window.evaluate_js.call_args[0][0]
    assert "onSyncProgress" in call_arg
    assert '"type": "done"' in call_arg


def test_runner_emits_error_event_on_exception(fake_window):
    runner = SyncProgressRunner(fake_window)
    def task(emit):
        raise RuntimeError("boom")
    runner.start(task)

    assert _wait_for(lambda: any(
        '"type": "error"' in c[0][0]
        for c in fake_window.evaluate_js.call_args_list
    ))


def test_runner_assigns_unique_sync_ids(fake_window):
    runner = SyncProgressRunner(fake_window)
    a = runner.start(lambda emit: None)
    b = runner.start(lambda emit: None)
    assert a != b


def test_runner_cancel_sets_flag(fake_window):
    runner = SyncProgressRunner(fake_window)
    seen_cancel = threading.Event()
    def task(emit, is_cancelled=lambda: False):
        # poll cancellation flag
        while not is_cancelled():
            time.sleep(0.01)
        seen_cancel.set()
    sync_id = runner.start(task)
    time.sleep(0.05)
    runner.cancel(sync_id)
    assert seen_cancel.wait(timeout=1.0)
