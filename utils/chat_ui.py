from __future__ import annotations

import re

import os

from starlette.types import ASGIApp, Message, Receive, Scope, Send

# ---------------------------------------------------------------------------
# HTML middleware: inject base-path configuration
# ---------------------------------------------------------------------------


class ChatBasePathMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app
        self.base_path = f"/{os.environ.get('PARTICIPANT_NAME')}/proxy/7932"

    async def __call__(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
    ) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Each request has its own response state.
        response_start: Message | None = None
        body_chunks: list[bytes] = []
        rewrite_html = False

        async def wrapped_send(message: Message) -> None:
            nonlocal response_start, body_chunks, rewrite_html

            if message["type"] == "http.response.start":
                headers = dict(message.get("headers", []))
                content_type = headers.get(b"content-type", b"")

                rewrite_html = (
                    b"text/html" in content_type and message.get("status", 200) == 200
                )

                if rewrite_html:
                    response_start = message
                    body_chunks = []
                    return

                await send(message)
                return

            if message["type"] == "http.response.body" and rewrite_html:
                body_chunks.append(message.get("body", b""))

                if message.get("more_body", False):
                    return

                assert response_start is not None
                html = b"".join(body_chunks)

                config = f"""
                <script>
                (() => {{
                    const prefix = {self.base_path!r};
                    const originalFetch = window.fetch;

                    function rewriteUrl(value) {{
                        const url = new URL(value, window.location.href);

                        if (
                            url.origin === window.location.origin &&
                            (url.pathname === "/api" || url.pathname.startsWith("/api/"))
                        ) {{
                            url.pathname = prefix + url.pathname;
                        }}

                        return url.href;
                    }}

                    window.fetch = function(input, init) {{
                        if (input instanceof Request) {{
                            const url = rewriteUrl(input.url);

                            if (url !== input.url) {{
                                input = new Request(url, input);
                            }}
                        }} else {{
                            input = rewriteUrl(String(input));
                        }}

                        return originalFetch.call(this, input, init);
                    }};

                    const originalOpen = XMLHttpRequest.prototype.open;

                    XMLHttpRequest.prototype.open = function(
                        method, url, ...args
                    ) {{
                        return originalOpen.call(
                            this, method, rewriteUrl(String(url)), ...args
                        );
                    }};
                }})();
                </script>
                """.encode()

                # Inject configuration before the frontend scripts execute.
                html, _count = re.subn(
                    rb"(<head\b[^>]*>)",
                    lambda match: match.group(1) + config,
                    html,
                    count=1,
                    flags=re.IGNORECASE,
                )

                headers = [
                    (key, value)
                    for key, value in response_start.get("headers", [])
                    if key.lower()
                    not in (b"content-length", b"content-encoding", b"etag")
                ]

                headers.append((b"content-length", str(len(html)).encode("ascii")))

                await send(
                    {
                        **response_start,
                        "headers": headers,
                    }
                )
                await send(
                    {
                        "type": "http.response.body",
                        "body": html,
                        "more_body": False,
                    }
                )
                rewrite_html = False
                return

            await send(message)

        await self.app(scope, receive, wrapped_send)
