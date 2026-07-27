"""Tests for task lifecycle state machine — TASK-0072."""

import pytest
from app.delivery.lifecycle import InvalidTransition, validate_transition


class TestValidateTransition:
    """Test every valid and invalid transition in the state machine."""

    # --- Valid transitions ---

    def test_backlog_to_ready(self):
        validate_transition("backlog", "ready")

    def test_backlog_to_cancelled(self):
        validate_transition("backlog", "cancelled")

    def test_ready_to_claimed(self):
        validate_transition("ready", "claimed")

    def test_ready_to_backlog(self):
        validate_transition("ready", "backlog")

    def test_ready_to_cancelled(self):
        validate_transition("ready", "cancelled")

    def test_claimed_to_in_progress(self):
        validate_transition("claimed", "in_progress")

    def test_claimed_to_backlog(self):
        """Claim released/expired reverts to backlog."""
        validate_transition("claimed", "backlog")

    def test_in_progress_to_done(self):
        validate_transition("in_progress", "done")

    def test_in_progress_to_blocked(self):
        validate_transition("in_progress", "blocked")

    def test_in_progress_to_needs_clarification(self):
        validate_transition("in_progress", "needs_clarification")

    def test_in_progress_to_ready_for_review(self):
        validate_transition("in_progress", "ready_for_review")

    def test_blocked_to_in_progress(self):
        validate_transition("blocked", "in_progress")

    def test_needs_clarification_to_in_progress(self):
        validate_transition("needs_clarification", "in_progress")

    def test_ready_for_review_to_done(self):
        validate_transition("ready_for_review", "done")

    def test_ready_for_review_to_changes_requested(self):
        validate_transition("ready_for_review", "changes_requested")

    def test_changes_requested_to_in_progress(self):
        validate_transition("changes_requested", "in_progress")

    # --- Invalid transitions ---

    def test_backlog_to_in_progress_invalid(self):
        with pytest.raises(InvalidTransition):
            validate_transition("backlog", "in_progress")

    def test_backlog_to_done_invalid(self):
        with pytest.raises(InvalidTransition):
            validate_transition("backlog", "done")

    def test_done_to_anything_invalid(self):
        with pytest.raises(InvalidTransition):
            validate_transition("done", "in_progress")

    def test_cancelled_to_anything_invalid(self):
        with pytest.raises(InvalidTransition):
            validate_transition("cancelled", "ready")

    def test_claimed_to_done_invalid(self):
        with pytest.raises(InvalidTransition):
            validate_transition("claimed", "done")

    def test_in_progress_to_backlog_invalid(self):
        with pytest.raises(InvalidTransition):
            validate_transition("in_progress", "backlog")

    def test_blocked_to_done_invalid(self):
        with pytest.raises(InvalidTransition):
            validate_transition("blocked", "done")

    def test_unknown_state_invalid(self):
        with pytest.raises(InvalidTransition):
            validate_transition("unknown", "ready")

    def test_to_unknown_state_invalid(self):
        with pytest.raises(InvalidTransition):
            validate_transition("ready", "unknown")
