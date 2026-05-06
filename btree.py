from bisect import bisect_left, bisect_right
from collections import deque


class BTreeNode:
    def __init__(self, is_leaf=True):
        self.is_leaf = is_leaf
        self.keys = []
        self.rids = []
        self.children = []


class BTree:
    """B-tree where order means the minimum degree d.

    Each non-root node stores between d - 1 and 2d - 1 keys.
    """

    name = "B-tree"

    def __init__(self, order):
        if order < 3:
            raise ValueError("order must be at least 3")
        self.order = order
        self.max_keys = 2 * order - 1
        self.min_keys = order - 1
        self.root = BTreeNode(is_leaf=True)
        self.split_count = 0
        self.redistribution_count = 0
        self.merge_count = 0
        self.two_to_three_split_count = 0

    def search(self, key):
        return self._search(self.root, key)

    def _search(self, node, key):
        i = bisect_left(node.keys, key)
        if i < len(node.keys) and node.keys[i] == key:
            return node.rids[i]
        if node.is_leaf:
            return None
        return self._search(node.children[i], key)

    def insert(self, key, rid):
        result = self.search(key)
        if result is not None:
            self.delete(key)

        self._insert_recursive(self.root, key, rid)
        if len(self.root.keys) > self.max_keys:
            left, promoted_key, promoted_rid, right = self._split_node(self.root)
            self.root = BTreeNode(is_leaf=False)
            self.root.keys = [promoted_key]
            self.root.rids = [promoted_rid]
            self.root.children = [left, right]
            self.split_count += 1

    def _insert_recursive(self, node, key, rid):
        i = bisect_left(node.keys, key)
        if node.is_leaf:
            node.keys.insert(i, key)
            node.rids.insert(i, rid)
            return

        self._insert_recursive(node.children[i], key, rid)
        if len(node.children[i].keys) > self.max_keys:
            self._fix_child_overflow(node, i)

    def _fix_child_overflow(self, parent, child_index):
        child = parent.children[child_index]
        left, promoted_key, promoted_rid, right = self._split_node(child)
        parent.keys.insert(child_index, promoted_key)
        parent.rids.insert(child_index, promoted_rid)
        parent.children[child_index] = left
        parent.children.insert(child_index + 1, right)
        self.split_count += 1

    def _split_node(self, node):
        mid = len(node.keys) // 2
        left = BTreeNode(is_leaf=node.is_leaf)
        right = BTreeNode(is_leaf=node.is_leaf)

        left.keys = node.keys[:mid]
        left.rids = node.rids[:mid]
        right.keys = node.keys[mid + 1 :]
        right.rids = node.rids[mid + 1 :]

        if not node.is_leaf:
            left.children = node.children[: mid + 1]
            right.children = node.children[mid + 1 :]

        return left, node.keys[mid], node.rids[mid], right

    def delete(self, key):
        deleted = self._delete(self.root, key)
        if not self.root.is_leaf and len(self.root.keys) == 0:
            self.root = self.root.children[0]
        return deleted

    def _delete(self, node, key):
        idx = bisect_left(node.keys, key)

        if idx < len(node.keys) and node.keys[idx] == key:
            if node.is_leaf:
                node.keys.pop(idx)
                node.rids.pop(idx)
                return True
            return self._delete_from_internal(node, idx)

        if node.is_leaf:
            return False

        if len(node.children[idx].keys) == self.min_keys:
            idx = self._fill_child(node, idx)
        return self._delete(node.children[idx], key)

    def _delete_from_internal(self, node, idx):
        key = node.keys[idx]
        left_child = node.children[idx]
        right_child = node.children[idx + 1]

        if len(left_child.keys) > self.min_keys:
            pred_key, pred_rid = self._max_item(left_child)
            node.keys[idx] = pred_key
            node.rids[idx] = pred_rid
            return self._delete(left_child, pred_key)

        if len(right_child.keys) > self.min_keys:
            succ_key, succ_rid = self._min_item(right_child)
            node.keys[idx] = succ_key
            node.rids[idx] = succ_rid
            return self._delete(right_child, succ_key)

        merged = self._merge_children(node, idx)
        return self._delete(merged, key)

    def _max_item(self, node):
        while not node.is_leaf:
            node = node.children[-1]
        return node.keys[-1], node.rids[-1]

    def _min_item(self, node):
        while not node.is_leaf:
            node = node.children[0]
        return node.keys[0], node.rids[0]

    def _fill_child(self, parent, idx):
        if idx > 0 and len(parent.children[idx - 1].keys) > self.min_keys:
            self._borrow_from_left(parent, idx)
            return idx
        if idx + 1 < len(parent.children) and len(parent.children[idx + 1].keys) > self.min_keys:
            self._borrow_from_right(parent, idx)
            return idx
        if idx + 1 < len(parent.children):
            self._merge_children(parent, idx)
            return idx
        self._merge_children(parent, idx - 1)
        return idx - 1

    def _borrow_from_left(self, parent, idx):
        child = parent.children[idx]
        sibling = parent.children[idx - 1]

        child.keys.insert(0, parent.keys[idx - 1])
        child.rids.insert(0, parent.rids[idx - 1])
        if not child.is_leaf:
            child.children.insert(0, sibling.children.pop())

        parent.keys[idx - 1] = sibling.keys.pop()
        parent.rids[idx - 1] = sibling.rids.pop()
        self.redistribution_count += 1

    def _borrow_from_right(self, parent, idx):
        child = parent.children[idx]
        sibling = parent.children[idx + 1]

        child.keys.append(parent.keys[idx])
        child.rids.append(parent.rids[idx])
        if not child.is_leaf:
            child.children.append(sibling.children.pop(0))

        parent.keys[idx] = sibling.keys.pop(0)
        parent.rids[idx] = sibling.rids.pop(0)
        self.redistribution_count += 1

    def _merge_children(self, parent, idx):
        left = parent.children[idx]
        right = parent.children[idx + 1]

        left.keys.append(parent.keys.pop(idx))
        left.rids.append(parent.rids.pop(idx))
        left.keys.extend(right.keys)
        left.rids.extend(right.rids)
        if not left.is_leaf:
            left.children.extend(right.children)
        parent.children.pop(idx + 1)
        self.merge_count += 1
        return left

    def range_query(self, low, high):
        result = []
        self._range_query(self.root, low, high, result)
        return result

    def _range_query(self, node, low, high, result):
        if node.is_leaf:
            for key, rid in zip(node.keys, node.rids):
                if low <= key <= high:
                    result.append(rid)
            return

        for i, key in enumerate(node.keys):
            if low <= key:
                self._range_query(node.children[i], low, high, result)
            if low <= key <= high:
                result.append(node.rids[i])
            if key > high:
                return
        self._range_query(node.children[-1], low, high, result)

    def height(self):
        height = 0
        node = self.root
        while node and not node.is_leaf:
            height += 1
            node = node.children[0]
        return height + 1

    def count_nodes(self):
        return sum(1 for _ in self._iter_nodes())

    def utilization(self):
        nodes = list(self._iter_nodes())
        if not nodes:
            return 0.0
        return sum(len(node.keys) for node in nodes) / (len(nodes) * self.max_keys)

    def _iter_nodes(self):
        q = deque([self.root])
        while q:
            node = q.popleft()
            yield node
            q.extend(node.children)

    def validate(self):
        leaf_depths = set()

        def visit(node, depth, low, high, is_root=False):
            if node.keys != sorted(node.keys):
                return False
            if len(node.keys) > self.max_keys:
                return False
            if not is_root and len(node.keys) < self.min_keys:
                return False
            for key in node.keys:
                if (low is not None and key <= low) or (high is not None and key >= high):
                    return False

            if node.is_leaf:
                leaf_depths.add(depth)
                return True

            if len(node.children) != len(node.keys) + 1:
                return False
            bounds = [low] + node.keys + [high]
            for i, child in enumerate(node.children):
                if not visit(child, depth + 1, bounds[i], bounds[i + 1]):
                    return False
            return True

        return visit(self.root, 0, None, None, True) and len(leaf_depths) <= 1


