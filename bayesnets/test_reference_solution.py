"""Private TA verification; run from bayesnets with unittest discovery.

The exhaustive inference oracle multiplies CPT entries directly and sums complete
assignments. It never calls joinFactors, eliminate, or either inference routine.
No third-party packages are needed. Berkeley starter attribution: ai.berkeley.edu.
"""
import contextlib
import io
import itertools
import math
from pathlib import Path
import random
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bayesNet as bn
import factorOperations as fo
import inference


def assignments(domains, variables):
    variables = sorted(variables)
    for values in itertools.product(*(domains[v] for v in variables)):
        yield dict(zip(variables, values))


def make_net(domains, edges, rng, deterministic=False):
    net = bn.constructEmptyBayesNet(list(domains), edges, domains)
    for variable in sorted(domains):
        parents = net.inEdges()[variable]
        cpt = bn.Factor([variable], parents, domains)
        for parent_values in assignments(domains, parents):
            weights = [rng.randint(1, 12) for _ in domains[variable]]
            if deterministic:
                weights = [1] + [0] * (len(weights) - 1)
            total = sum(weights)
            for value, weight in zip(domains[variable], weights):
                row = dict(parent_values)
                row[variable] = value
                cpt.setProbability(row, weight / total)
        net.setCPT(variable, cpt)
    return net


def oracle(net, query, evidence):
    """Return unnormalized query masses and evidence probability independently."""
    domains = net.variableDomainsDict()
    masses = {tuple(a[v] for v in query): 0.0 for a in assignments(domains, query)}
    cpts = [net.getCPT(v) for v in sorted(domains)]
    for row in assignments(domains, domains):
        if any(row[v] != value for v, value in evidence.items()):
            continue
        joint = math.prod(cpt.getProbability(row) for cpt in cpts)
        masses[tuple(row[v] for v in query)] += joint
    return masses, sum(masses.values())


