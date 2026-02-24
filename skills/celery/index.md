# Celery Skills

Based on Celery 5.6.2 documentation.
Generated from https://docs.celeryq.dev/en/stable/ on 2026-02-24.

## Available Skills

| Skill | Topics Covered | Lines |
|-------|---------------|-------|
| [fundamentals](./fundamentals.md) | App setup, configuration, task definition, calling tasks, results, signatures, canvas intro, project layout | 291 |
| [tasks](./tasks.md) | Task decorator options, bound tasks, retries, autoretry, states, lifecycle handlers, custom task classes, Pydantic validation | 318 |
| [calling-canvas](./calling-canvas.md) | delay/apply_async, signatures, partials, immutable, chain, group, chord, chunks, map/starmap, workflow patterns | 348 |
| [workers](./workers.md) | Starting workers, concurrency pools, lifecycle, celery multi, remote control, revoking, queues, time limits, autoscaling, daemonization | 343 |
| [periodic-tasks](./periodic-tasks.md) | Celery Beat, beat_schedule, crontab, solar, intervals, database scheduler, timezone handling | 188 |
| [routing](./routing.md) | task_routes, queue config, AMQP exchanges, custom routers, priority queues, broadcast routing | 209 |
| [monitoring-ops](./monitoring-ops.md) | Flower, inspect/control commands, events, real-time monitoring, optimization, prefetch tuning, debugging | 217 |
| [brokers-backends](./brokers-backends.md) | RabbitMQ, Redis, SQS, result backends (Redis, RPC, Django ORM, database), visibility timeout | 183 |
| [configuration](./configuration.md) | All key settings by category (broker, result, task, worker, beat, security), config patterns | 190 |
| [signals-testing](./signals-testing.md) | All signals (task, worker, beat), pytest fixtures, unit testing patterns, security, message signing | 236 |
| [django](./django.md) | Django integration (celery.py, shared_task, autodiscover, settings), transaction safety, django-celery-results/beat | 247 |
| [extensions](./extensions.md) | Bootsteps, custom components, blueprints, timer API, gossip callbacks, CLI options, third-party extensions | 206 |

## How to Use

Reference individual skills in your project's CLAUDE.md:

    @~/.claude/skills/celery/tasks.md
    @~/.claude/skills/celery/calling-canvas.md

Or reference this index to see all available skills:

    @~/.claude/skills/celery/index.md

## Coverage

- Total documentation pages read: ~30
- Skill files created: 12
- Total lines: 2,976
- Pages failed: 0
