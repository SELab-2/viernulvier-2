---
name: 'Epic: Domain Implementation'
about: Use this issue to monitor the architecture and view the progress of the sub-tasks
  for the backend domains.
title: "[DOMAIN_NAME] Domain Implementation (Epic)"
labels: backend
assignees: ''

---

## Overview
This issue tracks the complete implementation of the **[DOMAIN_NAME]** domain.

## Sub-Issues
- [ ] Data Layer: Models, Constraints & Model Tests (#)
- [ ] Admin Layer: CMS Configuration & Manual Validation (#)
- [ ] API Layer: Serializers, ViewSets & Integration Tests (#)

## Definition of Done
- [ ] All models use `db_table = "lowercase_name"`
- [ ] Admin is user-friendly with working Inlines
- [ ] API is optimized (no N+1) and documented in OpenAPI
- [ ] Automated tests (Pytest) passing for both Models and API
- [ ] Code reviewed and merged
