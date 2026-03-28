import io
import sys

from pathweaver.metrics import format_comparison_table, run_comparison
from pathweaver.scenarios import ALL_SCENARIOS

SEPARATOR = "-" * 60


def validate_all() -> str:
    buf = io.StringIO()

    def out(line: str = "") -> None:
        print(line)
        buf.write(line + "\n")

    for scenario in ALL_SCENARIOS:
        out(f"Scenario: {scenario.name}")
        out(f"Description: {scenario.description}")
        out(f"Agents: {len(scenario.agents)}  Grid: {scenario.grid.width}x{scenario.grid.height}")
        out()

        results = run_comparison(scenario.grid, scenario.agents)
        out(format_comparison_table(results))
        out()

        for r in results:
            if r.algorithm == "CBS" and r.capped:
                out(f"WARNING: CBS hit node limit on this scenario")
            if not r.success:
                out(f"WARNING: {r.algorithm} failed to find paths for all agents")

        out(SEPARATOR)

    return buf.getvalue()


if __name__ == "__main__":
    content = validate_all()
    with open("results.md", "w") as f:
        f.write(content)
    print("\nResults written to results.md")
