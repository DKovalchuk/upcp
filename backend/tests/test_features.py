"""Tests for feature flags."""

import os

from app.shared.features import FeatureFlags, get_feature_flags


class TestFeatureFlags:
    def test_default_flags_are_all_false(self) -> None:
        flags = FeatureFlags()
        assert flags.public_registration is False
        assert flags.email_verification is False
        assert flags.oidc_auth is False
        assert flags.agent_auto_close is False
        assert flags.multi_org is False
        assert flags.webhooks is False

    def test_from_env_reads_environment(self) -> None:
        os.environ["UPCP_FEATURE_PUBLIC_REGISTRATION"] = "true"
        os.environ["UPCP_FEATURE_WEBHOOKS"] = "true"
        try:
            flags = FeatureFlags.from_env()
            assert flags.public_registration is True
            assert flags.webhooks is True
            assert flags.email_verification is False  # Not set
        finally:
            del os.environ["UPCP_FEATURE_PUBLIC_REGISTRATION"]
            del os.environ["UPCP_FEATURE_WEBHOOKS"]

    def test_from_env_case_insensitive(self) -> None:
        os.environ["UPCP_FEATURE_AGENT_AUTO_CLOSE"] = "True"
        try:
            flags = FeatureFlags.from_env()
            assert flags.agent_auto_close is True
        finally:
            del os.environ["UPCP_FEATURE_AGENT_AUTO_CLOSE"]

    def test_get_feature_flags_returns_singleton(self) -> None:
        import app.shared.features as mod

        mod._feature_flags = None  # Reset cache
        flags1 = get_feature_flags()
        flags2 = get_feature_flags()
        assert flags1 is flags2
