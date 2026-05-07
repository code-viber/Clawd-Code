# Architecture Notes

## Problem framing

EDA regressions generate large volumes of semi-structured logs across Linux job
farms. The expensive part is not just detecting an error; it is quickly deciding
whether the issue is a timing/design problem, a tool crash, a shared
infrastructure outage, or a database integrity risk, then routing it to the
right owner with enough context to reproduce it.

Silicon Signal Triage demonstrates a local version of that workflow:

```text
EDA logs -> parser -> signature builder -> rendezvous scheduler -> runbook report
```

## Components

- `parser.py` converts structured log lines into typed `LogRecord` objects and
  quarantines malformed lines.
- `signatures.py` normalizes variable values, classifies operational category,
  and creates deterministic BLAKE2 signatures.
- `scheduler.py` groups signatures and assigns them with weighted rendezvous
  hashing. Specialty and capacity bias routing while preserving stability.
- `render.py` produces a human-readable report for engineers and managers.
- `profiler.py` separates parse latency from triage latency for quick local
  experiments.
- `cpp/signature_index.cpp` is an optional native prototype for the signature
  indexing stage if profiling shows Python is not enough.

## Why rendezvous hashing

Rendezvous hashing scores every `(signature, worker)` pair and picks the highest
score. Compared with modulo-based routing, it avoids broad reassignment when the
worker set changes. That matters for EDA support because issue ownership often
spans multiple reruns, reproducers, and customer updates.

The demo adds two production-oriented weights:

1. **Capacity**: larger support pools take more signatures.
2. **Specialty**: timing issues prefer timing owners, crash issues prefer debug
   owners, and infra issues prefer follow-the-sun infrastructure owners.

## Scaling path

The local CLI is deliberately easy to run in an interview, but the seams map to
an enterprise service:

1. Replace file parsing with stream ingestion from job schedulers or object
   storage notifications.
2. Persist signatures, jobs, and ownership in a database with audit history.
3. Run workers behind Unix sockets, gRPC, or a message queue depending on site
   constraints.
4. Add tool-specific plug-ins for PrimeTime, VCS, ICC2, Formality, and internal
   flows.
5. Export metrics for queue length, duplicate suppression, mean time to owner,
   and recurring failure rate.

## Reliability and debugging posture

- Malformed input is isolated rather than crashing the whole triage pass.
- Signature IDs are deterministic for reproducible tests and audit links.
- Output includes rationale and reproducer hints, not just labels.
- The native prototype remains optional until measurements justify operational
  complexity.
