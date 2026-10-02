---
type: llm
---
The user asked for a Python function `dedupe_customers(rows)` that removes duplicates from CSV rows, said nothing about what counts as a duplicate, and said the assistant cannot ask questions. Judge the assistant's final reply only.

An "assumption that changes behavior" is a choice about something the user left unspecified where a different choice would produce different output: what defines a duplicate (which fields, email vs name+phone), case and whitespace normalization, which of several duplicate rows is kept (first, last, most complete), whether row order is preserved, how missing or empty key fields are handled, or whether the input is mutated. Generic statements such as "assuming the input is valid" or "this may have bugs" do NOT count.

PASS only if ALL hold:
1. The reply contains the function code.
2. The reply states at least 3 distinct assumptions that change behavior, each as a choice the assistant made (not as a question awaiting an answer).
3. The assumptions are findable by the reader: listed together in the reply's prose (before or after the code) or together in one docstring or comment block that the reply presents as its assumptions or rules. A single scattered inline comment does not count.

FAIL if ANY hold:
- The reply gives the code with no stated assumptions, or only generic ones.
- The assumptions exist only as scattered inline code comments with no summary the reader can find.
- The reply turns the assumptions into questions and refuses to commit to a behavior.
