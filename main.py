import argparse
import copy
import time
from itertools import product
import string

# and
class Conjunction:
    def __init__(self):
        self.children = []
        self.unit_clauses = []
        self.backtracing_clauses = []
        self._stack = []
        self.trail = []

    def model(self, include_unassigned=False, default=False):
        m = {}
        for name, val in self.trail:
            m[name] = val
        if include_unassigned:
            names = set(m)
            for clause in self.children:
                for lit in clause.children:
                    names.add(lit.name)
            return {n: m.get(n, default) for n in sorted(names)}
        return dict(sorted(m.items()))

    def get_all(self):
        population = []
        for child in self.children:
            if not child.always_true:
                population.append(child.get_all())
        return population

    def get_falsifiable_children(self):
        return [child for child in self.children if not child.always_true]

    def remove_tautologies(self):
        self.children = self.get_falsifiable_children()

    def clean(self):
        self.remove_tautologies()
        for child in self.children:
            child.remove_false_children()

    def prune(self):
        for child in self.children:
            child.simplify()

    def process_unit_clauses(self):
        self.unit_clauses = []
        for child in self.children:
            if child.is_unit_clause():
                child.set_value(True)
                child.check_values()
                self.unit_clauses.append(child.children[0])
                self.trail.append((child.children[0].name, child.children[0].variable_value))
        self.propagate_clauses(self.unit_clauses)

    def _pick_clause_index(self):
        for i, child in enumerate(self.children):
            if not getattr(child, "always_true", False) and len(child.children) > 0:
                return i
        return None

    def backtracing(self):
        idx = self._pick_clause_index()
        if idx is None:
            return
        self._stack.append({"snap": copy.deepcopy(self), "idx": idx, "flipped": False})
        self.backtracing_clauses = []
        chosen = self.children[idx].set_value_return_literal(True)
        self.backtracing_clauses.append(chosen)
        self.trail.append((chosen.name, chosen.variable_value)) 
        self.propagate_clauses(self.backtracing_clauses)

    def try_flip_last(self):
        while self._stack:
            frame = self._stack[-1]
            if not frame["flipped"]:
                restored = copy.deepcopy(frame["snap"])
                self.__dict__ = restored.__dict__
                frame["flipped"] = True
                self.backtracing_clauses = []
                idx = frame["idx"]
                if idx is None or idx >= len(self.children) or getattr(self.children[idx], "always_true", False) or len(self.children[idx].children) == 0:
                    idx = self._pick_clause_index()
                    frame["idx"] = idx
                    if idx is None:
                        return True
                chosen = self.children[idx].set_value_return_literal(False)
                self.backtracing_clauses.append(chosen)
                self.trail.append((chosen.name, chosen.variable_value))
                self.propagate_clauses(self.backtracing_clauses)
                return True
            else:
                self._stack.pop()
        return False

    def propagate_clauses(self, clauses):
        for child in self.children:
            child.propagate_clauses(clauses)

    def find_conflict(self):
        return any(getattr(l, "conflict", False) for l in self.unit_clauses + self.backtracing_clauses)

    def check_values(self):
        for child in self.children:
            child.check_values()

    def __str__(self):
        res = ''
        for i, child in enumerate(self.children):
            if i == len(self.children) - 1:
                res += f'{str(child)}'
            else:
                res += f'{str(child)}, '
        return f'{{{res}}}'

# or
class Disjunction:
    def __init__(self):
        self.children = []
        self.always_true = False

    def get_all(self):
        return self.children

    def get_falsifiable_children(self):
        return [child for child in self.children if child.value is True or child.value is None]

    def remove_false_children(self):
        self.children = self.get_falsifiable_children()

    def is_unit_clause(self):
        return len(self.children) == 1

    def set_value(self, value):
        for child in self.children:
            child.set_value(value ^ child.negated)

    def set_value_return_literal(self, value):
        self.children[0].set_value(value ^ self.children[0].negated)
        return self.children[0]

    def simplify(self):
        for child in self.children:
            for other in self.children:
                if child.is_negative_of(other):
                    self.always_true = True

    def check_values(self):
        for child in self.children:
            if child.value:
                self.always_true = True
                return True

    def propagate_clauses(self, clauses):
        for child in self.children:
            child.propagate_clauses(clauses)

    def __str__(self):
        if self.always_true:
            return '{True}'
        res = ''
        for i, child in enumerate(self.children):
            if i == len(self.children) - 1:
                res += f'{str(child)}'
            else:
                res += f'{str(child)}, '
        return f'{{{res}}}'

class Literal:
    def __init__(self, name):
        self.variable_value = None
        self.name = name
        self.negated = False
        self.conflict = False
        self.parse()

    @property
    def value(self):
        if self.variable_value is None:
            return None
        return not self.variable_value if self.negated else self.variable_value

    def set_value(self, value):
        self.variable_value = value

    def is_negative_of(self, other):
        if other.name == self.name and other.negated != self.negated:
            return True
        return False

    def propagate_clauses(self, clauses):
        for literal in clauses:
            if literal == self:
                if (self.variable_value is not None and self.variable_value != literal.variable_value):
                    self.conflict = True
                    return
                self.variable_value = literal.variable_value

    def parse(self):
        n = self.name.strip()
        if n.startswith('-'):
            self.negated = True
            n = n[1:]
        self.name = n

    def __str__(self):
        if self.value is not None:
            return 'True' if self.value else 'False'
        return f'-{self.name}' if self.negated else self.name

    def __eq__(self, other):
        return self.name == other.name

