# Python Problem Log

| Date | Problem | Pattern | Solved from blank? | Notes |
|---|---|---|---|---|
| 2026-06-03 | Two Sum | Arrays & Hashing | With hints | Understood hashmap approach; needed help with enumerate, seen[complement] lookup, and indentation |
| 2026-06-11 | Group Anagrams | Arrays & Hashing | Mostly — got logic right, needed syntax fixes (colon, sorted vs sort) | Understood defaultdict(list), sorted key fingerprint, and append pattern |
| 2026-06-11 | Top K Frequent Elements | Arrays & Hashing | Partial — got count loop + "find max" intuition, needed help extending max→top-k and the sort-by-value syntax | Learned defaultdict(int) for counting, sorted(key=lambda), and Counter.most_common(k) |

---

## Two Sum

**Problem:** Given a list of integers `nums` and an integer `target`, return the indices of the two numbers that add up to `target`. Exactly one solution exists.

```
Example:
nums = [2, 7, 11, 15], target = 9
Output: [0, 1]  # nums[0] + nums[1] = 9
```

**Solution (hashmap — O(n) time, O(n) space):**

```python
def two_sum(nums, target):
    seen = {}
    for i, num in enumerate(nums):
        complement = target - num
        if complement in seen:
            return [seen[complement], i]
        seen[num] = i
```

**How it works:**
- Walk through the list once
- For each number, calculate its complement (`target - num`)
- Check if the complement was already seen — if yes, return both indices
- Otherwise store the current number and its index in `seen`
- `seen[num] = i` stores number as key, index as value — so `seen[complement]` retrieves the index

**Brute force (O(n²) — too slow):**

```python
def two_sum(nums, target):
    for i in range(len(nums)):
        for j in range(i + 1, len(nums)):
            if nums[i] + nums[j] == target:
                return [i, j]
```

---

## Q&A — 2026-06-03

**Q: What is O(n) and O(n²)?**
O(n) means you touch each element once — 1000 items = ~1000 operations. O(n²) means for each element you check every other element — 1000 items = ~1,000,000 operations. Dictionary lookup is O(1) (instant), which is why the hashmap solution is O(n) overall. Always state time + space complexity after writing a solution in interviews.

**Q: What does `enumerate(nums)` do?**
Gives you both the index and value in one line as you loop. `for i, num in enumerate([2,7,11,15])` produces pairs `(0,2), (1,7), (2,11), (3,15)`. Without it you'd need `for i in range(len(nums)): num = nums[i]` — two lines instead of one.

**Q: What does `seen[complement]` return?**
It returns the index where that complement was previously stored. `seen = {2: 0}` means the number `2` was found at index `0`. So `seen[2]` returns `0`. The key is the number, the value is its index.

**Q: What do `return [seen[complement], i]` and `seen[num] = i` do?**
- `seen[num] = i` — stores the current number and its index into the dict ("I saw number `num` at index `i`")
- `return [seen[complement], i]` — when the complement is found, retrieves the index where it was stored and pairs it with the current index

**Q: Why return a list `[...]` and not a tuple `(...)`?**
The problem asks for a list. `[0, 1]` is a list, `(0, 1)` is a tuple. Both work in practice but use square brackets to match the expected output type.

---

## Group Anagrams
*Date: 2026-06-11 | Pattern: Arrays & Hashing*

**Problem:** Given a list of strings, group the anagrams together. Return groups in any order.

```
Example:
Input:  ["eat","tea","tan","ate","nat","bat"]
Output: [["eat","tea","ate"], ["tan","nat"], ["bat"]]
```

**Solution (defaultdict + sorted key — O(n·k log k) time, O(n·k) space):**

```python
from collections import defaultdict

def group_anagrams(strs):
    groups = defaultdict(list)      # dict that auto-creates [] for any new key
    for word in strs:               # loop through each word
        key = "".join(sorted(word)) # sort letters → anagram fingerprint: "eat" → "aet"
        groups[key].append(word)    # add word to its bucket
    return list(groups.values())    # return all buckets as list of lists
```

**How it works:**
- All anagrams produce the same sorted string ("eat", "tea", "ate" all → "aet")
- Use that sorted string as the dict key → all anagrams land in the same bucket
- `defaultdict(list)` auto-creates `[]` on first access so `.append()` never crashes

---

## Q&A — 2026-06-11

**Q: Why does a plain dict crash but defaultdict works?**
`{}["newkey"].append("x")` → KeyError because "newkey" doesn't exist yet. `defaultdict(list)["newkey"].append("x")` works because it auto-creates `[]` at "newkey" the first time it's accessed.

**Q: What does `sorted(word)` return?**
A list of characters sorted alphabetically. `sorted("eat")` → `['a', 'e', 't']`. Not a string — that's why you need `"".join(...)` to turn it back.

**Q: What does `"".join(sorted(word))` do?**
`"".join(...)` joins a list of strings into one string using `""` (nothing) as separator. `['a','e','t']` → `"aet"`. If you used `",".join(...)` you'd get `"a,e,t"` — also a valid key but `""` is cleaner.

**Q: How is `groups.values()` different from `groups`?**
`groups` is the full dict e.g. `{"aet": ["eat","tea"], "abt": ["bat"]}`. `groups.values()` gives just the values (the buckets): `[["eat","tea"], ["bat"]]`. Wrap in `list()` to return as a plain list.

