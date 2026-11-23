import unittest

from src.shortener import URLShortener


class URLShortenerTests(unittest.TestCase):
    def test_shorten_and_expand_new_url(self):
        shortener = URLShortener()
        url = "https://example.com/a/path?query=value"

        code = shortener.shorten(url)

        self.assertEqual(shortener.expand(code), url)

    def test_shortening_same_url_reuses_code(self):
        shortener = URLShortener()
        url = "https://example.com/"

        first_code = shortener.shorten(url)
        second_code = shortener.shorten(url)

        self.assertEqual(second_code, first_code)

    def test_rejects_urls_without_http_scheme_or_host(self):
        shortener = URLShortener()
        invalid_urls = (
            "example.com/path",
            "ftp://example.com/file",
            "https:///path",
        )

        for url in invalid_urls:
            with self.subTest(url=url):
                with self.assertRaises(ValueError):
                    shortener.shorten(url)

    def test_expand_rejects_empty_or_invalid_code(self):
        shortener = URLShortener()

        for code in ("", "bad!"):
            with self.subTest(code=code):
                with self.assertRaises(ValueError):
                    shortener.expand(code)

    def test_expand_rejects_valid_but_unissued_code(self):
        with self.assertRaises(ValueError):
            URLShortener().expand("1")

    def test_shortener_supports_both_collision_strategies(self):
        for strategy in ("chaining", "linear"):
            with self.subTest(strategy=strategy):
                shortener = URLShortener(collision_strategy=strategy)
                url = "https://example.com/strategy"
                code = shortener.shorten(url)

                self.assertEqual(shortener.collision_strategy, strategy)
                self.assertEqual(shortener.expand(code), url)


if __name__ == "__main__":
    unittest.main()
