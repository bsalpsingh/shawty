# shawty 😄

A URL shortener. Yes, again 🙃. No, that's not really the point.

## Why this exists

This is stop #1 in an ongoing project to actually *get* distributed systems, instead of just nodding along in system design interviews. Build it, break it, understand it — one piece at a time.

I'm not chasing product polish or a feature list here. I'm chasing the boring-but-mighty stuff you'd sketch out on a Hello Interview-style whiteboard: API gateways, load balancers, caches, databases (SQL and NoSQL), message queues, CDNs, consistent hashing, rate limiters, sharding, replication, service discovery, container orchestration. The unglamorous plumbing that somehow holds the whole internet together. Each project in this series grabs one slice of that world and takes it apart to see what makes it tick.

## How this is built

The old-fashioned way, on purpose 😌.

Agent harnesses and code-generators are kept on a short leash here. I type the lines, weigh the dependencies, hunt the bugs myself 😅. Fluency is a muscle — it goes soft fast if you're not using it — so if a tool designs the schema or scaffolds the service for me, I've just outsourced the exact thing I showed up to learn.

Translation:

- Docs before shortcuts.
- Boilerplate, tedium and all, typed by hand.
- Mistakes happen, get fixed, get written down 😬.
- Agents are for asking questions, not for handing me code I haven't read.

## What you'll find here

- `app/` — the FastAPI service, split into `api`, `core`, `db`, `models`, `schema`, `utils`.
- `alembic/` — schema migrations.
- `docs/` — the HLD sketch I'm building from (and sometimes arguing with).
- `manifests/` — Kubernetes manifests for the bits living outside the app.
- `tests/` — slow, deliberate, and slowly growing.

Stack so far: FastAPI · SQLAlchemy (async) · asyncpg · Redis · Alembic · pybase62 — packaged with `uv`, on Python 3.13.

## What this isn't

- Not production-ready, and not pretending otherwise 😅.
- Not a tutorial — this is for me, not an audience.
- Not a benchmark. I won't dress up a choice as optimal just because it sounds better in a README.

## The series

`shawty` is #1. Next up: other flavors of distributed pain — coordination, consensus, sharding, queues, streaming, replication, the whole tangled mess. Each one gets its own repo, its own HLD, and its own scars.

If this looks naive in six months, good. That means it worked 😄.