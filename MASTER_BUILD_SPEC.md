# Agentic AI Automation Core System

Master Build Specification · Version 1.0 · 19 October 2026

Supersedes MASTER\_BUILD\_SPEC v1.1 · Audience: AI coding agents and human developers

## 1. Mission and Positioning

Build a secure, extensible AI automation core that accepts API and webhook events, executes bounded agentic workflows asynchronously, and integrates with cloud AI providers.

- **Default deployment:** one isolated VPS per customer, running as a single tenant.
- **Architecture:** tenant-aware from the first migration and scalable to a multi-tenant model by configuration and migration, not rewrite.
- **Extensibility:** industry capability is delivered through importable Industry Packs; the core remains industry-neutral.
- **Primary goal:** the smallest complete, secure, reliable, production-capable MVP.

Priorities, in order: security and privacy by default; tenant isolation; reliable execution and recovery; modular, replaceable components; testability and observability; low operating cost; continuous red-team validation; no fabricated results; explicit approval for material decisions.

Avoid microservices, Kubernetes, multiple databases, multiple AI providers, and heavyweight agent frameworks unless justified and approved.

## 2. Governance and Approval

This specification is an implementation baseline, not authorization for irreversible changes. Record approvals in `docs/decision-log.md` (decision, date, owner, approver, context, alternatives, rationale, security and operational impact, reversibility, evidence, status).

**Approval tiers**

| Tier | Scope | Approval |
| --- | --- | --- |
| 1 | Reversible, low-risk changes within approved design | Pull-request review |
| 2 | Architecture, security boundaries, data model, public API, pack format, integrations, cost limits | Named approver and decision-log entry |
| 3 | Production deployment, destructive migrations, secret changes, real billing, production data, accepted security risk | Named approver, recorded evidence, expiry date for exceptions |

Starting a new phase always requires approval. Approver response expectations are agreed in Phase 0.

**Baseline decisions confirmed in v1.0**

- Deployment default is an isolated VPS per customer (silo tier). Shared multi-tenant hosting uses pooled PostgreSQL with row-level security.
- Industry Packs are declarative only in the MVP. Executable pack code requires a separate approved phase.
- Vector memory uses pgvector inside PostgreSQL for the MVP.
- Cross-tenant learning, fine-tuning, and pooled content analytics are prohibited.
- Tenant memory is strictly isolated (Section 12).

**Open decisions, to close in Phase 0**

VPS provider, region, and sizing; AI provider, model, retention terms, and monthly budget; data sensitivity and applicable data-protection law; pack manifest format and signing scheme; backup destination, retention, and deletion SLA; per-tenant encryption keys (required or optional); first reference pack and its industry; webhook providers; RPO and RTO targets (proposed default: RPO 24 hours, RTO 4 hours); approval owners; minimum UI scope.

Where answers are unavailable, propose safe defaults, label them as assumptions, and obtain approval before material implementation.

**Agent protocol**

For each material task: state the intended outcome; identify assumptions and unresolved decisions; recommend an approach and alternatives; ask only consequential questions; wait for approval on irreversible, security-sensitive, externally visible, or costly changes; implement incrementally; report changed files, commands run, results, risks, and next steps. Never expose secrets or claim unexecuted results. Do not implement the platform in one unreviewed pass.

At the start of every task, read this specification and `AGENTS.md`, inspect the repository and Git state, identify the current phase and acceptance criteria, and check recorded approvals. After implementation, run relevant checks, perform a red-team review, add regression tests, update documentation and decision records, and request review before advancing phases or affecting production.

## 3. Product Scope

**MVP requirements**

- Responsive web UI for mobile and desktop with session-based login.
- Authenticated API access via API keys.
- API- and webhook-triggered workflows.
- Separate asynchronous Worker, Redis-based task distribution, and PostgreSQL persistence.
- Replaceable `LLMProvider` interface.
- Task submission, status, results, failures, retries, and cancellation.
- Industry Pack loader and registry with one reference pack.
- Tenant-isolated memory.
- Structured logs, health checks, security controls, and cost limits.
- CI, security testing, deployment verification, and rollback documentation.

