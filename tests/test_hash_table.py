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

    def test_linear_probing_wraps_from_last_slot_to_first(self):
        table = HashTable(
            bucket_count=4,
            max_load=None,
            collision_strategy="linear",
        )
        for key in ("c", "g", "k", "o"):
            table.put(key, key.upper())

        self.assertEqual(table.probe_path("o"), [3, 0, 1, 2])
        self.assertEqual(table.get_with_probes("o"), ("O", 4))
        self.assertEqual(table.get("c"), "C")
        self.assertEqual(table.get("g"), "G")

    def test_linear_probing_full_table_reports_all_probes_and_rejects_insert(self):
        table = HashTable(
            bucket_count=4,
            max_load=None,
            collision_strategy="linear",
        )
        for key in ("c", "g", "k", "o"):
            table.put(key, key)

        self.assertEqual(table.get_with_probes("w"), (None, 4))
        with self.assertRaises(OverflowError):
            table.put("w", "W")

    def test_linear_probing_resizes_and_rehashes_entries(self):
        table = HashTable(
            bucket_count=4,
            collision_strategy="linear",
        )
        for key in ("a", "b", "c", "d"):
            table.put(key, key.upper())

        self.assertEqual(len(table._buckets), 8)
        for key in ("a", "b", "c", "d"):
            self.assertEqual(table.get(key), key.upper())

    def test_rejects_unknown_collision_strategy(self):
        with self.assertRaises(ValueError):
            HashTable(collision_strategy="quadratic")


if __name__ == "__main__":
    unittest.main()
