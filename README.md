# CSE 537 Project 3 - Bayes Nets

Private TA reference solution with completed Q1-Q4, a playable Ghostbusters
keyboard game, a PDF report, and reproducible verification.

## Contents

- `bayesnets/`: complete runnable project and preserved starter support files.
- `Project3_TA_Report.pdf`: per-question approaches, results, benchmarks, and analysis.
- `Project3_TA_Solution.zip`: complete project archive without caches or temporary files.
- `Project3_Verification.txt`: verification record, including a fresh archive extraction.

## Play Pac-Man

Requires Python 3 with Tk support. Verified on Python 3.12.5 / Tk 8.6.

On macOS, double-click `bayesnets/Launch_Pacman.command`, or run:

```sh
python3 bayesnets/play_gui.py
python3 bayesnets/play_gui.py --layout smallHunt --fixed-seed
```

Use arrow keys or WASD to move; Q stops. Hunt invisible ghosts using the colored
cells and noisy distance readings. Close the window to exit. For a teaching demo,
add `--show-ghosts`. Available layouts: oneHunt, smallHunt, openHunt, bigHunt.

## Verify the solution

```sh
cd bayesnets
python3 test_q1to4.py
python3 -m unittest discover -s validation -v
PYTHONHASHSEED=1234 python3 validation/analyze_order.py
PYTHONHASHSEED=1234 python3 validation/benchmark.py
```

All four supplied examples and 16 additional test methods pass. The checks include
1,155 inference queries across 100 seeded random DAGs against an independent
exhaustive oracle, exact operation traces, domain boundaries, immutability, and
impossible evidence. Eight complete game-engine tests cover all four layouts.
Graphical launch, arrow keys, WASD, sensor readings, and shading were also
verified manually. No external private autograder was available.

## Assignment scope

Q1 constructs the Bayes-net graph and domains; Q2 joins factors; Q3 marginalizes
a variable; Q4 performs variable elimination. Only the four designated sections
in `inference.py` and `factorOperations.py` were changed. All original support,
layout, and supplied example-test files are preserved.

The keyboard demo uses the supplied `demoInference.py` independently of Q1-Q4.
Its behavior and test-only game drivers are separate from inference correctness.

## Attribution

Adapted from the supplied CSE 537 Project 03 materials and the
[UC Berkeley Pacman AI projects](http://ai.berkeley.edu), developed by John DeNero,
Dan Klein, Pieter Abbeel, and contributors. Original licensing and attribution
notices are retained. Keep this solution private.