**Initial exclusions:** unrestricted autonomous agents; arbitrary Python, SQL, or shell execution; executable pack code; complex visual workflow builders; multi-region high availability; automatic multi-provider routing; Kubernetes; unnecessary microservices.

Build the smallest complete end-to-end workflow first.

## 4. Technology Stack

| Layer | Technology |
| --- | --- |
| Language | Python 3.12+ |
| API | FastAPI, Pydantic |
| ORM and migrations | SQLAlchemy 2.x, Alembic |
| Database | PostgreSQL with pgvector |
| Queue | Redis Streams with consumer groups |
| Reliability | PostgreSQL transactional outbox |
| Worker | Separate Python process |
| AI | Cloud provider behind `LLMProvider` |
| Frontend | Lightweight responsive HTML, CSS, JavaScript |
| Local and VPS runtime | Docker Compose |
| CI | GitHub Actions |
| Testing | Pytest: unit, integration, security, resilience, E2E |
| Quality | Ruff and static type checking |
| Observability | Structured logs, OpenTelemetry-compatible instrumentation |

Pin dependencies and maintain a reproducible lockfile.

## 5. Architecture

```
Browser / API clients / Webhook providers
        |
  HTTPS reverse proxy (automatic TLS)
        |
  FastAPI API
   |-- Authentication, authorization, TenantContext, validation, rate limits
   |-- Task, webhook, workflow, pack, and approval APIs
   |
   |-- PostgreSQL (source of truth; pgvector)
   |     Tenants, users, workflows, tasks, attempts, outbox,
   |     packs, agent runs, memory, approvals, usage ledger
   |
   |-- Transactional outbox publisher
         |
     Redis Streams (tenant-namespaced)
         |
     Worker pool
         |
     Workflow and agent runtime (pack-defined, bounded)
         |
     LLMProvider -> Cloud AI API
```

**Architectural rules**

- PostgreSQL is the source of truth for durable state, results, memory, and audit records. Redis is a queue and coordination layer only.
- Use a transactional outbox. Assume at-least-once delivery and enforce idempotency. Never claim exactly-once execution.
- Scale API and Worker independently.
- Business logic is independent of Redis and provider SDKs.
- Introduce interfaces only where they provide real replacement or testing value.
- Cloudflare or any edge service does not replace application-level authentication and authorization.

## 6. Deployment Topologies and Tenancy

- **Silo (default):** one isolated VPS per customer; one default tenant; dedicated PostgreSQL, Redis, secrets, and backups.
- **Pooled (shared hosting):** many tenants on shared infrastructure; PostgreSQL row-level security enforced; namespaced Redis keys.
- **Bridged (optional, requires approval):** schema per tenant.

**Tenancy rules**

- Every tenant-owned table carries `tenant_id`, including on a single-tenant VPS.
- `tenant_id` derives only from authenticated identity and travels in an immutable `TenantContext`. Never trust a client-supplied `tenant_id` or `user_id`.
- Workers, retrievers, tools, and pack runtimes receive a `TenantContext` and fail closed without one.
- Every tenant-owned query enforces ownership. The application database role must not bypass row-level security.
- Moving from silo to pooled hosting is a configuration and migration step with its own migration plan, rollback strategy, test evidence, and approval.

## 7. Core Data Model

Versioned Alembic migrations for: `tenants`, `users`, `api_keys`, `workflows`, `tasks`, `task_attempts`, `outbox_events`, `webhook_events`, `usage_ledger`, `approvals`, `agent_runs`, `agent_steps`, `packs`, `pack_versions`, `pack_installations`, `memory_items`, `memory_embeddings`, `memory_audit`.

Include UUIDs, foreign keys, unique constraints, indexes, timestamps, retention rules, and JSON size limits. Never store or log plaintext API keys. Schema or retention changes require a migration plan, recovery strategy, test evidence, and approval before production execution.

## 8. Task Processing and Reliability

States: `queued`, `running`, `retrying`, `completed`, `failed`, `cancelled`.

