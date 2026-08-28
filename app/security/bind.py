from __future__ import annotations

import logging

from app.config import get_settings, is_loopback_host

logger = logging.getLogger("ats_app")


def assert_bind_is_loopback() -> None:
    settings = get_settings()
    if is_loopback_host(settings.app_host):
        return
    if settings.app_allow_nonlocal:
        logger.warning(
            "APP_HOST=%s is not loopback — APP_ALLOW_NONLOCAL=true, Bewerberdaten können im Netz erreichbar sein.",
            settings.app_host,
        )
        return
    raise RuntimeError(
        f"APP_HOST={settings.app_host} ist nicht Loopback. "
        "Start abgebrochen. Setzen Sie APP_ALLOW_NONLOCAL=true, um das bewusst zu erlauben."
    )
