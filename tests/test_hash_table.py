import unittest

from src.hash_table import HashTable


class HashTableTests(unittest.TestCase):
    def test_colliding_keys_can_both_be_stored_and_retrieved(self):
        table = HashTable()
        # "a" and "i" map to the same bucket with the specified initial capacity.
        table.put("a", "first")
        table.put("i", "second")

        self.assertEqual(table.get("a"), "first")
        self.assertEqual(table.get("i"), "second")

    def test_put_updates_existing_key_without_adding_an_entry(self):
        table = HashTable()
        table.put("key", "before")
        table.put("key", "after")

        self.assertEqual(table.get("key"), "after")
        self.assertEqual(table.size, 1)

    def test_get_returns_none_for_missing_key(self):
        self.assertIsNone(HashTable().get("missing"))

    def test_resizes_above_load_factor_and_preserves_entries(self):
        table = HashTable()
        self.assertEqual(len(table._buckets), 8)

        for number in range(7):
            table.put(f"key-{number}", number)

        self.assertEqual(len(table._buckets), 16)
        for number in range(7):
            self.assertEqual(table.get(f"key-{number}"), number)


if __name__ == "__main__":
    unittest.main()