**Submission flow:** authenticate and authorize; validate workflow and input size; enforce rate and cost limits; validate the idempotency key; create task and outbox event in one transaction; return the task ID with `202 Accepted`; publish to Redis Streams; Worker claims and executes; persist results and transitions; acknowledge only after durable processing or a recovery decision.

**Reliability requirements**

- Bounded exponential backoff with jitter, maximum attempts, and execution timeouts.
- Worker leases, pending-entry reclaim (`XAUTOCLAIM` or equivalent), and abandoned-task recovery.
- Dead-letter handling and a poison-message limit, with operator visibility.
- Idempotency keys are unique per tenant and retained for a defined window. Reuse of a key with a different payload hash returns `409 Conflict`.
- Clear distinction between transient and permanent errors. No retries for validation or authorization failures.
- Protection against retry storms and duplicate billable operations.
- Explicit cancellation semantics, including in-flight provider calls, with race-condition tests.
- Outbox and Redis recovery processes; safe handling of restarts and duplicate delivery.
- No secrets or sensitive payloads in logs.

## 9. API Contract

- `GET /health/live`, `GET /health/ready`
- `POST /v1/tasks` (requires `Idempotency-Key`; returns `202 Accepted`)
- `GET /v1/tasks`, `GET /v1/tasks/{task_id}`, `POST /v1/tasks/{task_id}/cancel`
- `GET /v1/workflows`
- `POST /v1/webhooks/{provider}`
- Pack and approval endpoints (import, activate, roll back, list, decide), with shapes approved in Phase 0.

Use FastAPI-generated OpenAPI documentation and consistent errors for authentication, authorization, validation, missing resources, conflicts, rate limits, and temporary failures.

Webhook handlers verify signatures, enforce timestamp tolerance, deduplicate event IDs through `webhook_events`, and prevent replay. Public API or webhook changes require compatibility analysis, documentation, contract tests, and approval.

## 10. Agentic Runtime and AI Safety

Implement an explicit `LLMProvider` interface. Provider configuration, model selection, limits, usage accounting, timeouts, and error handling live outside workflow logic.

Agents are bounded, not autonomous:

- Maximum steps, tokens, duration, and cost per run; per-user, per-tenant, and per-workflow limits; budgets reserved before the provider call.
- Tool allowlist declared by the installed pack and approved at activation.
- Human approval for sensitive or irreversible actions, recorded in `approvals`.
- Every run and step recorded in `agent_runs` and `agent_steps`, with provider, model, latency, and usage metadata.
- Validate model output against a schema. Treat external content and model output as untrusted, and defend against prompt injection.
- No arbitrary code, SQL, shell, or unauthorized tools.
- Handle timeouts, rate limits, malformed output, and outages. Minimize sensitive data retention and logging.
- Approval is required before adding providers, models, tools, or retention behavior.

The initial workflow is bounded (for example, event summarization) and ships as the reference pack.

## 11. Industry Packs

An Industry Pack is a versioned, declarative bundle that extends the core without modifying it.

**Contents**

- Manifest: name, version, compatible core range, declared permissions.
- Workflows with input and output schemas.
- Versioned prompts with evaluation fixtures.
- Tools and connectors, allowlisted with scoped credentials.
- Policies: approval rules, limits, retention.
- Mandatory regression and adversarial tests.

**Lifecycle:** import, validate, stage, approve, activate, roll back. Activation is per tenant and recorded as a `pack_installation`.

**Rules**

- Declarative only in the MVP; no executable code.
- Packs are signed, and the signature is verified on import.
- Upgrades present a permission diff for approval.
- The red-team suite runs on every import and upgrade.
- Packs cannot reach core or other-pack data without a declared, approved permission.
- Shared pack assets contain no tenant data.
- The core remains industry-neutral, with no industry logic in core modules.

## 12. Tenant Memory Isolation

Memory includes conversation context, long-term facts, summaries, embeddings, vector indexes, caches, queue payloads, and pack-level state. All of it is tenant-owned. Isolation is enforced below the model and never depends on a prompt, a model decision, or a client-supplied identifier.

