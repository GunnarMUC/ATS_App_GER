from __future__ import annotations

import secrets

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

COOKIE_NAME = "csrf_token"
FORM_FIELD = "csrf_token"
HEADER_NAME = "x-csrf-token"
SAFE_METHODS = {"GET", "HEAD", "OPTIONS", "TRACE"}
EXEMPT_PREFIXES = ("/health", "/static")


def new_token() -> str:
    return secrets.token_urlsafe(32)


def _exempt(path: str) -> bool:
    return any(path == p or path.startswith(p + "/") for p in EXEMPT_PREFIXES)


def _provided_header(request: Request) -> str:
    return request.headers.get(HEADER_NAME) or request.headers.get("X-CSRF-Token") or ""


class CSRFMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        token = request.cookies.get(COOKIE_NAME) or new_token()
        request.state.csrf_token = token
        had_cookie = COOKIE_NAME in request.cookies

        if request.method not in SAFE_METHODS and not _exempt(request.url.path):
            provided = _provided_header(request)
            if not provided:
                ctype = request.headers.get("content-type") or ""
                if "application/x-www-form-urlencoded" in ctype or "multipart/form-data" in ctype:
                    form = await request.form()
                    provided = str(form.get(FORM_FIELD) or "")
            if not had_cookie or not provided or not secrets.compare_digest(provided, token):
                accept = request.headers.get("accept") or ""
                if "text/html" in accept:
                    return Response("CSRF-Prüfung fehlgeschlagen.", status_code=403)
                return JSONResponse(
                    {"error": "csrf_failed", "message": "CSRF-Token fehlt oder ungültig."},
                    status_code=403,
                )

        response = await call_next(request)
        if not had_cookie:
            response.set_cookie(
                COOKIE_NAME,
                token,
                httponly=False,
                samesite="strict",
                path="/",
            )
        return response
