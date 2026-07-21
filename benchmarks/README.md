# Benchmarks

Two small scripts that exercise the analyze-and-render pipeline offline.
They are meant to be run before pushing a change to make sure perf and
cost stay inside the budgets documented in `README.md`.

## `perf.py`

```
make bench                # default 50 issues, 3 repeats
python benchmarks/perf.py --issues 200 --repeats 5
```

The script synthesises fake issues with realistic signal distributions,
runs the full `IssueAnalyzer.analyze` -> `ReportGenerator.generate_markdown`
path against a stubbed LLM, and prints min / median / mean / max
elapsed time. The v0.1 success criteria ask for `< 5 minutes`; the
script should report sub-second numbers on a developer laptop.

## `cost.py`

```
make bench-cost           # default claude-sonnet-4, 50 issues
python benchmarks/cost.py --model gpt-4o-mini --issues 30
```

Prints the estimated prompt and completion token counts and the
implied USD cost using each provider's published list prices. Numbers
are estimates; the authoritative count is the one in the generated
report's `## Cost` section.
