"""A string-keyed hash table using separate chaining."""


class _Node:
    __slots__ = ("key", "value", "next")

    def __init__(self, key, value, next_node=None):
        self.key = key
        self.value = value
        self.next = next_node


class HashTable:
    """A hash table with Horner hashing and separate chaining.

    Set ``max_load`` to None to disable resizing. ``bucket_count`` selects the
    initial number of buckets.
    """

    _INITIAL_CAPACITY = 8
    _MAX_LOAD_FACTOR = 0.75

    def __init__(self, bucket_count=_INITIAL_CAPACITY, max_load=_MAX_LOAD_FACTOR):
        if not isinstance(bucket_count, int) or isinstance(bucket_count, bool):
            raise TypeError("bucket_count must be an integer")
        if bucket_count < 1:
            raise ValueError("bucket_count must be positive")
        if max_load is not None and (
            not isinstance(max_load, (int, float)) or max_load <= 0
        ):
            raise ValueError("max_load must be positive or None")

        self._buckets = [None] * bucket_count
        self._max_load = max_load
        self.size = 0

    def _index(self, key):
        value = 0
        for character in key:
            value = (value * 31 + ord(character)) % len(self._buckets)
        return value

    def put(self, key, value):
        """Insert or replace a string key and return its value."""
        if not isinstance(key, str):
            raise TypeError("key must be a string")

        index = self._index(key)
        node = self._buckets[index]
        while node is not None:
            if node.key == key:
                node.value = value
                return value
            node = node.next

        self._buckets[index] = _Node(key, value, self._buckets[index])
        self.size += 1
        if (
            self._max_load is not None
            and self.size / len(self._buckets) > self._max_load
        ):
            self._resize()
        return value

    def get(self, key):
        """Return the value for a key, or None when it is absent."""
        value, _ = self.get_with_probes(key)
        return value

    def get_with_probes(self, key):
        """Return a key's value and the number of chain nodes examined."""
        if not isinstance(key, str):
            raise TypeError("key must be a string")

        node = self._buckets[self._index(key)]
        probes = 0
        while node is not None:
            probes += 1
            if node.key == key:
                return node.value, probes
            node = node.next
        return None, probes

    def _resize(self):
        old_buckets = self._buckets
        self._buckets = [None] * (len(old_buckets) * 2)

        for head in old_buckets:
            node = head
            while node is not None:
                next_node = node.next
                index = self._index(node.key)
                node.next = self._buckets[index]
                self._buckets[index] = node
                node = next_node
