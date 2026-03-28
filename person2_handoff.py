from pathweaver.metrics import format_comparison_table, run_comparison
from pathweaver.scenarios import ALL_SCENARIOS, get_scenario

SCENARIO_NAMES = [s.name for s in ALL_SCENARIOS]

failures = []


def fail(check, msg: str) -> None:
    print(f"FAIL  {check}: {msg}")
    failures.append(check)


def passed(check: int, label: str) -> None:
    print(f"PASS  {check}: {label}")


# ---------------------------------------------------------------------------
# Check 1: all 4 scenarios load from get_scenario()
# ---------------------------------------------------------------------------
loaded = {}
check1_ok = True
for name in SCENARIO_NAMES:
    try:
        loaded[name] = get_scenario(name)
    except Exception as e:
        fail(1, f"get_scenario({name!r}) raised {e}")
        check1_ok = False

if check1_ok and len(loaded) == 4:
    passed(1, "All 4 scenarios load via get_scenario()")
elif check1_ok:
    fail(1, f"Expected 4 scenarios, got {len(loaded)}")

# ---------------------------------------------------------------------------
# Check 2: each scenario has >= 2 agents, no agent starts on an obstacle
# ---------------------------------------------------------------------------
check2_ok = True
for name, s in loaded.items():
    if len(s.agents) < 2:
        fail(2, f"{name}: only {len(s.agents)} agent(s)")
        check2_ok = False
    for i, (start, goal) in enumerate(s.agents):
        if not s.grid.passable(start):
            fail(2, f"{name} agent {i}: start {start} is on an obstacle")
            check2_ok = False
if check2_ok:
    passed(2, "All scenarios have >= 2 agents, no start on obstacle")

# ---------------------------------------------------------------------------
# Check 3: no agent goal on an obstacle
# ---------------------------------------------------------------------------
check3_ok = True
for name, s in loaded.items():
    for i, (start, goal) in enumerate(s.agents):
        if not s.grid.passable(goal):
            fail(3, f"{name} agent {i}: goal {goal} is on an obstacle")
            check3_ok = False
if check3_ok:
    passed(3, "No agent goal is on an obstacle")

# ---------------------------------------------------------------------------
# Run comparisons once (reused by checks 4-8)
# ---------------------------------------------------------------------------
results_by_scenario = {}
for name, s in loaded.items():
    results_by_scenario[name] = run_comparison(s.grid, s.agents)

# ---------------------------------------------------------------------------
# Check 4: run_comparison returns exactly 4 AlgorithmResult objects
# ---------------------------------------------------------------------------
check4_ok = True
for name, results in results_by_scenario.items():
    if len(results) != 4:
        fail(4, f"{name}: got {len(results)} results, expected 4")
        check4_ok = False
if check4_ok:
    passed(4, "run_comparison() returns exactly 4 results for each scenario")

# ---------------------------------------------------------------------------
# Check 5: each result has algorithm name set, makespan > 0,
#           per_agent length == agent count
# ---------------------------------------------------------------------------
check5_ok = True
for name, results in results_by_scenario.items():
    n_agents = len(loaded[name].agents)
    for r in results:
        if not r.algorithm:
            fail(5, f"{name}/{r.algorithm!r}: algorithm name is empty")
            check5_ok = False
        if r.makespan <= 0:
            fail(5, f"{name}/{r.algorithm}: makespan={r.makespan} (expected > 0)")
            check5_ok = False
        if len(r.per_agent) != n_agents:
            fail(5, f"{name}/{r.algorithm}: per_agent length {len(r.per_agent)} != {n_agents}")
            check5_ok = False
if check5_ok:
    passed(5, "All results have algorithm name, makespan > 0, correct per_agent length")

print(
    "Note: Prioritized/Cooperative A* may show residual conflicts when "
    "an earlier agent's path passes through a later agent's goal cell. "
    "This is a known property of priority-based planning, not a bug."
)
print()

# ---------------------------------------------------------------------------
# Check 6a: CBS conflicts == 0 on all scenarios
# CBS guarantees optimality and conflict-freedom within its node cap.
# ---------------------------------------------------------------------------
check6a_ok = True
for name, results in results_by_scenario.items():
    for r in results:
        if r.algorithm == "CBS" and r.conflicts != 0:
            fail("6a", f"{name}/CBS: conflicts={r.conflicts} (expected 0)")
            check6a_ok = False
if check6a_ok:
    passed("6a", "CBS has 0 conflicts on all scenarios")

# ---------------------------------------------------------------------------
# Check 6b: Independent planning has conflicts > 0 on crossing and bottleneck
# Sanity check that conflict detection is working — independent planning
# should always collide on these adversarial scenarios.
# ---------------------------------------------------------------------------
check6b_ok = True
for name in ("crossing", "bottleneck"):
    if name not in results_by_scenario:
        fail("6b", f"scenario {name!r} not found in results")
        check6b_ok = False
        continue
    for r in results_by_scenario[name]:
        if r.algorithm == "Independent" and r.conflicts == 0:
            fail("6b", f"{name}/Independent: conflicts=0 (expected > 0 — conflict detection may be broken)")
            check6b_ok = False
if check6b_ok:
    passed("6b", "Independent planning has conflicts > 0 on crossing and bottleneck")

# ---------------------------------------------------------------------------
# Check 7: CBS capped is False on all scenarios
# ---------------------------------------------------------------------------
check7_ok = True
for name, results in results_by_scenario.items():
    for r in results:
        if r.algorithm == "CBS" and r.capped:
            fail(7, f"{name}/CBS: capped=True (hit node limit)")
            check7_ok = False
if check7_ok:
    passed(7, "CBS capped=False on all scenarios")

# ---------------------------------------------------------------------------
# Check 8: format_comparison_table returns a non-empty string per scenario
# ---------------------------------------------------------------------------
check8_ok = True
for name, results in results_by_scenario.items():
    table = format_comparison_table(results)
    if not table.strip():
        fail(8, f"{name}: format_comparison_table() returned empty string")
        check8_ok = False
if check8_ok:
    passed(8, "format_comparison_table() returns non-empty string for each scenario")

# ---------------------------------------------------------------------------
# Check 9: get_scenario("nonexistent") raises ValueError
# ---------------------------------------------------------------------------
try:
    get_scenario("nonexistent")
    fail(9, "get_scenario('nonexistent') did not raise ValueError")
except ValueError:
    passed(9, "get_scenario('nonexistent') raises ValueError")
except Exception as e:
    fail(9, f"get_scenario('nonexistent') raised {type(e).__name__} instead of ValueError: {e}")

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
print()
if not failures:
    print("Person 2 handoff complete. Ready for Person 3.")
else:
    print(f"Failed checks: {sorted(set(failures))}")
