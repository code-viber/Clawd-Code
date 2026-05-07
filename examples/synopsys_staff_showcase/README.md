# Silicon Signal Triage

Silicon Signal Triage is a self-contained interview showcase for the Synopsys
Senior Staff Software Engineer role. It models a Common Engineering Components
platform that helps R&D engineers, FAEs, and customers identify, diagnose, and
route EDA tool failures from large regression farms.

The project is intentionally compact, but it demonstrates senior-staff signals:

- **EDA workflow empathy**: log signatures for timing closure, tool crashes,
  license infrastructure, storage, and design database failures.
- **Distributed-systems design**: weighted rendezvous hashing keeps issue
  ownership stable as support workers are added or removed.
- **Unix/Linux practicality**: newline-oriented logs, shell demo script, JSON
  topology, and an optional C++17 hot-path prototype.
- **Performance mindset**: deterministic signatures, bounded normalization, and
  a profiling helper that separates parse and triage latency.
- **Operational communication**: every assignment includes priority, rationale,
  action, reproducer guidance, owner, and blast radius.

## Run the demo

```bash
./examples/synopsys_staff_showcase/scripts/run_demo.sh
```

Or run the CLI directly:

```bash
PYTHONPATH=examples/synopsys_staff_showcase/python \
python -m eda_hpc_triage.cli triage \
  examples/synopsys_staff_showcase/sample_data/regression.log \
  --workers examples/synopsys_staff_showcase/sample_data/workers.json
```

Machine-readable output:

```bash
PYTHONPATH=examples/synopsys_staff_showcase/python \
python -m eda_hpc_triage.cli triage \
  examples/synopsys_staff_showcase/sample_data/regression.log \
  --json
```

## Optional native hot path

The Python workflow is the product demo. The C++ file sketches how a profiled
signature-indexing hot path could be moved into native code:

```bash
cd examples/synopsys_staff_showcase/cpp
c++ -std=c++17 -O2 -Wall -Wextra -pedantic signature_index.cpp -o signature_index
./signature_index < ../sample_data/regression.log
```

## What to discuss in an interview

1. How stable hashing minimizes queue churn during worker topology changes.
2. Where to insert sockets, message queues, or a database when moving from local
   CLI to an enterprise service.
3. How to measure parser throughput and decide whether native acceleration is
   justified.
4. How failure signatures can be enriched with tool metadata, design hierarchy,
   customer impact, and regression ownership.
5. How to mentor teams using concise runbooks and reproducible failure capture.

See [ARCHITECTURE.md](ARCHITECTURE.md) for design details.