---

## Top K Frequent Elements
*Date: 2026-06-11 | Pattern: Arrays & Hashing*

**Problem:** Given a list of integers `nums` and an integer `k`, return the `k` most frequent elements. Any order.

```
Example:
nums = [1, 1, 1, 2, 2, 3], k = 2
Output: [1, 2]   # 1 appears 3 times, 2 appears twice
```

**Version 1 — count + sort by value (write this from blank — O(n log n) time, O(n) space):**

```python
from collections import defaultdict

def top_k_frequent(nums, k):
    counts = defaultdict(int)              # auto-creates 0 for any new key
    for num in nums:
        counts[num] += 1                   # count occurrences
    ordered = sorted(counts, key=lambda x: counts[x], reverse=True)
    return ordered[:k]                     # first k = most frequent
```

- `defaultdict(int)` starts every new key at 0, so `counts[num] += 1` never crashes
- `sorted(counts, ...)` iterates the dict's **keys**; `key=lambda x: counts[x]` says "rank each key by its count"
- `reverse=True` puts the biggest counts first; slice `[:k]` takes the top k

**Version 2 — Counter shortcut (mention in interviews, then offer V1/V3):**

```python
from collections import Counter

def top_k_frequent(nums, k):
    return [num for num, count in Counter(nums).most_common(k)]
```

**Version 3 — bucket sort, the optimal answer (O(n) time, O(n) space — no sorting):**

```python
from collections import Counter

def top_k_frequent(nums, k):
    counts = Counter(nums)
    buckets = [[] for _ in range(len(nums) + 1)]   # index = count
    for num, count in counts.items():
        buckets[count].append(num)                 # numbers grouped by how often they appear
    result = []
    for count in range(len(buckets) - 1, 0, -1):   # walk highest count → lowest
        for num in buckets[count]:
            result.append(num)
            if len(result) == k:
                return result
```

- A number can appear at most `len(nums)` times → one bucket per possible count, so no sort needed
- `buckets[3]` holds every number that appeared exactly 3 times
- Walking buckets from the highest index down gives most-frequent first; stop at k

---

## Q&A — 2026-06-12

**Q: In `for num, _ in Counter(nums).most_common(k)` — what is the `_`?**
`.most_common(k)` returns (number, count) pairs like `[(1, 3), (2, 2)]`. The loop unpacks each pair into two variables. `_` is the Python convention for "I'm required to unpack this but I don't use it" — here we keep the number and throw away the count. `for num, count in ...` works identically; `_` just signals intent. This makes V2 the easiest Top K version: `return [num for num, _ in Counter(nums).most_common(k)]`.

**Q: `defaultdict(int)` vs `defaultdict(list)` — when to use which?**
The argument is the factory — what gets auto-created for a missing key. `int()` returns `0`, `list()` returns `[]`. Use **int for counting** (`counts[num] += 1` needs a 0 to add to — Top K Frequent) and **list for grouping** (`groups[key].append(word)` needs a `[]` to append onto — Group Anagrams). Decision question for any new problem: am I *tallying* things (int) or *bucketing* things (list)?

**Q: What does `counts[num] += 1` store?**
The running count of each number — number as key, count-so-far as value. It's shorthand for `counts[num] = counts[num] + 1`: read the current count, add 1, store it back. For `[1, 1, 1, 2, 2, 3]` the dict grows `{1:1}` → `{1:2}` → `{1:3}` → `{1:3, 2:1}` → `{1:3, 2:2}` → `{1:3, 2:2, 3:1}`. `defaultdict(int)` makes the first occurrence work by auto-creating the key at 0 — a plain `{}` would raise KeyError. Same pattern as Two Sum's `seen[num] = i`: number is the key; the value is whatever you want back later (count here, index there).

**Q: What does `return sorted(counts, key=lambda x: counts[x], reverse=True)[:k]` do?**
Four pieces, with `counts = {1: 3, 2: 2, 3: 1}`, k=2:
1. `sorted(counts, ...)` — sorting a dict iterates its **keys** → input is `[1, 2, 3]`
2. `key=lambda x: counts[x]` — the measuring stick: rank each key by its count, not by the key itself (1 is ranked by 3, 2 by 2, 3 by 1)
3. `reverse=True` — biggest count first → `[1, 2, 3]`
4. `[:k]` — first k items → `[1, 2]`

One sentence: "take the dict's keys, order them by their counts biggest-first, return the first k." Gotcha: the lambda only controls the *ordering* — the output is still the keys, never the counts.

**Q: In Two Sum, why does `seen[num] = i` make the number the key instead of the value?**
In Python, `d[x] = y` always means *x is the key, y is the value* — whatever is inside the square brackets is the key. We deliberately put the **number** in the brackets because of how we need to look things up later: dict lookups go key → value, and the question we ask on every loop iteration is "have I already seen this *number*, and if so at what *index*?" That's `complement in seen` (search by number) followed by `seen[complement]` (retrieve its index). If we stored it the other way around (`seen[i] = num`, index as key), we couldn't check for the complement without scanning every value — back to O(n²). Rule of thumb: **the thing you search by is the key; the thing you want back is the value.**