class BStarTree(BTree):
    name = "B*-tree"

    def _fix_child_overflow(self, parent, child_index):
        if child_index + 1 < len(parent.children) and len(parent.children[child_index + 1].keys) < self.max_keys:
            self._redistribute_with_right(parent, child_index)
            return
        if child_index > 0 and len(parent.children[child_index - 1].keys) < self.max_keys:
            self._redistribute_with_left(parent, child_index)
            return
        if child_index + 1 < len(parent.children):
            self._split_two_to_three_right(parent, child_index)
            return
        if child_index > 0:
            self._split_two_to_three_left(parent, child_index)
            return
        super()._fix_child_overflow(parent, child_index)

    def _redistribute_with_right(self, parent, idx):
        left = parent.children[idx]
        right = parent.children[idx + 1]
        keys = left.keys + [parent.keys[idx]] + right.keys
        rids = left.rids + [parent.rids[idx]] + right.rids
        left_count = len(keys) // 2

        left.keys = keys[:left_count]
        left.rids = rids[:left_count]
        parent.keys[idx] = keys[left_count]
        parent.rids[idx] = rids[left_count]
        right.keys = keys[left_count + 1 :]
        right.rids = rids[left_count + 1 :]

        if not left.is_leaf:
            children = left.children + right.children
            left.children = children[: left_count + 1]
            right.children = children[left_count + 1 :]
        self.redistribution_count += 1

    def _redistribute_with_left(self, parent, idx):
        left = parent.children[idx - 1]
        right = parent.children[idx]
        keys = left.keys + [parent.keys[idx - 1]] + right.keys
        rids = left.rids + [parent.rids[idx - 1]] + right.rids
        left_count = len(keys) // 2

        left.keys = keys[:left_count]
        left.rids = rids[:left_count]
        parent.keys[idx - 1] = keys[left_count]
        parent.rids[idx - 1] = rids[left_count]
        right.keys = keys[left_count + 1 :]
        right.rids = rids[left_count + 1 :]

        if not left.is_leaf:
            children = left.children + right.children
            left.children = children[: left_count + 1]
            right.children = children[left_count + 1 :]
        self.redistribution_count += 1

    def _split_two_to_three_right(self, parent, idx):
        first = parent.children[idx]
        second = parent.children[idx + 1]
        keys = first.keys + [parent.keys[idx]] + second.keys
        rids = first.rids + [parent.rids[idx]] + second.rids
        children = first.children + second.children
        self._replace_two_children_with_three(parent, idx, keys, rids, children, first.is_leaf)

    def _split_two_to_three_left(self, parent, idx):
        first = parent.children[idx - 1]
        second = parent.children[idx]
        keys = first.keys + [parent.keys[idx - 1]] + second.keys
        rids = first.rids + [parent.rids[idx - 1]] + second.rids
        children = first.children + second.children
        self._replace_two_children_with_three(parent, idx - 1, keys, rids, children, first.is_leaf)

    def _replace_two_children_with_three(self, parent, idx, keys, rids, children, is_leaf):
        remaining = len(keys) - 2
        base = remaining // 3
        extra = remaining % 3
        counts = [base + (1 if i < extra else 0) for i in range(3)]

        n1 = BTreeNode(is_leaf=is_leaf)
        n2 = BTreeNode(is_leaf=is_leaf)
        n3 = BTreeNode(is_leaf=is_leaf)

        p1 = counts[0]
        p2 = p1 + 1 + counts[1]
        n1.keys = keys[:p1]
        n1.rids = rids[:p1]
        sep1_key, sep1_rid = keys[p1], rids[p1]
        n2.keys = keys[p1 + 1 : p2]
        n2.rids = rids[p1 + 1 : p2]
        sep2_key, sep2_rid = keys[p2], rids[p2]
        n3.keys = keys[p2 + 1 :]
        n3.rids = rids[p2 + 1 :]

        if not is_leaf:
            n1.children = children[: counts[0] + 1]
            start = counts[0] + 1
            n2.children = children[start : start + counts[1] + 1]
            start += counts[1] + 1
            n3.children = children[start:]

        parent.keys[idx] = sep1_key
        parent.rids[idx] = sep1_rid
        parent.keys.insert(idx + 1, sep2_key)
        parent.rids.insert(idx + 1, sep2_rid)
        parent.children[idx] = n1
        parent.children[idx + 1] = n2
        parent.children.insert(idx + 2, n3)
        self.split_count += 1
        self.two_to_three_split_count += 1