def _parser(formula):
    formula = formula.replace('¬', '-')
    formula = formula.strip().replace(' ', '')
    conjunctions = formula.split('},')
    output = []
    for conjunction in conjunctions:
        disjunction = conjunction.strip().strip('{').strip('}').split(',')
        output.append(disjunction)
    _conjunction = Conjunction()
    for conjunction in output:
        _disjunction = Disjunction()
        for disjunction_literal in conjunction:
            _literal = Literal(disjunction_literal)
            _disjunction.children.append(_literal)
        _conjunction.children.append(_disjunction)
    return _conjunction


def generate_unsat_formula(n):
    vars_ = list(string.ascii_lowercase[:n])

    clauses = []
    for assignment in product([True, False], repeat=n):
        lits = []
        for v, val in zip(vars_, assignment):
            lits.append(f"-{v}" if val else v)
        clauses.append("{" + ",".join(lits) + "}")
    return "{" + ",".join(clauses) + "}"


def solve(parsed, verbose=True):
    def vprint(*a, **k):
        if verbose:
            print(*a, **k)

    vprint("Solving:")
    vprint(parsed)
    vprint("=" * 50)

    while True:
        vprint("Current Formula:")
        vprint(parsed)
        vprint("-" * 50)

        # Prune the formula
        parsed.prune()
        vprint("After Pruning:")
        vprint(parsed)
        vprint("-" * 50)

        # Clean after pruning
        parsed.clean()
        vprint("After Cleaning (Post-Pruning):")
        vprint(parsed)
        vprint("-" * 50)

        # Process unit clauses
        parsed.process_unit_clauses()
        vprint("After Processing Unit Clauses:")
        if parsed.find_conflict():
            if parsed.try_flip_last():
                vprint("After Flipping Last Decision:")
                vprint(parsed)
                vprint("-" * 50)
                continue
            vprint("UNSATISFIABLE!")
            return False, None

        vprint(parsed)
        vprint("-" * 50)

        # Clean after processing unit clauses
        parsed.clean()
        vprint("After Cleaning (Post-Unit Clauses):")
        vprint(parsed)
        vprint("-" * 50)

        # Check values
        parsed.check_values()
        vprint("After Checking Values:")
        vprint(parsed)
        vprint("-" * 50)

        # Clean after checking values
        parsed.clean()
        vprint("After Cleaning (Post-Checking Values):")
        vprint(parsed)
        vprint("-" * 50)

        # Check for termination conditions
        if not parsed.children:
            vprint("SATISFIABLE!")
            model = parsed.model(include_unassigned=True, default=False)
            vprint("Model:", model)
            return True, model

        if any(len(child.children) == 0 for child in parsed.children):
            if parsed.try_flip_last():
                vprint("After Flipping Last Decision:")
                vprint(parsed)
                vprint("-" * 50)
                continue
            vprint("UNSATISFIABLE!")
            return False, None

        # Perform backtracking (decision)
        parsed.backtracing()
        vprint("After Backtracking:")
        if parsed.find_conflict():
            if parsed.try_flip_last():
                vprint("After Flipping Last Decision:")
                vprint(parsed)
                vprint("-" * 50)
                continue
            vprint("UNSATISFIABLE!")
            return False, None
        vprint(parsed)
        vprint("-" * 50)

        # Clean after backtracking
        parsed.clean()
        vprint("After Cleaning (Post-Backtracking):")
        vprint(parsed)
        vprint("-" * 50)


def main():
    parser = argparse.ArgumentParser("SAT Solver")
    parser.add_argument(
        'formula',
        nargs=argparse.REMAINDER,
        help='e.g. {{-a, b}, {-v, r, q}}',
    )

    parser.add_argument(
        '-b', '--benchmark',
        type=int,
        metavar='N',
        help='run benchmark for n=1..N on the 2^n-clause UNSAT family'
    )

    args = parser.parse_args()

    if args.benchmark is not None:
        N = args.benchmark
        if N < 1:
            raise SystemExit("Benchmark N must be >= 1")

        print(f"Benchmark: classic 2^n-clause UNSAT family (n = 1..{N})")
        print("-" * 60)
        print(f"{'n':>2}  {'clauses':>7}  {'result':>6}  {'time':>8}")
        print("-" * 60)

        for n in range(1, N + 1):
            cnf_str = generate_unsat_formula(n)
            parsed = _parser(cnf_str)

            t0 = time.perf_counter()
            sat, _ = solve(parsed, verbose=False)
            dt = time.perf_counter() - t0

            result = "SAT" if sat else "UNSAT"
            print(f"{n:>2}  {2**n:>7}  {result:>6}  {dt:>8.4f}")

        print("-" * 60)
        return

    formula = ' '.join(args.formula)
    parsed = _parser(formula)
    solve(parsed, True)

if __name__ == "__main__":
    main()