**Controls**

- **Storage:** `memory_items` and `memory_embeddings` carry a mandatory `tenant_id`; row-level security applies in pooled mode.
- **Retrieval:** the tenant filter is part of the vector query and applied before ranking, never after a global top-k.
- **Caches and queues:** keys and streams are namespaced `t:{tenant_id}:`. No shared prompt or completion cache across tenants.
- **Packs:** pack memory is namespaced by tenant and pack installation.
- **Learning:** no cross-tenant learning, fine-tuning, or pooled content analytics. Provider terms must exclude training on customer data and bound retention.
- **Integrity:** memory is untrusted input. Each item records provenance, trust level, TTL, and size limit. Promotion to long-term memory is gated by policy or approval.
- **Lifecycle:** offboarding purges rows, vectors, caches, and queued payloads with a verified deletion report. Backup retention and export are defined per tenant. Per-tenant encryption keys are optional pending approval.
- **Observability:** logs carry tenant tags and never memory content.

**Release gate:** the canary test must pass. Tenant A plants a unique string, and Tenant B attempts retrieval by direct query, semantic similarity, and prompt injection. The gate also requires cache-collision, missing-`TenantContext`, RLS-bypass, pack-boundary, and purge-verification tests.

## 13. Security Requirements

- Hash API keys securely. Use least-privilege credentials, separated per environment and per VPS.
- Enforce authentication, authorization, tenant isolation, rate limits, and quotas.
- Validate inputs and limit request and response sizes.
- Verify webhook signatures and prevent replay.
- Protect against SQL injection, SSRF, unsafe deserialization, and path traversal.
- UI sessions: secure cookies, CSRF protection, session expiry.
- Keep secrets out of source control and logs. Use HTTPS everywhere. Restrict CORS, outbound access, and administrative endpoints.
- VPS hardening: host firewall, key-only SSH, automatic security updates, non-root containers, only the reverse proxy exposed.
- Pin and scan dependencies and container images.
- Encrypted off-host PostgreSQL backups with tested restoration.
- Document security exceptions with controls, expiry dates, and approvers.

## 14. Red-Team Development

For every significant feature or architecture change: identify threats; analyze attack paths and failure modes; run reproducible adversarial tests; remediate and add regression tests; record evidence and approval.

**Coverage:** authentication, authorization, tenant and memory isolation; malformed and oversized requests; webhook forgery, replay, and duplicates; rate-limit bypass; Redis, PostgreSQL, and Worker failures; duplicate messages, expired leases, retries, and recovery; prompt injection, unauthorized tools, malicious packs, malformed outputs, cost abuse, and data leakage; secret leakage, vulnerable dependencies, failed migrations, restore, rollback, and resource exhaustion.

Run only against authorized environments with synthetic or approved test data. Each finding records severity, evidence, impact, remediation, regression test, and verification status. Critical and high findings block production unless approved as exceptions.

## 15. Testing and Quality Gates

Required: unit and integration tests; API contract tests; queue and Worker tests; tenant-isolation and memory-isolation tests; pack validation tests; AI-provider mock tests; authorized real-provider smoke tests; resilience and recovery tests; security and dependency scans; end-to-end tests; deployment health checks.

Mocks are valid for isolated tests, not proof of real integrations. Use deterministic fixtures and synthetic data. Every phase defines entry criteria, approvals, acceptance criteria, evidence, exit criteria, residual risks, and rollback or recovery plans. Only actual recorded evidence may pass a gate.

## 16. Repository Structure

```
ai-automation/
├── app/
├── packs/              reference pack and pack tooling
├── migrations/
├── tests/
├── frontend/
├── docs/
├── scripts/
├── .github/
├── .env.example
├── .gitignore
├── Dockerfile
├── compose.yaml
├── pyproject.toml
├── README.md
├── AGENTS.md
└── MASTER_BUILD_SPEC.md
```

Keep modules focused and document material deviations.

## 17. GitHub and CI/CD

Workflows: code quality and type checks; unit and integration tests; dependency and secret scanning; security regression tests, including the isolation canary suite and pack validation; build validation; deployment verification.