class BPlusNode:
    def __init__(self, is_leaf=True):
        self.is_leaf = is_leaf
        self.keys = []
        self.children = []
        self.rids = []
        self.next = None
        self.prev = None


class BPlusTree:
    name = "B+tree"

    def __init__(self, order):
        if order < 3:
            raise ValueError("order must be at least 3")
        self.order = order
        self.max_keys = 2 * order - 1
        self.min_keys = order - 1
        self.root = BPlusNode(is_leaf=True)
        self.split_count = 0
        self.redistribution_count = 0
        self.merge_count = 0
        self.two_to_three_split_count = 0

    def search(self, key):
        leaf = self._find_leaf(key)
        idx = bisect_left(leaf.keys, key)
        if idx < len(leaf.keys) and leaf.keys[idx] == key:
            return leaf.rids[idx]
        return None

    def _find_leaf(self, key):
        node = self.root
        while not node.is_leaf:
            node = node.children[bisect_right(node.keys, key)]
        return node

    def insert(self, key, rid):
        if self.search(key) is not None:
            self.delete(key)
        promoted = self._insert_recursive(self.root, key, rid)
        if promoted is not None:
            key_up, right = promoted
            new_root = BPlusNode(is_leaf=False)
            new_root.keys = [key_up]
            new_root.children = [self.root, right]
            self.root = new_root

    def _insert_recursive(self, node, key, rid):
        if node.is_leaf:
            idx = bisect_left(node.keys, key)
            node.keys.insert(idx, key)
            node.rids.insert(idx, rid)
            if len(node.keys) <= self.max_keys:
                return None
            return self._split_leaf(node)

        idx = bisect_right(node.keys, key)
        promoted = self._insert_recursive(node.children[idx], key, rid)
        if promoted is None:
            return None
        key_up, right = promoted
        node.keys.insert(idx, key_up)
        node.children.insert(idx + 1, right)
        if len(node.keys) <= self.max_keys:
            return None
        return self._split_internal(node)

    def _split_leaf(self, leaf):
        split = (len(leaf.keys) + 1) // 2
        right = BPlusNode(is_leaf=True)
        right.keys = leaf.keys[split:]
        right.rids = leaf.rids[split:]
        leaf.keys = leaf.keys[:split]
        leaf.rids = leaf.rids[:split]

        right.next = leaf.next
        if right.next is not None:
            right.next.prev = right
        leaf.next = right
        right.prev = leaf
        self.split_count += 1
        return right.keys[0], right

    def _split_internal(self, node):
        mid = len(node.keys) // 2
        right = BPlusNode(is_leaf=False)
        promoted_key = node.keys[mid]
        right.keys = node.keys[mid + 1 :]
        right.children = node.children[mid + 1 :]
        node.keys = node.keys[:mid]
        node.children = node.children[: mid + 1]
        self.split_count += 1
        return promoted_key, right

    def delete(self, key):
        path = []
        node = self.root
        while not node.is_leaf:
            idx = bisect_right(node.keys, key)
            path.append((node, idx))
            node = node.children[idx]

        idx = bisect_left(node.keys, key)
        if idx == len(node.keys) or node.keys[idx] != key:
            return False
        node.keys.pop(idx)
        node.rids.pop(idx)

        if path:
            parent, child_idx = path[-1]
            if child_idx > 0 and node.keys:
                parent.keys[child_idx - 1] = node.keys[0]

        self._rebalance_after_delete(node, path)
        if not self.root.is_leaf and len(self.root.keys) == 0:
            self.root = self.root.children[0]
        return True

    def _rebalance_after_delete(self, node, path):
        while path and len(node.keys) < self.min_keys:
            parent, idx = path.pop()
            left = parent.children[idx - 1] if idx > 0 else None
            right = parent.children[idx + 1] if idx + 1 < len(parent.children) else None

            if left is not None and len(left.keys) > self.min_keys:
                self._borrow_leaf_or_internal_from_left(parent, idx, left, node)
                return
            if right is not None and len(right.keys) > self.min_keys:
                self._borrow_leaf_or_internal_from_right(parent, idx, node, right)
                return

            if left is not None:
                self._merge_bplus_nodes(parent, idx - 1, left, node)
                node = parent
            elif right is not None:
                self._merge_bplus_nodes(parent, idx, node, right)
                node = parent
            else:
                return

    def _borrow_leaf_or_internal_from_left(self, parent, idx, left, node):
        if node.is_leaf:
            node.keys.insert(0, left.keys.pop())
            node.rids.insert(0, left.rids.pop())
            parent.keys[idx - 1] = node.keys[0]
        else:
            node.children.insert(0, left.children.pop())
            node.keys.insert(0, parent.keys[idx - 1])
            parent.keys[idx - 1] = left.keys.pop()
        self.redistribution_count += 1

    def _borrow_leaf_or_internal_from_right(self, parent, idx, node, right):
        if node.is_leaf:
            node.keys.append(right.keys.pop(0))
            node.rids.append(right.rids.pop(0))
            parent.keys[idx] = right.keys[0] if right.keys else node.keys[-1]
        else:
            node.children.append(right.children.pop(0))
            node.keys.append(parent.keys[idx])
            parent.keys[idx] = right.keys.pop(0)
        self.redistribution_count += 1

    def _merge_bplus_nodes(self, parent, idx, left, right):
        if left.is_leaf:
            left.keys.extend(right.keys)
            left.rids.extend(right.rids)
            left.next = right.next
            if left.next is not None:
                left.next.prev = left
        else:
            left.keys.append(parent.keys[idx])
            left.keys.extend(right.keys)
            left.children.extend(right.children)
        parent.keys.pop(idx)
        parent.children.pop(idx + 1)
        self.merge_count += 1

    def range_query(self, low, high):
        result = []
        node = self._find_leaf(low)
        while node is not None:
            for key, rid in zip(node.keys, node.rids):
                if key > high:
                    return result
                if key >= low:
                    result.append(rid)
            node = node.next
        return result

    def height(self):
        height = 1
        node = self.root
        while not node.is_leaf:
            height += 1
            node = node.children[0]
        return height

    def count_nodes(self):
        return sum(1 for _ in self._iter_nodes())

    def utilization(self):
        nodes = list(self._iter_nodes())
        if not nodes:
            return 0.0
        return sum(len(node.keys) for node in nodes) / (len(nodes) * self.max_keys)

    def _iter_nodes(self):
        q = deque([self.root])
        while q:
            node = q.popleft()
            yield node
            if not node.is_leaf:
                q.extend(node.children)

    def validate(self):
        leaf_depths = set()
        leaves = []

        def visit(node, depth, low, high, is_root=False):
            if node.keys != sorted(node.keys):
                return False
            if len(node.keys) > self.max_keys:
                return False
            if not is_root and len(node.keys) < self.min_keys:
                return False
            if node.is_leaf:
                for key in node.keys:
                    if (low is not None and key < low) or (high is not None and key >= high):
                        return False
                leaf_depths.add(depth)
                leaves.append(node)
                return True

            if len(node.children) != len(node.keys) + 1:
                return False
            bounds = [low] + node.keys + [high]
            for i, child in enumerate(node.children):
                if not visit(child, depth + 1, bounds[i], bounds[i + 1]):
                    return False
            return True

        if not visit(self.root, 0, None, None, True) or len(leaf_depths) > 1:
            return False
        for left, right in zip(leaves, leaves[1:]):
            if left.next is not right or right.prev is not left:
                return False
        return True
