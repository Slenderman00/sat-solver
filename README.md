# Sat Solver

I have developed an object oriented Sat Solver, using a naive approach. The solver consists of three classes:

    1. Conjunction class (And)
    2. Disjunction class (Or)
    3. Literal class

The conjunctive class contains disjunctive objects whilst the 
disjunctive class contains literals. Each literal can be negated. Each class is responsible for pruning itself and its children. This approach worked extremely well until I realized I hadnt taken backtracking. 

The backtracking follows a simple heuristic, it will always try to assign a value to the first unsatisfied literal of the first unsatisfied clause. If a conflict is detected, the solver assumes this was a result of the last assigned value and therefor it backtracks and flips it. To handle backtracking the solver uses deepcopy to create copies of itself and all child classes, this unefficient and uses way more memory than needed but it works.

## Benchmark

```
(.venv) [joar@archlinux sat-solver]$ python3 main.py -b 10
Benchmark: classic 2^n-clause UNSAT family (n = 1..10)
------------------------------------------------------------
 n  clauses  result  time (s)
------------------------------------------------------------
 1        2   UNSAT    0.0000
 2        4   UNSAT    0.0002
 3        8   UNSAT    0.0008
 4       16   UNSAT    0.0046
 5       32   UNSAT    0.0285
 6       64   UNSAT    0.1844
 7      128   UNSAT    1.2619
 8      256   UNSAT    8.6350
 9      512   UNSAT   62.3218
10     1024   UNSAT  445.4178
------------------------------------------------------------
```
This clearly shows that the benchmark time grows exponentially with n. 
This is expected as the clauses also grows exponentially with n

## Example
The solver will also print out how it solves and a model when given a single problem to solve.
```
(.venv) [joar@archlinux sat-solver]$ python3 main.py {{p, q, r}, {p, q, -r}, {p, -q, r}, {p, -q, -r}, {-p, q, r}, {-p, q, -r}, {-p, ¬q, r}}
Solving:
{{p, q, r}, {p, q, -r}, {p, -q, r}, {p, -q, -r}, {-p, q, r}, {-p, q, -r}, {-p, -q, r}}
==================================================
Current Formula:
{{p, q, r}, {p, q, -r}, {p, -q, r}, {p, -q, -r}, {-p, q, r}, {-p, q, -r}, {-p, -q, r}}
--------------------------------------------------
After Pruning:
{{p, q, r}, {p, q, -r}, {p, -q, r}, {p, -q, -r}, {-p, q, r}, {-p, q, -r}, {-p, -q, r}}
--------------------------------------------------
After Cleaning (Post-Pruning):
{{p, q, r}, {p, q, -r}, {p, -q, r}, {p, -q, -r}, {-p, q, r}, {-p, q, -r}, {-p, -q, r}}
--------------------------------------------------
After Processing Unit Clauses:
{{p, q, r}, {p, q, -r}, {p, -q, r}, {p, -q, -r}, {-p, q, r}, {-p, q, -r}, {-p, -q, r}}
--------------------------------------------------
After Cleaning (Post-Unit Clauses):
{{p, q, r}, {p, q, -r}, {p, -q, r}, {p, -q, -r}, {-p, q, r}, {-p, q, -r}, {-p, -q, r}}
--------------------------------------------------
After Checking Values:
{{p, q, r}, {p, q, -r}, {p, -q, r}, {p, -q, -r}, {-p, q, r}, {-p, q, -r}, {-p, -q, r}}
--------------------------------------------------
After Cleaning (Post-Checking Values):
{{p, q, r}, {p, q, -r}, {p, -q, r}, {p, -q, -r}, {-p, q, r}, {-p, q, -r}, {-p, -q, r}}
--------------------------------------------------
After Backtracking:
{{True, q, r}, {True, q, -r}, {True, -q, r}, {True, -q, -r}, {False, q, r}, {False, q, -r}, {False, -q, r}}
--------------------------------------------------
After Cleaning (Post-Backtracking):
{{True, q, r}, {True, q, -r}, {True, -q, r}, {True, -q, -r}, {q, r}, {q, -r}, {-q, r}}
--------------------------------------------------
Current Formula:
{{True, q, r}, {True, q, -r}, {True, -q, r}, {True, -q, -r}, {q, r}, {q, -r}, {-q, r}}
--------------------------------------------------
After Pruning:
{{True, q, r}, {True, q, -r}, {True, -q, r}, {True, -q, -r}, {q, r}, {q, -r}, {-q, r}}
--------------------------------------------------
After Cleaning (Post-Pruning):
{{True, q, r}, {True, q, -r}, {True, -q, r}, {True, -q, -r}, {q, r}, {q, -r}, {-q, r}}
--------------------------------------------------
After Processing Unit Clauses:
{{True, q, r}, {True, q, -r}, {True, -q, r}, {True, -q, -r}, {q, r}, {q, -r}, {-q, r}}
--------------------------------------------------
After Cleaning (Post-Unit Clauses):
{{True, q, r}, {True, q, -r}, {True, -q, r}, {True, -q, -r}, {q, r}, {q, -r}, {-q, r}}
--------------------------------------------------
After Checking Values:
{{True}, {True}, {True}, {True}, {q, r}, {q, -r}, {-q, r}}
--------------------------------------------------
After Cleaning (Post-Checking Values):
{{q, r}, {q, -r}, {-q, r}}
--------------------------------------------------
After Backtracking:
{{True, r}, {True, -r}, {False, r}}
--------------------------------------------------
After Cleaning (Post-Backtracking):
{{True, r}, {True, -r}, {r}}
--------------------------------------------------
Current Formula:
{{True, r}, {True, -r}, {r}}
--------------------------------------------------
After Pruning:
{{True, r}, {True, -r}, {r}}
--------------------------------------------------
After Cleaning (Post-Pruning):
{{True, r}, {True, -r}, {r}}
--------------------------------------------------
After Processing Unit Clauses:
{{True, True}, {True, False}, {True}}
--------------------------------------------------
After Cleaning (Post-Unit Clauses):
{{True, True}, {True}}
--------------------------------------------------
After Checking Values:
{{True}, {True}}
--------------------------------------------------
After Cleaning (Post-Checking Values):
{}
--------------------------------------------------
SATISFIABLE!
Model: {'p': True, 'q': True, 'r': True}
```