class ReferenceTests(unittest.TestCase):
    def assert_close(self, actual, expected):
        self.assertTrue(math.isclose(actual, expected, rel_tol=1e-10, abs_tol=1e-12),
                        f'{actual} != {expected}')

    def check_inference(self, net, query, evidence, order):
        before = [(v, str(net.getCPT(v))) for v in sorted(net.variablesSet())]
        trace = []
        result = inference.inferenceByVariableEliminationWithCallTracking(trace)(
            net, query, evidence, order)
        masses, total = oracle(net, query, evidence)
        self.assertEqual(before, [(v, str(net.getCPT(v))) for v in sorted(net.variablesSet())])
        if total == 0:
            self.assertIsNone(result)
            return
        self.assertIsNotNone(result)
        domains = net.getReducedVariableDomains(evidence)
        singleton_query = {v for v in query if len(domains[v]) == 1}
        self.assertEqual(result.unconditionedVariables(), set(query) - singleton_query)
        self.assertEqual(result.conditionedVariables(), set(evidence) | singleton_query)
        self.assertEqual(result.variableDomainsDict(), domains)
        for row in result.getAllPossibleAssignmentDicts():
            self.assert_close(result.getProbability(row), masses[tuple(row[v] for v in query)] / total)
        self.assert_close(sum(result.getProbability(r) for r in result.getAllPossibleAssignmentDicts()), 1)
        hidden_order = order if order is not None else sorted(set(domains) - set(query) - set(evidence))
        self.assertEqual([v for op, v in trace if op == 'join'], list(hidden_order))
        # Each join is followed by its own elimination or by the next join
        # when the lone-unconditioned-variable factor must be discarded.
        i = 0
        for v in hidden_order:
            self.assertEqual(trace[i], ('join', v))
            i += 1
            if i < len(trace) and trace[i][0] == 'eliminate':
                self.assertEqual(trace[i], ('eliminate', v))
                i += 1
        self.assertEqual(i, len(trace))

    def test_q1_dimensions_and_walls(self):
        class Walls:
            def __init__(self, w, h): self.width, self.height = w, h
        class State:
            def __init__(self, w, h): self.walls = Walls(w, h)
            def getWalls(self): return self.walls
        for w, h in [(1, 1), (1, 8), (9, 1), (2, 7), (8, 5)]:
            with self.subTest(width=w, height=h):
                net = inference.constructBayesNet(State(w, h))
                self.assertEqual(net.variablesSet(), {'Pacman', 'Ghost0', 'Ghost1', 'Observation0', 'Observation1'})
                self.assertEqual({(a, b) for b, parents in net.inEdges().items() for a in parents},
                                 {('Pacman', 'Observation0'), ('Pacman', 'Observation1'),
                                  ('Ghost0', 'Observation0'), ('Ghost1', 'Observation1')})
                domains = net.variableDomainsDict()
                for v in ['Pacman', 'Ghost0', 'Ghost1']:
                    self.assertEqual(set(domains[v]), set(itertools.product(range(w), range(h))))
                    self.assertEqual(len(domains[v]), w*h)
                for v in ['Observation0', 'Observation1']:
                    self.assertEqual(domains[v], list(range(w+h+6)))

    def test_q2_general_unnormalized_join(self):
        domains = {v: [0, 1, 2] for v in ['V', 'W', 'X', 'Y', 'Z', 'Unused']}
        first = bn.Factor(['V', 'W'], ['X', 'Y', 'Z'], domains)
        second = bn.Factor(['X', 'Y'], ['Z'], domains)
        for f in [first, second]:
            for i, row in enumerate(f.getAllPossibleAssignmentDicts()):
                f.setProbability(row, (i % 7) * 0.8)
        snapshots = [str(f) for f in [first, second]]
        result = fo.joinFactors(iter([first, second]))
        self.assertEqual(result.unconditionedVariables(), {'V', 'W', 'X', 'Y'})
        self.assertEqual(result.conditionedVariables(), {'Z'})
        self.assertEqual(result.variableDomainsDict(), domains)
        for row in assignments(domains, {'V', 'W', 'X', 'Y', 'Z'}):
            self.assert_close(result.getProbability(row), first.getProbability(row)*second.getProbability(row))
        self.assertEqual(snapshots, [str(f) for f in [first, second]])

    def test_q2_single_factor_is_new(self):
        domains = {'A': ['x', 'y'], 'B': [False, True], 'Unused': [8]}
        source = bn.Factor(['A'], ['B'], domains)
        for i, row in enumerate(source.getAllPossibleAssignmentDicts()): source.setProbability(row, i / 3)
        result = fo.joinFactors([source])
        self.assertIsNot(source, result)
        self.assertEqual(str(source), str(result))
        result.setProbability({'A': 'x', 'B': False}, 4)
        self.assert_close(source.getProbability({'A': 'x', 'B': False}), 0)

    def test_q2_disconnected_factors(self):
        domains = {'A': [0, 1], 'B': [0, 1], 'C': [0, 1]}
        fs = [bn.Factor([v], [], domains) for v in domains]
        for f in fs:
            for row in f.getAllPossibleAssignmentDicts(): f.setProbability(row, 2)
        joined = fo.joinFactors(fs)
        self.assertEqual(joined.unconditionedVariables(), set(domains))
        for row in joined.getAllPossibleAssignmentDicts(): self.assert_close(joined.getProbability(row), 8)

    def test_q2_supplied_duplicate_typecheck(self):
        f = bn.Factor(['A'], [], {'A': [0, 1]})
        with contextlib.redirect_stdout(io.StringIO()), self.assertRaises(ValueError): fo.joinFactors([f, f])

    def test_q3_arbitrary_domain_sum_and_immutability(self):
        domains = {'A': ['red', 'blue'], 'B': [2, 4, 9, 12], 'C': [False, True], 'Unused': [0]}
        f = bn.Factor(['A', 'B'], ['C'], domains)
        for i, row in enumerate(f.getAllPossibleAssignmentDicts()): f.setProbability(row, i * 0.23)
        before = str(f)
        result = fo.eliminate(f, 'B')
        self.assertEqual(result.unconditionedVariables(), {'A'})
        self.assertEqual(result.conditionedVariables(), {'C'})
        self.assertEqual(result.variableDomainsDict(), domains)
        for row in result.getAllPossibleAssignmentDicts():
            self.assert_close(result.getProbability(row), sum(f.getProbability(dict(row, B=b)) for b in domains['B']))
        self.assertEqual(before, str(f))

    def test_q3_singleton_eliminated_domain(self):
        domains = {'A': [0, 1], 'B': [4]}
        f = bn.Factor(['A', 'B'], [], domains)
        for row in f.getAllPossibleAssignmentDicts(): f.setProbability(row, 0.7)
        result = fo.eliminate(f, 'B')
        for row in result.getAllPossibleAssignmentDicts(): self.assert_close(result.getProbability(row), 0.7)

    def test_q3_typechecks_and_tracking(self):
        domains = {'A': [0, 1], 'B': [0, 1]}
        f = bn.Factor(['A'], ['B'], domains)
        for variable in ['A', 'B', 'Missing']:
            trace = []
            with contextlib.redirect_stdout(io.StringIO()), self.assertRaises(ValueError):
                fo.eliminateWithCallTracking(trace)(f, variable)
            self.assertEqual(trace, [('eliminate', variable)])

    def test_q4_exact_operation_sequence(self):
        rng = random.Random(7)
        domains = {v: [0, 1] for v in ['A', 'B', 'C', 'D']}
        net = make_net(domains, [('A', 'B'), ('B', 'C'), ('C', 'D')], rng)
        trace = []
        inference.inferenceByVariableEliminationWithCallTracking(trace)(net, ['A'], {'D': 1}, ['B', 'C'])
        self.assertEqual(trace, [('join', 'B'), ('eliminate', 'B'), ('join', 'C'), ('eliminate', 'C')])
        self.check_inference(net, ['A'], {'D': 1}, ['B', 'C'])

    def test_q4_discard_leaf_exact_sequence(self):
        net = make_net({'A': [0, 1], 'B': [0, 1], 'C': [0, 1]}, [('A', 'B')], random.Random(3))
        trace = []
        inference.inferenceByVariableEliminationWithCallTracking(trace)(net, ['A'], {}, ['B', 'C'])
        self.assertEqual(trace, [('join', 'B'), ('join', 'C')])
        self.check_inference(net, ['A'], {}, ['B', 'C'])

    def test_q4_no_hidden_variables(self):
        net = make_net({'A': [0, 1], 'B': [0, 1]}, [('A', 'B')], random.Random(8))
        self.check_inference(net, ['A'], {'B': 0}, [])
        self.check_inference(net, ['A', 'B'], {}, [])

    def test_q4_singleton_query(self):
        net = make_net({'A': ['only'], 'B': [0, 1]}, [('A', 'B')], random.Random(9))
        self.check_inference(net, ['A'], {}, ['B'])

    def test_q4_impossible_evidence(self):
        net = make_net({'A': [0, 1], 'B': [0, 1], 'C': [0, 1]},
                       [('A', 'B'), ('B', 'C')], random.Random(1), deterministic=True)
        self.check_inference(net, ['A'], {'C': 1}, ['B'])

    def test_q4_random_dags_all_orders(self):
        rng = random.Random(537)
        query_count = 0
        for trial in range(100):
            names = [f'Node_{i}' for i in range(rng.randint(2, 6))]
            domains = {v: list(range(rng.randint(2, 3))) for v in names}
            edges = [(a, b) for i, a in enumerate(names) for b in names[i+1:] if rng.random() < 0.4]
            net = make_net(domains, edges, rng)
            shuffled = rng.sample(names, len(names))
            query = shuffled[:rng.randint(1, min(2, len(names)))]; rest = shuffled[len(query):]
            evvars = rest[:rng.randint(0, min(2, len(rest)))]
            evidence = {v: rng.choice(domains[v]) for v in evvars}
            hidden = sorted(set(names) - set(query) - set(evidence))
            for order in [None] + list(itertools.permutations(hidden)):
                with self.subTest(trial=trial, query=query, evidence=evidence, order=order):
                    self.check_inference(net, query, evidence, order)
                query_count += 1
        print(f'Independent exhaustive oracle: {query_count} inference queries across 100 random DAGs.')


if __name__ == '__main__':
    unittest.main(verbosity=2)
