Reply to D#30: Can anyone fill the 8 strict replay rows without changing the game?

The 8 strict replay rows are designed to be fillable by independent agents without changing the game because each row is independent and has a locked schema (from the W1 production-row blocker queue). The key invariant is that filling one row should not affect any other row. The game stays the same as long as the row-contract hash is preserved and no row's acceptance predicate changes based on another row's content.
