"""Test-specific settings. Disables axes to prevent login lockout interference in non-axes tests."""
from .dev import *  # noqa: F401, F403

# django-axes: disable in test environment to prevent
# unrelated tests from triggering lockouts.
# Axes-specific tests use @override_settings(AXES_ENABLED=True) explicitly.
AXES_ENABLED = False
