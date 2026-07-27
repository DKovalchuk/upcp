"""Feature flags — runtime feature toggles."""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class FeatureFlags:
    """Feature flags loaded from environment variables.

    Convention: UPCP_FEATURE_<NAME>=true/false
    """

    public_registration: bool = False
    email_verification: bool = False
    oidc_auth: bool = False
    agent_auto_close: bool = False
    multi_org: bool = False
    webhooks: bool = False

    @classmethod
    def from_env(cls) -> "FeatureFlags":
        """Load feature flags from environment variables."""
        return cls(
            public_registration=os.environ.get("UPCP_FEATURE_PUBLIC_REGISTRATION", "false").lower()
            == "true",
            email_verification=os.environ.get("UPCP_FEATURE_EMAIL_VERIFICATION", "false").lower()
            == "true",
            oidc_auth=os.environ.get("UPCP_FEATURE_OIDC_AUTH", "false").lower() == "true",
            agent_auto_close=os.environ.get("UPCP_FEATURE_AGENT_AUTO_CLOSE", "false").lower()
            == "true",
            multi_org=os.environ.get("UPCP_FEATURE_MULTI_ORG", "false").lower() == "true",
            webhooks=os.environ.get("UPCP_FEATURE_WEBHOOKS", "false").lower() == "true",
        )


_feature_flags: FeatureFlags | None = None


def get_feature_flags() -> FeatureFlags:
    """Get cached feature flags."""
    global _feature_flags
    if _feature_flags is None:
        _feature_flags = FeatureFlags.from_env()
    return _feature_flags
