"""HTTP web interface for the in-memory URL shortener."""

import argparse
from html import escape
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from pathlib import Path
import sys
from urllib.parse import parse_qsl, unquote, urlsplit

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT))

from src.shortener import URLShortener

_MAX_REQUEST_SIZE = 65536


def _page(title, content):
    return (
        "<!doctype html><html lang=\"ko\"><head><meta charset=\"utf-8\">"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">"
        f"<title>{title}</title><style>"
        "body{font-family:system-ui,sans-serif;max-width:960px;margin:2rem auto;"
        "padding:0 1rem;color:#202124}input{box-sizing:border-box;padding:.7rem;"
        "width:min(100%,40rem)}button{padding:.7rem 1rem;margin-top:.7rem}"
        "a{overflow-wrap:anywhere}.bucket{padding:.8rem;border-bottom:1px solid #ddd}"
        ".node{display:inline-block;border:1px solid #8a9bad;border-radius:.5rem;"
        "padding:.7rem;margin:.5rem;vertical-align:top;max-width:28rem;overflow-wrap:anywhere}"
        ".arrow{font-size:1.4rem;color:#526579}code{overflow-wrap:anywhere}"
        "details{margin-top:.6rem}li{margin:.25rem 0}"
        "</style></head><body>"
        f"<h1>{title}</h1>{content}</body></html>"
    )


def _hash_calculation(key, bucket_count):
    value = 0
    steps = []
    for character in key:
        previous = value
        value = (value * 31 + ord(character)) % bucket_count
        steps.append(
            f"<li><code>h = ({previous} * 31 + ord({_html_escape(repr(character))})) "
            f"% {bucket_count} = {value}</code></li>"
        )
    return "".join(steps), value


def _base_url(headers):
    host = headers.get("Host", "localhost:8000")
    try:
        parsed_host = urlsplit(f"//{host}")
        valid_host = (
            parsed_host.netloc == host
            and bool(parsed_host.hostname)
            and parsed_host.username is None
            and parsed_host.password is None
            and not parsed_host.path
            and not parsed_host.query
            and not parsed_host.fragment
            and not any(character.isspace() for character in host)
        )
    except ValueError:
        valid_host = False
    if not valid_host:
        host = "localhost:8000"

    forwarded_scheme = headers.get("X-Forwarded-Proto", "http").split(",", 1)[0]
    scheme = forwarded_scheme.strip().lower()
    if scheme not in ("http", "https"):
        scheme = "http"
    return f"{scheme}://{host}"


def _short_path(strategy, code):
    prefix = "c" if strategy == "chaining" else "l"
    return f"/{prefix}/{_html_escape(code)}"


def _table_page(shortener, base_url, strategy):
    table = shortener._url_to_code
    bucket_count = len(table._buckets)
    if strategy == "chaining":
        algorithm_name = "개별 체이닝"
    else:
        algorithm_name = "선형 탐지"
    content = (
        f"<p>{algorithm_name} 방식의 URL 키 해시 테이블입니다.</p>"
        f"<p>버킷 수: {bucket_count} · 저장된 URL: {table.size}</p>"
        '<p><a href="/table?strategy=chaining">개별 체이닝</a> · '
        '<a href="/table?strategy=linear">선형 탐지</a> · '
        '<a href="/">새 URL 줄이기</a></p>'
    )

    for bucket_index, head in enumerate(table._buckets):
        content += (
            f"<section class=\"bucket\"><strong>"
            f"{'버킷' if strategy == 'chaining' else '칸'} {bucket_index}</strong>: "
        )
        if head is None:
            content += "<span>비어 있음</span></section>"
            continue

        node = head
        first = True
        while node is not None:
            if strategy == "chaining" and not first:
                content += '<span class="arrow" aria-label="다음 노드">→</span>'
            code = node.value
            escaped_url = _html_escape(node.key)
            short_path = _short_path(strategy, code)
            content += (
                f'<article class="node"><strong>URL 키</strong>: {escaped_url}<br>'
                f'<strong>짧은 코드</strong>: <code>{_html_escape(code)}</code><br>'
                f'<strong>짧은 링크</strong>: '
                f'<a href="{short_path}">{_html_escape(base_url)}'
                f'{short_path}</a>'
            )
            steps, calculated_bucket = _hash_calculation(node.key, bucket_count)
            if strategy == "linear":
                probe_path = " → ".join(str(slot) for slot in table.probe_path(node.key))
                content += (
                    f"<details><summary>호너 해시와 탐지 경로 "
                    f"(시작 칸 {calculated_bucket})</summary>"
                    f"<ol>{steps}</ol><p>확인한 칸: {probe_path}</p>"
                    "</details></article>"
                )
                node = None
            else:
                content += (
                    f"<details><summary>호너 해시 계산 과정 "
                    f"(최종 버킷 {calculated_bucket})</summary>"
                    f"<ol>{steps}</ol></details></article>"
                )
                node = node.next
            first = False
        content += "</section>"

    return _page(f"현재 해시 테이블 · {algorithm_name}", content)


