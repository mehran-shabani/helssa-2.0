# Changelog

## v2.3.0 - 2025-10-04
- chore: reset release baseline to start from v2.3.0 and increment patch versions by 0.01

## v2.0.0 - 2024-01-01
- Bootstrap baseline
## v2.1.0 - 2025-10-04
### feat
- feat(chatbot): add consent-aware smart storage
- feat: add multimodal chatbot endpoint
- feat: enforce coverage and add diagnostics writer
- feat(apps): add doctor_online, certificate, sub, down, chatbot (read-only APIs)
- feat: add dev bootstrap helpers
- feat: add database perf tooling
- feat: harden bitpay webhook flows
- feat(api): add system and analytics endpoints

### fix
- fix: handle changelog without tags

### chore
- chore: add log capture utility
- chore(deps): bump actions/checkout from 4 to 5
- chore(deps): bump actions/setup-python from 5 to 6
- chore: bootstrap helssa backend

### docs
- docs: refresh repository structure report

### other
- Merge pull request #25 from mehran-shabani/codex/add-smart-storage-to-chatbot-app
- Update release.yml
- Update release.yml
- Merge pull request #24 from mehran-shabani/codex/implement-multimodal-chatbot-api
- Merge pull request #21 from mehran-shabani/codex/tighten-quality-gates-and-add-diagnostic-writer
- Merge pull request #19 from mehran-shabani/codex/review-and-update-repo_structure.md
- Merge pull request #17 from mehran-shabani/codex/cleanup-repo-and-scaffold-new-apps
- Update tests/domains/test_doctor_online_api.py
- Update tests/domains/test_certificate_api.py
- Update tests/domains/test_doctor_online_api.py
- Update sub/api.py
- Merge pull request #18 from mehran-shabani/coderabbitai/docstrings/10913f9
- 📝 Add docstrings to `codex/cleanup-repo-and-scaffold-new-apps`
- Merge pull request #16 from mehran-shabani/codex/generate-comprehensive-repository-structure-report
- Add repository structure reporting script
- Merge pull request #15 from mehran-shabani/codex/add-generic-log-capture-utility
- Merge pull request #14 from mehran-shabani/codex/stabilize-helssa-dev-environment
- Update apps/ops/management/commands/bootstrap_dev.py
- Merge pull request #13 from mehran-shabani/codex/add-diagnostic-probe-to-helssa-backend
- Add diagnostic management command
- Merge pull request #11 from mehran-shabani/codex/add-database-indexes-and-performance-reporting
- Remove ruff and isort from CI config
- Refactor: Move Django Error import and fix migration
- Auto-commit pending changes before rebase - PR synchronize
- Update perf/metrics.py
- Update telemedicine/migrations/0002_transaction_indexes.py
- Refactor: Add missing import for models
- Refactor: Improve import statements and add transaction indexes
- Update README.md
- Refactor perf slowlog command and fix telemedicine migration
- Update perf/management/commands/perf_slowlog.py
- Update config/urls.py
- Update perf/management/commands/perf_slowlog.py
- Update tests/test_perf.py
- Merge pull request #9 from mehran-shabani/codex/harden-bitpay-webhook-with-idempotency-and-security
- Update telemedicine/gateway/signature.py
- Update telemedicine/views.py
- Update telemedicine/gateway/signature.py
- Update config/settings/base.py
- Fix signature verification and improve error handling
- Merge pull request #4 from mehran-shabani/codex/add-phase-2-read-only-apis-for-helssa
- Merge pull request #8 from mehran-shabani/revert-7-coderabbitai/docstrings/63b52bd
- Revert "📝 Add docstrings to `codex/add-phase-2-read-only-apis-for-helssa`"
- Merge pull request #7 from mehran-shabani/coderabbitai/docstrings/63b52bd
- 📝 Add docstrings to `codex/add-phase-2-read-only-apis-for-helssa`
- Refactor: Improve system health and analytics endpoints
- Update analytics/api.py
- Merge pull request #6 from mehran-shabani/coderabbitai/docstrings/249f0f9
- 📝 Add docstrings to `codex/add-phase-2-read-only-apis-for-helssa`
- Merge pull request #5 from mehran-shabani/coderabbitai/docstrings/7854093
- 📝 Add docstrings to `codex/add-phase-2-read-only-apis-for-helssa`
- Merge pull request #3 from mehran-shabani/dependabot/github_actions/actions/checkout-5
- Merge pull request #2 from mehran-shabani/dependabot/github_actions/actions/setup-python-6
- Merge pull request #1 from mehran-shabani/codex/bootstrap-django-project-with-ci-and-release
- Update README.md
- Initial commit

## v2.2.0 - 2025-10-04
### feat
- feat(chatbot): add consent-aware smart storage
- feat: add multimodal chatbot endpoint
- feat: enforce coverage and add diagnostics writer

### fix
- fix: handle changelog without tags

### other
- Merge pull request #26 from mehran-shabani/codex/fix-git-error-in-changelog-script
- [skip ci] chore(release): v2.1.0
- Merge pull request #25 from mehran-shabani/codex/add-smart-storage-to-chatbot-app
- Update release.yml
- Update release.yml
- Merge pull request #24 from mehran-shabani/codex/implement-multimodal-chatbot-api
- Merge pull request #21 from mehran-shabani/codex/tighten-quality-gates-and-add-diagnostic-writer

