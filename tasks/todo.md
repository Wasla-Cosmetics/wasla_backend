# Brand And Branch Catalog Tasks

- [ ] Add Brand and Branch models and migrate existing categories safely.
  - Acceptance: every category has a branch and existing products remain valid.
  - Verify: focused model tests and migration checks.
- [ ] Add CRUD APIs and nested hierarchy serialization.
  - Acceptance: public reads, admin writes, translated lists, and protected
    deletion follow existing API conventions.
  - Verify: focused API tests.
- [ ] Add ownership filters and multilingual global search.
  - Acceptance: brand, branch, category, and product filters work across
    languages; brand and branch appear in search.
  - Verify: focused filter and search tests.
- [ ] Update admin, seed data, translations, and documentation.
  - Acceptance: seed command creates the complete hierarchy and docs match the
    API.
  - Verify: seed and Arabic catalog tests.
- [ ] Complete final quality and production-parity verification.
  - Acceptance: clean worktree with all checks green.
  - Verify: Black, Django checks, migrations, full SQLite tests, Docker tests.