def _html_escape(value):
    return escape(value, quote=True)


def create_server(host="0.0.0.0", port=8000, shortener=None):
    """Create an HTTP server with both collision strategies."""
    chaining_app = (
        shortener
        if shortener is not None and shortener.collision_strategy == "chaining"
        else URLShortener("chaining")
    )
    linear_app = (
        shortener
        if shortener is not None and shortener.collision_strategy == "linear"
        else URLShortener("linear")
    )
    apps = (("chaining", chaining_app), ("linear", linear_app))

    def app_for(strategy):
        for app_strategy, app in apps:
            if app_strategy == strategy:
                return app
        raise ValueError(f"unknown collision strategy: {strategy}")

    class RequestHandler(BaseHTTPRequestHandler):
        def _respond(self, status, body, content_type="text/html; charset=utf-8"):
            encoded_body = body.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(encoded_body)))
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(encoded_body)

        def do_GET(self):
            parsed_path = urlsplit(self.path)
            path = parsed_path.path

            if path == "/":
                content = (
                    "<p>긴 URL을 입력하면 짧은 링크를 만들어 드립니다.</p>"
                    '<form action="/shorten" method="post">'
                    '<label for="url">원래 URL</label><br>'
                    '<input id="url" name="url" type="url" '
                    'placeholder="https://example.com/path" required>'
                    '<br><label for="strategy">충돌 처리 방식</label><br>'
                    '<select id="strategy" name="strategy">'
                    '<option value="chaining">개별 체이닝</option>'
                    '<option value="linear">선형 탐지</option>'
                    '</select>'
                    '<br><button type="submit">줄이기</button></form>'
                    '<p><a href="/table?strategy=chaining">체이닝 테이블 보기</a> · '
                    '<a href="/table?strategy=linear">선형 탐지 테이블 보기</a></p>'
                )
                self._respond(200, _page("URL 단축기", content))
                return

            if path == "/table":
                query = parse_qsl(parsed_path.query, keep_blank_values=True)
                strategy = "chaining"
                for name, value in query:
                    if name == "strategy":
                        strategy = value
                        break
                if strategy not in ("chaining", "linear"):
                    self._respond(
                        400,
                        _page("잘못된 방식", "<p>해시 충돌 처리 방식을 확인해 주세요.</p>"),
                    )
                    return
                self._respond(
                    200,
                    _table_page(
                        app_for(strategy),
                        _base_url(self.headers),
                        strategy,
                    ),
                )
                return

            if path.startswith("/expand/") and path.count("/") == 2:
                code = unquote(path[len("/expand/"):])
                query = parse_qsl(parsed_path.query, keep_blank_values=True)
                strategy = "chaining"
                for name, value in query:
                    if name == "strategy":
                        strategy = value
                        break
                if strategy not in ("chaining", "linear"):
                    self._respond(400, '{"error":"invalid strategy"}', "application/json; charset=utf-8")
                    return
                try:
                    original_url = app_for(strategy).expand(code)
                except ValueError:
                    self._respond(404, '{"error":"unknown code"}', "application/json; charset=utf-8")
                    return
                body = '{"url":' + json.dumps(original_url, ensure_ascii=False) + "}"
                self._respond(200, body, "application/json; charset=utf-8")
                return

            if (
                path.startswith("/c/")
                or path.startswith("/l/")
            ) and path.count("/") == 2:
                strategy = "chaining" if path.startswith("/c/") else "linear"
                code = unquote(path[3:])
                try:
                    original_url = app_for(strategy).expand(code)
                except ValueError:
                    self._respond(404, _page("링크를 찾을 수 없음", "<p>등록되지 않은 짧은 링크입니다.</p>"))
                    return

                self.send_response(302)
                self.send_header("Location", original_url)
                self.send_header("Content-Length", "0")
                self.end_headers()
                return

            if path.startswith("/") and path.count("/") == 1 and len(path) > 1:
                code = unquote(path[1:])
                try:
                    original_url = app_for("chaining").expand(code)
                except ValueError:
                    self._respond(404, _page("링크를 찾을 수 없음", "<p>등록되지 않은 짧은 링크입니다.</p>"))
                    return

                self.send_response(302)
                self.send_header("Location", original_url)
                self.send_header("Content-Length", "0")
                self.end_headers()
                return

            self._respond(404, _page("페이지를 찾을 수 없음", "<p>요청한 페이지가 없습니다.</p>"))

        def do_POST(self):
            if urlsplit(self.path).path != "/shorten":
                self._respond(404, _page("페이지를 찾을 수 없음", "<p>요청한 페이지가 없습니다.</p>"))
                return

            try:
                content_length = int(self.headers.get("Content-Length", ""))
            except ValueError:
                self._respond(400, _page("잘못된 요청", "<p>요청 본문 길이가 올바르지 않습니다.</p>"))
                return
            if content_length < 0 or content_length > _MAX_REQUEST_SIZE:
                self._respond(413, _page("요청이 너무 큼", "<p>요청 본문이 너무 큽니다.</p>"))
                return

            try:
                body = self.rfile.read(content_length).decode("utf-8")
                if self.headers.get_content_type() == "application/json":
                    fields = json.loads(body, object_pairs_hook=lambda pairs: pairs)
                    if not isinstance(fields, list) or any(
                        not isinstance(field, tuple)
                        or len(field) != 2
                        or not isinstance(field[0], str)
                        for field in fields
                    ):
                        raise ValueError("JSON body must be an object")
                else:
                    fields = parse_qsl(body, keep_blank_values=True, max_num_fields=20)
            except (UnicodeDecodeError, ValueError):
                self._respond(400, _page("잘못된 요청", "<p>폼 데이터를 읽을 수 없습니다.</p>"))
                return

            urls = [value for name, value in fields if name == "url"]
            strategies = [value for name, value in fields if name == "strategy"]
            if len(urls) != 1:
                self._respond(400, _page("잘못된 요청", "<p>URL을 하나 입력해 주세요.</p>"))
                return

            strategy = strategies[0] if strategies else "chaining"
            if len(strategies) > 1 or strategy not in ("chaining", "linear"):
                self._respond(
                    400,
                    _page("잘못된 방식", "<p>해시 충돌 처리 방식을 선택해 주세요.</p>"),
                )
                return

            try:
                code = app_for(strategy).shorten(urls[0])
            except ValueError:
                self._respond(400, _page("잘못된 URL", "<p>HTTP 또는 HTTPS 주소를 입력해 주세요.</p>"))
                return

            short_path = _short_path(strategy, code)
            if self.headers.get_content_type() == "application/json":
                short_url = f"{_base_url(self.headers)}{short_path}"
                body = (
                    '{"code":'
                    + json.dumps(code, ensure_ascii=False)
                    + ',"short_url":'
                    + json.dumps(short_url, ensure_ascii=False)
                    + "}"
                )
                self._respond(200, body, "application/json; charset=utf-8")
                return

            short_url = f"{_base_url(self.headers)}{short_path}"
            content = (
                "<p>짧은 링크가 준비되었습니다.</p>"
                f'<p><a href="{short_url}">{short_url}</a></p>'
                '<p><a href="/">다른 URL 줄이기</a> · '
                '<a href="/table">해시 테이블 보기</a></p>'
            )
            self._respond(200, _page("줄이기 완료", content))

    return HTTPServer((host, port), RequestHandler)


def main():
    parser = argparse.ArgumentParser(description="Run the URL shortener web server.")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    arguments = parser.parse_args()

    server = create_server(arguments.host, arguments.port)
    print(f"URL shortener listening on http://{arguments.host}:{arguments.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
