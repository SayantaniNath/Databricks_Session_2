# NeetCode 150 — Arrays & Hashing
# Run this file to verify your solutions: python3 neetcode_practice.py

# ============================================================
# BIG O REFERENCE
# ============================================================
# Measures how runtime (or memory) grows as input size grows.
#
# O(1)        Constant      — dict lookup, array index        1000 items → 1 op
# O(log n)    Logarithmic   — binary search                   1000 items → ~10 ops
# O(n)        Linear        — one loop                        1000 items → 1,000 ops
# O(n log n)  Linearithmic  — sorting                         1000 items → ~10,000 ops
# O(n²)       Quadratic     — nested loops                    1000 items → 1,000,000 ops
# O(2ⁿ)       Exponential   — recursion/backtracking          grows astronomically
#
# Interview rule of thumb: O(n²) usually fails for array problems. Target O(n) or O(n log n).
# Two Sum brute force (two loops)     → O(n²)
# Two Sum hashmap (one loop + lookup) → O(n)   dict lookup is O(1), so n × O(1) = O(n)

from collections import defaultdict


# ============================================================
# 1. Two Sum
# ============================================================
# Problem: Given nums and target, return indices of the two numbers that add up to target.
#          Exactly one solution exists. Cannot use the same element twice.
# Example: nums = [2, 7, 11, 15], target = 9 → [0, 1]
# Time: O(n) | Space: O(n)

def two_sum(nums, target):
    seen = {}
    for i, num in enumerate(nums):
        complement = target - num
        if complement in seen:
            return [seen[complement], i]
        seen[num] = i


assert two_sum([2, 7, 11, 15], 9) == [0, 1]
assert two_sum([3, 2, 4], 6) == [1, 2]
assert two_sum([3, 3], 6) == [0, 1]
print("Two Sum: all tests passed")


# ============================================================
# 2. Group Anagrams
# ============================================================
# Problem: Given a list of strings, group the anagrams together.
#          Return the groups in any order.
# Example: ["eat","tea","tan","ate","nat","bat"]
#          → [["eat","tea","ate"], ["tan","nat"], ["bat"]]
# Key insight: anagrams share the same sorted characters → use sorted word as key
# Time: O(n * k log k) | Space: O(n * k)   k = max word length

def group_anagrams(strs):
    groups = defaultdict(list)      # dict that auto-creates [] for any new key
    for word in strs:               # loop through each word in the input list
        key = "".join(sorted(word)) # sort letters alphabetically → anagram fingerprint: "eat" → "aet"
        groups[key].append(word)    # add original word to its bucket (all anagrams share the same key)
    return list(groups.values())    # groups.values() = all buckets; list() wraps them


result = group_anagrams(["eat", "tea", "tan", "ate", "nat", "bat"])
assert sorted([sorted(g) for g in result]) == sorted([sorted(g) for g in [["eat","tea","ate"],["tan","nat"],["bat"]]])
assert group_anagrams([""]) == [[""]]
assert group_anagrams(["a"]) == [["a"]]
print("Group Anagrams: all tests passed")


# ============================================================
# 3. Top K Frequent Elements — 3 versions
# ============================================================
# Problem: Given nums and k, return the k most frequent elements. Any order.
# Example: nums = [1,1,1,2,2,3], k = 2 → [1, 2]
# Key insight: count with a dict, then pick the k keys with the biggest counts

# --- Version 1: count + sort by value (write this one from blank) ---
# Time: O(n log n) | Space: O(n)

def top_k_frequent(nums, k):
    counts = defaultdict(int)              # dict that auto-creates 0 for any new key
    for num in nums:                       # count occurrences of each number
        counts[num] += 1
    ordered = sorted(counts, key=lambda x: counts[x], reverse=True)  # keys sorted by count, biggest first
    return ordered[:k]                     # first k keys = k most frequent


# --- Version 2: Counter shortcut (mention in interviews, then offer V1/V3) ---
# Time: O(n log n) | Space: O(n)

from collections import Counter

def top_k_frequent_counter(nums, k):
    return [num for num, count in Counter(nums).most_common(k)]


# --- Version 3: bucket sort — the optimal answer (no sorting at all) ---
# Time: O(n) | Space: O(n)
# Trick: a number can appear at most len(nums) times, so make one bucket per
# possible count. buckets[3] holds every number that appeared exactly 3 times.
# Walk buckets from highest count down, collecting numbers until you have k.

def top_k_frequent_bucket(nums, k):
    counts = Counter(nums)
    buckets = [[] for _ in range(len(nums) + 1)]   # index = count, value = numbers with that count
    for num, count in counts.items():
        buckets[count].append(num)
    result = []
    for count in range(len(buckets) - 1, 0, -1):   # highest count → lowest
        for num in buckets[count]:
            result.append(num)
            if len(result) == k:
                return result


for fn in (top_k_frequent, top_k_frequent_counter, top_k_frequent_bucket):
    assert sorted(fn([1, 1, 1, 2, 2, 3], 2)) == [1, 2]
    assert fn([1], 1) == [1]
    assert sorted(fn([4, 4, 7, 7, 9], 2)) == [4, 7]
print("Top K Frequent: all tests passed (3 versions)")
