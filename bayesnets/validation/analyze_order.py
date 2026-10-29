"""Reproducible factor-table size comparison on a seven-node binary star."""
import json
import os
from pathlib import Path
import random
from unittest.mock import patch
from test_reference_solution import bn, inference, make_net, oracle


def main():
    domains = {v: [0, 1] for v in ['Center'] + [f'Leaf{i}' for i in range(6)]}
    net = make_net(domains, [('Center', f'Leaf{i}') for i in range(6)], random.Random(537))
    modes = [
        ('VE: center first', ['Center'] + [f'Leaf{i}' for i in range(1, 6)]),
        ('VE: leaves first', [f'Leaf{i}' for i in range(1, 6)] + ['Center']),
        ('Enumeration', None),
    ]
    constructor = bn.Factor.__init__
    results = []
    expected, total = oracle(net, ['Leaf0'], {})
    for label, order in modes:
        sizes = []
        def counted_init(self, *args, **kwargs):
            constructor(self, *args, **kwargs)
            sizes.append(len(self.getAllPossibleAssignmentDicts()))
        with patch.object(bn.Factor, '__init__', counted_init):
            if label == 'Enumeration':
                result = inference.inferenceByEnumeration(net, ['Leaf0'], {})
            else:
                result = inference.inferenceByVariableElimination(net, ['Leaf0'], {}, order)
        posterior = [result.getProbability({'Leaf0': v}) for v in domains['Leaf0']]
        for value, actual in zip(domains['Leaf0'], posterior):
            assert abs(actual - expected[(value,)] / total) < 1e-12
        results.append({'method': label, 'largest_created_factor_rows': max(sizes),
                        'total_created_factor_rows': sum(sizes), 'posterior_Leaf0': posterior})
    print(json.dumps({'network': 'Center -> Leaf0,...,Leaf5; binary variables; query Leaf0; no evidence',
                      'seed': 537, 'python_hash_seed': os.environ.get('PYTHONHASHSEED', 'unset'), 'results': results}, indent=2))


if __name__ == '__main__':
    main()
