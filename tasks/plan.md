# Implementation Plan: Brand And Branch Catalog

## Overview

Introduce the approved `Brand → Branch → Category → Product` ownership chain
without losing existing catalog records. Deliver the model, API, search, seed,
and documentation changes in independently verified slices.

## Architecture Decisions

- Product stores only `category`; branch and brand are derived relationships.
- Brand and Branch use translated titles and the existing default-image
  behavior.
- Brand-to-Branch and Branch-to-Category deletion uses `PROTECT`.
- Existing categories are assigned to a migration-created `Wasla → Main
  Branch` hierarchy before the branch field becomes required.
- Category parent and child nodes must remain within one branch.
- New endpoints follow existing public-read/admin-write conventions.

## Build Order

1. Domain schema and backward-compatible data migration.
2. CRUD serializers, endpoints, permissions, and deletion semantics.
3. Ownership filters and multilingual search integration.
4. Admin, seed data, localization, and documentation.
5. Full SQLite and PostgreSQL verification and final review.

## Risks And Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Existing categories become orphaned | High | Data migration assigns all rows before enforcing non-null |
| Cross-branch category tree | High | Validate parent and existing children at model/API boundaries |
| Brand deletion erases products | High | Protect populated brands and branches and return HTTP 409 |
| Existing product clients break | Medium | Keep Product fields and category relationship; add nested ownership only |
| Search results become ambiguous | Low | Add explicit `brand` and `branch` discriminator values |

## Verification Checkpoints

- Schema tests and migration checks pass before API work.
- CRUD and permissions tests pass before filters/search.
- Store and seed suites pass before documentation commit.
- Full local and Docker suites pass before handoff.
