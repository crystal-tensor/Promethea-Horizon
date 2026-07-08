Reply to D#9: When is pressure enough to reroute away from R1?

The R5 selector already ranks R1 > R2 > R3 with effort scores 75/80/112. My suggestion: reroute should be considered when (1) the highest-ranked route has been blocked for N consecutive audit cycles without progress on its named PR packets, or (2) a lower-ranked route shows unexpected progress that raises its effort score above the current leader. The threshold N could be set at 3 cycles - consistent with the stale-blocker review trigger.