Use pull requests, branch protection, required reviews, and protected production environments. Never expose production secrets to untrusted pull-request code. Deploy only from approved branches or releases, verify health checks, and maintain rollback procedures.

## 18. Deployment and Cost Controls

**Local:** Docker Compose for API, Worker, PostgreSQL, and Redis, with documented setup, migration, startup, shutdown, and test commands.

**VPS (default production):** Docker Compose with API, Worker, PostgreSQL, and Redis behind a TLS reverse proxy; secrets via environment or restricted secret files; health checks and monitoring; encrypted off-host backups with tested restores; a documented per-instance update and rollback procedure.

**Production deployment requires:** approved design and release plan; successful staging verification; migration and rollback plan; backup or recovery confirmation; security and dependency checks; cost and quota configuration; named approver; recorded deployment evidence.

**Cost controls:** limit input size, tokens, duration, retries, concurrency, and per-user and per-tenant usage. Record usage and estimated cost in `usage_ledger`. Alert on abnormal usage. Avoid unbounded polling and retries. Budget approval is required for real-provider tests or quota increases. Billing alerts are not hard spending caps.

## 19. Phased Execution

**Phase 0: Assessment and Design.** Inspect the repository, document architecture and threats, confirm scope, close open decisions, record assumptions. *Gate:* approved architecture, decisions, assumptions, and development plan.

**Phase 1: Foundation.** Configuration, logging, FastAPI, PostgreSQL with pgvector, migrations, tenant-aware models, `TenantContext`, health checks, Docker Compose, CI, authentication foundations (API keys and UI sessions), core interfaces. *Gate:* application starts; approvals, migrations, health checks, and CI pass.

**Phase 2: Reliable Execution.** Outbox, Redis Streams, Worker, workflow engine, idempotency, retries, leases, dead-letter handling, acknowledgements, recovery, failure tests. *Gate:* tasks survive restarts and tested infrastructure failures without losing durable records.

**Phase 2.5: Pack Foundation.** Pack loader, registry, validation, signature verification, lifecycle, tenant memory layer, and a reference pack that proves the core and pack boundary. *Gate:* the reference pack installs, activates, and rolls back; the isolation canary suite passes.

**Phase 3: AI Workflow and API.** Reference-pack workflow, task APIs, agent runtime limits, output validation, usage accounting, error handling, budget enforcement, approvals. *Gate:* an authenticated request completes an approved workflow end to end in a non-production environment.

**Phase 4: UI.** Mobile-first interface for authentication, submission, status, results, approvals, errors, loading, empty, retry, and failure states. *Gate:* users complete the primary workflow without direct API calls.

**Phase 5: Hardening.** Security, adversarial, resilience, backup, rollback, isolation, and cost-control tests; fix critical and high findings; approve residual risks. *Gate:* release evidence is complete and risks have owners and expiry dates.

**Phase 6: Deployment and Handover.** Deploy to the approved VPS, configure operations, run smoke tests, verify recovery and rollback, document limitations, obtain production approval. *Gate:* the MVP is accessible, verified, documented, recoverable, and approved.

## 20. Definition of Done

The MVP is complete when:

- Setup is reproducible, and the application runs locally and on an isolated VPS with Docker Compose.
- Migrations, backups, and recovery are verified.
- Redis processing and outbox recovery are tested.
- The reference pack workflow works end to end.
- Authentication, tenant isolation, and memory isolation are tested.
- The responsive UI works on mobile and desktop.
- CI passes in GitHub.
- Security and resilience results are documented.
- Secrets, quotas, logging, backups, and rollback are documented.
- Limitations and residual risks are disclosed.
- Material decisions carry recorded approval, and no tests or integrations are falsely reported.
- The project owner approves release.

**Final rule:** build a secure, reliable, minimal production-capable MVP first. Add complexity only when justified by evidence, risk, workload, or explicit product requirements. When a consequential decision is unclear, stop, explain the trade-offs, ask focused questions, and obtain approval before proceeding.
