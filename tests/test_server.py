import json
import threading
import unittest
from http.client import HTTPConnection
from urllib.parse import urlencode

from src.server import create_server


class ServerTests(unittest.TestCase):
    def setUp(self):
        self.server = create_server(host="127.0.0.1", port=0)
        self.server_thread = threading.Thread(
            target=self.server.serve_forever,
            daemon=True,
        )
        self.server_thread.start()
        self.connection = HTTPConnection(*self.server.server_address)

    def tearDown(self):
        self.connection.close()
        self.server.shutdown()
        self.server.server_close()
        self.server_thread.join()

    def test_homepage_contains_url_form_and_table_link(self):
        self.connection.request("GET", "/")
        response = self.connection.getresponse()
        body = response.read().decode("utf-8")

        self.assertEqual(response.status, 200)
        self.assertIn('<form action="/shorten" method="post">', body)
        self.assertIn('name="url"', body)
        self.assertIn('href="/table"', body)

    def test_submitting_url_shows_link_that_redirects_to_original(self):
        original_url = "https://example.com/a?x=1&y=two"
        self.connection.request(
            "POST",
            "/shorten",
            body=urlencode({"url": original_url}),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        response = self.connection.getresponse()
        body = response.read().decode("utf-8")

        self.assertEqual(response.status, 200)
        short_url = (
            f"http://{self.server.server_address[0]}:"
            f"{self.server.server_address[1]}/0"
        )
        self.assertIn(f'href="{short_url}">{short_url}</a>', body)

        self.connection.request("GET", "/0")
        redirect = self.connection.getresponse()
        redirect.read()

        self.assertEqual(redirect.status, 302)
        self.assertEqual(redirect.getheader("Location"), original_url)

    def test_table_shows_chained_nodes_and_horner_steps(self):
        for url in (
            "https://example.com/a",
            "https://example.com/i",
        ):
            self.connection.request(
                "POST",
                "/shorten",
                body=urlencode({"url": url}),
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            response = self.connection.getresponse()
            response.read()
            self.assertEqual(response.status, 200)

        self.connection.request("GET", "/table")
        response = self.connection.getresponse()
        body = response.read().decode("utf-8")

        self.assertEqual(response.status, 200)
        self.assertIn("URL 키", body)
        self.assertIn("짧은 코드", body)
        self.assertIn('aria-label="다음 노드">→', body)
        self.assertIn("<details>", body)
        self.assertIn("호너 해시 계산 과정", body)
        self.assertIn("ord(", body)
        self.assertIn("https://example.com/a", body)
        self.assertIn("https://example.com/i", body)

    def test_rejects_invalid_url_and_unknown_short_link(self):
        self.connection.request(
            "POST",
            "/shorten",
            body=urlencode({"url": "ftp://example.com/file"}),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        invalid_response = self.connection.getresponse()
        invalid_response.read()
        self.assertEqual(invalid_response.status, 400)

        self.connection.request("GET", "/unknown")
        missing_response = self.connection.getresponse()
        missing_response.read()
        self.assertEqual(missing_response.status, 404)

    def test_json_shortening_and_expand_endpoint(self):
        original_url = "https://example.com/json"
        self.connection.request(
            "POST",
            "/shorten",
            body=json.dumps({"url": original_url}),
            headers={"Content-Type": "application/json"},
        )
        response = self.connection.getresponse()
        payload = json.loads(response.read().decode("utf-8"))

        self.assertEqual(response.status, 200)
        self.assertEqual(payload["code"], "0")
        self.assertTrue(payload["short_url"].endswith("/0"))

        self.connection.request("GET", "/expand/0")
        expanded = self.connection.getresponse()
        expanded_payload = json.loads(expanded.read().decode("utf-8"))

        self.assertEqual(expanded.status, 200)
        self.assertEqual(expanded_payload["url"], original_url)


if __name__ == "__main__":
    unittest.main()
