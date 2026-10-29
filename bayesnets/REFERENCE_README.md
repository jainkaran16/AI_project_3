# CSE 537 Project 03 - private TA reference

Completed Q1-Q4 in `inference.py` and `factorOperations.py`. Only the four
marked implementation sections were changed. All 18 supplied support, layout,
and example-test files remain byte-for-byte identical to the starter ZIP.
Original Berkeley attribution and license notices are retained.

Use Python 3 (verified with 3.12.5). From the `bayesnets` directory:

```sh
python3 test_q1to4.py
python3 -m unittest discover -s validation -v
PYTHONHASHSEED=1234 python3 validation/analyze_order.py
PYTHONHASHSEED=1234 python3 validation/benchmark.py
```

The four supplied examples pass. The 16 additional test methods include 1,155
inference queries across 100 seeded random DAGs and all hidden-variable
permutations, checked against direct exhaustive CPT multiplication and summation.
Runtime uses the median of seven untraced queries, and Python allocation uses
five separate tracemalloc queries, with one warmup per method and problem.
Results for 5-, 7-, and 9-variable binary stars are saved in
`validation/benchmark_results.json`. Network construction and oracle checks are
excluded; every measured result is validated after measurement. The fixed hash
seed also stabilizes set iteration in the supplied enumeration implementation.

They also check graph/domain boundaries, arbitrary and unnormalized factors,
input immutability, exception behavior, disconnected graphs, exact operation
traces, the discard branch, singleton domains, and impossible evidence.
The tests do not require external packages or graphical access.

`validation/order_analysis.json` records a reproducible factor-size experiment:
seven binary variables in a star, querying one leaf. A leaf-first elimination
order has a largest created factor of 4 rows, versus 128 rows for center-first
elimination or enumeration. These are table-entry counts, not runtime or peak
process-memory measurements. All methods return the same posterior.

Contracts follow the supplied assignment: factors in a join share domains and
have disjoint unconditioned scopes; the input factor collection is nonempty;
Bayes-net CPTs are normalized; query and evidence are disjoint; the query is
nonempty; and an explicit elimination order lists all hidden variables exactly
once. `None` selects the supplied sorted default order. Zero-probability evidence
returns `None` through the supplied normalization helper. Singleton query domains
are conditioned by that same helper. Supplied type checks are preserved; they
are not a full validator for every malformed input.

## Play the game

Double-click `Launch_Pacman.command` on macOS, or run:

```sh
python3 play_gui.py
python3 play_gui.py --layout smallHunt --fixed-seed
python3 play_gui.py --layout bigHunt --show-ghosts
```

The launcher works from any working directory. Arrow keys or WASD move Pac-Man;
Q stops; closing the window exits. Ghosts are hidden by default; colored cells
and noisy distance readings provide clues. `--show-ghosts` reveals them for a
teaching demonstration. Python must include Tk (verified locally with Tk 8.6).
The original `python3 busters.py` entrypoint is also unchanged and works.

The actual graphical game and launcher were opened and arrow-key and WASD
movement, sensor readings, and shading were verified visually. Eight complete
engine games pass across all four layouts: stationary ghosts through the real
keyboard/shading pipeline and random ghosts with a test-only visible-position
driver. Both drivers are integration-test fixtures, not inference solutions or
players used by the launcher. The game uses `demoInference.py` independently of
Q1-Q4; GUI success is not used as evidence of factor/inference correctness. No external private autograder was
available. The PDF report provides the approaches, results, and critical analysis.

Keep this TA reference package private, consistent with the starter license.
