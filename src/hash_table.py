"""A string-keyed hash table using separate chaining."""


class _Node:
    __slots__ = ("key", "value", "next")

    def __init__(self, key, value, next_node=None):
        self.key = key
        self.value = value
        self.next = next_node


class HashTable:
    """A string-keyed hash table with separate chaining or linear probing.

    Set ``max_load`` to None to disable resizing. ``bucket_count`` selects the
    initial number of buckets. ``collision_strategy`` is ``"chaining"`` or
    ``"linear"``.
    """

    _INITIAL_CAPACITY = 8
    _MAX_LOAD_FACTOR = 0.75

    def __init__(
        self,
        bucket_count=_INITIAL_CAPACITY,
        max_load=_MAX_LOAD_FACTOR,
        collision_strategy="chaining",
    ):
        if not isinstance(bucket_count, int) or isinstance(bucket_count, bool):
            raise TypeError("bucket_count must be an integer")
        if bucket_count < 1:
            raise ValueError("bucket_count must be positive")
        if max_load is not None and (
            not isinstance(max_load, (int, float)) or max_load <= 0
        ):
            raise ValueError("max_load must be positive or None")
        if collision_strategy not in ("chaining", "linear"):
            raise ValueError("collision_strategy must be 'chaining' or 'linear'")

        self._buckets = [None] * bucket_count
        self._max_load = max_load
        self.collision_strategy = collision_strategy
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

        if self.collision_strategy == "linear":
            return self._put_linear(key, value)

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

    def _put_linear(self, key, value):
        capacity = len(self._buckets)
        index = self._index(key)
        for offset in range(capacity):
            slot = (index + offset) % capacity
            node = self._buckets[slot]
            if node is None:
                self._buckets[slot] = _Node(key, value)
                self.size += 1
                if (
                    self._max_load is not None
                    and self.size / capacity > self._max_load
                ):
                    self._resize()
                return value
            if node.key == key:
                node.value = value
                return value

        raise OverflowError("hash table is full")

    def get(self, key):
        """Return the value for a key, or None when it is absent."""
        value, _ = self.get_with_probes(key)
        return value

    def get_with_probes(self, key):
        """Return a key's value and the number of chain nodes examined."""
        if not isinstance(key, str):
            raise TypeError("key must be a string")

        if self.collision_strategy == "linear":
            capacity = len(self._buckets)
            index = self._index(key)
            for offset in range(capacity):
                slot = (index + offset) % capacity
                node = self._buckets[slot]
                if node is None:
                    return None, offset + 1
                if node.key == key:
                    return node.value, offset + 1
            return None, capacity

        node = self._buckets[self._index(key)]
        probes = 0
        while node is not None:
            probes += 1
            if node.key == key:
                return node.value, probes
            node = node.next
        return None, probes

    def probe_path(self, key):
        """Return slot indices inspected while locating an existing linear key."""
        if not isinstance(key, str):
            raise TypeError("key must be a string")
        if self.collision_strategy != "linear":
            raise ValueError("probe_path is only available for linear probing")

        capacity = len(self._buckets)
        index = self._index(key)
        path = []
        for offset in range(capacity):
            slot = (index + offset) % capacity
            path.append(slot)
            node = self._buckets[slot]
            if node is None or node.key == key:
                return path
        return path

    def _resize(self):
        old_buckets = self._buckets
        self._buckets = [None] * (len(old_buckets) * 2)

        if self.collision_strategy == "linear":
            for node in old_buckets:
                if node is not None:
                    self._put_linear_without_resize(node.key, node.value)
            return

        for head in old_buckets:
            node = head
            while node is not None:
                next_node = node.next
                index = self._index(node.key)
                node.next = self._buckets[index]
                self._buckets[index] = node
                node = next_node

    def _put_linear_without_resize(self, key, value):
        capacity = len(self._buckets)
        index = self._index(key)
        for offset in range(capacity):
            slot = (index + offset) % capacity
            if self._buckets[slot] is None:
                self._buckets[slot] = _Node(key, value)
                return
        raise OverflowError("hash table is full during resize")
