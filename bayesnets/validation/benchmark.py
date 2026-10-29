"""Reproduce inference timings and memory separately, following Project 2's method.

Run from bayesnets: python3 validation/benchmark.py
Network construction, validation and table-size instrumentation are excluded.
"""
import gc
import json
import os
from pathlib import Path
import platform
import random
import statistics
import time
import tracemalloc
from test_reference_solution import inference, make_net, oracle


def measure(net, query, evidence, order, method):
    def infer():
        if method == 'Enumeration':
            return inference.inferenceByEnumeration(net, query, evidence)
        return inference.inferenceByVariableElimination(net, query, evidence, order)
    expected, total = oracle(net, query, evidence)
    def validate(result):
        for row in result.getAllPossibleAssignmentDicts():
            assert abs(result.getProbability(row) - expected[tuple(row[v] for v in query)] / total) < 1e-12
    timings, peaks = [], []
    validate(infer())  # Warmup and correctness check before measurement.
    for _ in range(7):
        gc.collect()
        start = time.perf_counter()
        result = infer()
        timings.append((time.perf_counter() - start) * 1000)
        validate(result)
    for _ in range(5):
        gc.collect()
        tracemalloc.start()
        result = infer()
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        peaks.append(peak / 1024)
        validate(result)
    return {'method': method, 'runtime_ms': statistics.median(timings),
            'peak_python_kib': statistics.median(peaks)}


def main():
    rows = []
    for leaves in [4, 6, 8]:
        domains = {v: [0, 1] for v in ['Center'] + [f'Leaf{i}' for i in range(leaves)]}
        net = make_net(domains, [('Center', f'Leaf{i}') for i in range(leaves)], random.Random(537))
        hidden_leaves = [f'Leaf{i}' for i in range(1, leaves)]
        for method, order in [('VE: center first', ['Center'] + hidden_leaves),
                              ('VE: leaves first', hidden_leaves + ['Center']),
                              ('Enumeration', None)]:
            result = measure(net, ['Leaf0'], {}, order, method)
            result['binary_variables'] = leaves + 1
            rows.append(result)
    data = {'methodology': {'python_version': platform.python_version(), 'seed': 537, 'python_hash_seed': os.environ.get('PYTHONHASHSEED', 'unset'),
            'timing_repeats': 7, 'memory_repeats': 5, 'warmup_queries_per_case': 1,
            'runtime_statistic': 'median untraced wall-clock time',
            'memory_statistic': 'median separate tracemalloc peak Python allocation',
            'scope': 'inference including evidence specialization and normalization; excludes model construction, oracle checks, and table instrumentation',
            'network': 'binary star: Center -> every Leaf; query Leaf0; no evidence'},
            'results': rows}
    output = Path(__file__).with_name('benchmark_results.json')
    output.write_text(json.dumps(data, indent=2)+'\n')
    print(json.dumps(data, indent=2))


if __name__ == '__main__':
    main()
