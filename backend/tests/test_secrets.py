"""Tests for secret providers."""

import os
import tempfile
from pathlib import Path

from app.shared.secrets import (
    CompositeSecretProvider,
    EnvSecretProvider,
    FileSecretProvider,
)


class TestEnvSecretProvider:
    def test_get_existing_env(self) -> None:
        os.environ["TEST_SECRET_KEY"] = "test-value"
        try:
            provider = EnvSecretProvider()
            assert provider.get("TEST_SECRET_KEY") == "test-value"
        finally:
            del os.environ["TEST_SECRET_KEY"]

    def test_get_missing_env(self) -> None:
        provider = EnvSecretProvider()
        assert provider.get("NONEXISTENT_SECRET_KEY_12345") is None

    def test_get_missing_with_default(self) -> None:
        provider = EnvSecretProvider()
        assert provider.get("NONEXISTENT_SECRET_KEY_12345", "default") == "default"

    def test_has_existing(self) -> None:
        os.environ["TEST_SECRET_EXISTS"] = "yes"
        try:
            provider = EnvSecretProvider()
            assert provider.has("TEST_SECRET_EXISTS") is True
        finally:
            del os.environ["TEST_SECRET_EXISTS"]

    def test_has_missing(self) -> None:
        provider = EnvSecretProvider()
        assert provider.has("NONEXISTENT_SECRET_KEY_12345") is False


class TestFileSecretProvider:
    def test_get_from_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            secret_file = Path(tmpdir) / "my-secret"
            secret_file.write_text("file-secret-value\n")

            provider = FileSecretProvider(tmpdir)
            assert provider.get("my-secret") == "file-secret-value"

    def test_get_missing_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            provider = FileSecretProvider(tmpdir)
            assert provider.get("nonexistent") is None

    def test_get_missing_with_default(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            provider = FileSecretProvider(tmpdir)
            assert provider.get("nonexistent", "default") == "default"

    def test_has_existing(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "exists").write_text("value")
            provider = FileSecretProvider(tmpdir)
            assert provider.has("exists") is True

    def test_has_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            provider = FileSecretProvider(tmpdir)
            assert provider.has("nope") is False


class TestCompositeSecretProvider:
    def test_file_takes_precedence(self) -> None:
        os.environ["COMPOSITE_TEST"] = "env-value"
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                (Path(tmpdir) / "COMPOSITE_TEST").write_text("file-value")

                provider = CompositeSecretProvider(
                    [
                        FileSecretProvider(tmpdir),
                        EnvSecretProvider(),
                    ]
                )
                assert provider.get("COMPOSITE_TEST") == "file-value"
        finally:
            del os.environ["COMPOSITE_TEST"]

    def test_falls_back_to_env(self) -> None:
        os.environ["COMPOSITE_TEST2"] = "env-value"
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                provider = CompositeSecretProvider(
                    [
                        FileSecretProvider(tmpdir),
                        EnvSecretProvider(),
                    ]
                )
                assert provider.get("COMPOSITE_TEST2") == "env-value"
        finally:
            del os.environ["COMPOSITE_TEST2"]

    def test_returns_default_when_not_found(self) -> None:
        provider = CompositeSecretProvider(
            [
                EnvSecretProvider(),
            ]
        )
        assert provider.get("NONEXISTENT_12345", "fallback") == "fallback"
