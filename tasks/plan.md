# Implementation Plan: Production Hardening

## Overview

Address the repository-wide review findings in risk order while keeping each
slice deployable. Authentication becomes purpose-aware and revocable, public
collections remain bounded, query and concurrency defects are fixed, and the
deployment pipeline verifies the same database engine used in production.

## Architecture Decisions

- Keep the existing authentication route names, but make password reset use a
  short-lived, single-purpose reset credential instead of a normal login token.
- Put OTP generation, hashing, purpose, expiry, and delivery behind one
  authentication-owned module. Delivery is configurable so production is not
  coupled to a specific SMS vendor.
- Use a database-backed Django cache for DRF throttling so limits are shared by
  all Gunicorn workers without adding Redis to this small deployment.
- Keep list pagination mandatory for public endpoints. Any future bulk export
  should be an explicit authenticated interface.
- Preserve the response envelope and translated catalog field behavior.

## Task List

### Phase 1: Authentication Security

- Task 1: Add token-version invalidation and safe JWT lifetimes.
- Task 2: Add purpose-aware hashed OTP issuance and a delivery adapter seam.
- Task 3: Replace reset login tokens with short-lived reset credentials.
- Task 4: Add shared-store throttling and non-enumerating auth responses.

### Checkpoint: Authentication

- Focused authentication tests pass.
- Existing access and refresh behavior is covered by regression tests.
- Production settings reject an unconfigured OTP delivery backend.

### Phase 2: API And Data Correctness

- Task 5: Remove the public pagination bypass and eliminate product N+1 queries.
- Task 6: Handle concurrent duplicate reviews as a conflict and minimize public
  reviewer identity exposure.
- Task 7: Ensure the default media asset is initialized in local and deployed
  workflows.

### Checkpoint: API

- Store tests pass.
- Query counts and collection bounds have regression coverage.
- Public review responses contain no user identity fields.

### Phase 3: Operations And Documentation

- Task 8: Harden staging/production settings and refresh Arabic translations.
- Task 9: Add PostgreSQL, migration, production-check, and dependency-audit CI
  gates.
- Task 10: Gate deployment on verification and refuse dirty remote checkouts.
- Task 11: Align documentation with the secured contracts and actual Docker
  behavior.

### Checkpoint: Complete

- Full tests, formatting, Django checks, migration checks, dependency checks,
  Compose validation, and container integration tests pass.
- Changes are split into focused commits and the worktree is clean.

## Risks And Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Existing clients expect reset verification to log in | High | Keep route names, document the new reset token payload, and add contract tests |
| No SMS vendor is selected | High | Provide a narrow adapter seam, safe test backend, and fail-fast deployed configuration |
| Database-backed throttling adds writes | Medium | Limit it to authentication endpoints and keep rates configurable |
| JWT versioning invalidates sessions after password changes | Intended | Document it as a security behavior and test both old and new tokens |
| PostgreSQL CI is slower than SQLite | Low | Use one production-parity test job rather than a full matrix |

## Deployment Integration Note

- OTP delivery uses the included HTTPS webhook adapter. Each deployed GitHub
  environment must provide its provider URL and bearer token before deployment.
