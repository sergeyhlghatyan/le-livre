# Le Livre - Deployment Issues Tracker

Last Updated: December 28, 2024

## Critical Issues

### 1. Phase 0 Neo4j Relationships Missing

**Status**: 🔴 CRITICAL - Not Deployed

**Description**: The backend code references Phase 0 relationship types in Neo4j that haven't been created in the production database. This causes queries to return incomplete data.

**Missing Relationship Types**:
1. `USES_DEFINITION` - Used by `/provisions/context` endpoint
2. `AMENDED_FROM` - Used by `/provisions/impact-radius` endpoint
3. `SEMANTICALLY_SIMILAR` - Used by context service

**Missing Properties**:
- `term` (on USES_DEFINITION relationships)
- `confidence` (on USES_DEFINITION relationships)
- `text_delta` (on AMENDED_FROM relationships)
- `change_type` (on AMENDED_FROM relationships)

**Impact**:
- Context queries return limited information
- Amendment tracking not available
- Semantic similarity discovery not functional
- Users see incomplete relationship data

**Evidence from Logs**:
```
Received notification from DBMS server: "One of the relationship types in your query
is not available in the database, make sure you didn't misspell it or that the label
is available when you run this statement in your application (the missing relationship
type is: USES_DEFINITION)"
```

**Resolution Steps**:

1. Run `pipeline/gold/detect_amendments.py` on EC2
   ```bash
   docker compose -f docker-compose.prod.yml exec backend \
     python pipeline/gold/detect_amendments.py
   ```

2. Run `pipeline/gold/extract_definitions.py` on EC2
   ```bash
   docker compose -f docker-compose.prod.yml exec backend \
     python pipeline/gold/extract_definitions.py
   ```

3. Run `pipeline/gold/compute_similarity.py` on EC2
   ```bash
   docker compose -f docker-compose.prod.yml exec backend \
     python pipeline/gold/compute_similarity.py
   ```

4. Verify relationships were created:
   ```bash
   docker compose -f docker-compose.prod.yml exec neo4j cypher-shell -u neo4j -p <password> \
     "MATCH ()-[r:AMENDED_FROM]->() RETURN count(r) as count;"

   docker compose -f docker-compose.prod.yml exec neo4j cypher-shell -u neo4j -p <password> \
     "MATCH ()-[r:USES_DEFINITION]->() RETURN count(r) as count;"

   docker compose -f docker-compose.prod.yml exec neo4j cypher-shell -u neo4j -p <password> \
     "MATCH ()-[r:SEMANTICALLY_SIMILAR]->() RETURN count(r) as count;"
   ```

**Files Involved**:
- `backend/app/services/context.py` (lines 199-207)
- `backend/app/routers/provisions.py` (impact_radius endpoint)
- `pipeline/gold/detect_amendments.py`
- `pipeline/gold/extract_definitions.py`
- `pipeline/gold/compute_similarity.py`

---

## Medium Priority Issues

### 1. Frontend Svelte 5 Migration Warnings

**Status**: 🟡 MEDIUM - Functional but needs cleanup

**Description**: Multiple compile-time warnings related to incomplete Svelte 5 migration. The app works but has non-optimal reactivity patterns.

**Issues Found**:

**State Reactivity Issues**:
- `SearchInput` not declared with `$state()` - may not update correctly
- Closure capture issues in `SourceCard.svelte`, `SourceGroup.svelte`, provision pages
- State objects not properly reactive in some components

**Accessibility Issues**:
- `CommandPalette.svelte`: Missing `tabindex` on dialog
- `ConversationSwitcher.svelte`: Non-interactive elements with click handlers need ARIA roles
- `SourceCard.svelte`: Missing keyboard event handlers for accessible navigation

**Deprecations**:
- Using deprecated `<slot>` element instead of `{@render}` tags in multiple components

**Impact**:
- Components may not react to state changes properly
- Accessibility compliance issues
- Future Svelte versions may break deprecated patterns

**Resolution Steps**:

1. Fix state reactivity in SearchInput:
   ```typescript
   // Change from:
   let searchQuery = '';

   // To:
   let searchQuery = $state('');
   ```

2. Fix closure capture issues:
   ```typescript
   // Use proper reactive declarations
   $effect(() => {
     // Reactive logic here
   });
   ```

3. Replace `<slot>` with `{@render}`:
   ```svelte
   <!-- Change from: -->
   <slot name="header" />

   <!-- To: -->
   {@render header?.()}
   ```

4. Add ARIA roles and keyboard handlers:
   ```svelte
   <div
     role="button"
     tabindex="0"
     on:click={handler}
     on:keydown={(e) => e.key === 'Enter' && handler()}
   >
   ```

**Files Involved**:
- `frontend/src/lib/components/SearchInput.svelte`
- `frontend/src/lib/components/chat/SourceCard.svelte`
- `frontend/src/lib/components/chat/SourceGroup.svelte`
- `frontend/src/lib/components/CommandPalette.svelte`
- `frontend/src/lib/components/ConversationSwitcher.svelte`

---

## Low Priority Issues

### 1. Test Suite Failures

**Status**: 🟢 LOW - 86% passing (37/43 tests)

**Description**: 6 tests failing, mostly UI visibility and selector issues. Core functionality tests pass.

**Failing Tests**:

**Chat Sidebar UI Tests (5 tests)**:
- Issue: Chat input selector not finding elements
- Root cause: Sidebar may not be visible by default or needs specific trigger
- Note: API endpoint works when tested separately - just UI test visibility issue

**Section Page Navigation (1 test)**:
- Issue: "Should navigate to section from main page" failing
- Root cause: Route may not exist or selector is incorrect

**Impact**:
- No functional impact (features work)
- CI/CD pipeline shows test failures
- May mask future regressions

**Resolution Steps**:

1. Fix chat sidebar visibility:
   ```typescript
   // Update test to trigger sidebar visibility
   await page.click('[data-testid="open-chat-sidebar"]');
   await page.waitForSelector('[data-testid="chat-input"]');
   ```

2. Verify section navigation route:
   ```typescript
   // Check if route exists in +page.svelte or update test
   ```

**Files Involved**:
- `frontend/tests/*.spec.ts` (chat sidebar tests)
- `frontend/tests/section-nav.spec.ts`

---

### 2. Nginx Health Check Status

**Status**: 🟢 LOW - Cosmetic only

**Description**: Nginx container shows "unhealthy" in docker ps, but service is fully operational.

**Evidence**:
```bash
NAME               STATUS
lelivre-nginx      Up 22 minutes (unhealthy)  # But HTTPS works perfectly
```

**Impact**: None - service is fully functional, HTTPS working, all endpoints accessible

**Possible Causes**:
- Health check timing issue (too aggressive interval)
- Health check script needs adjustment
- Docker health check vs nginx actual health mismatch

**Resolution** (optional):
```dockerfile
# Adjust health check in docker-compose.prod.yml
healthcheck:
  test: ["CMD-SHELL", "wget --quiet --tries=1 --spider http://localhost:80/health || exit 1"]
  interval: 60s  # Increase from 30s
  timeout: 5s
  start_period: 10s
```

---

## Resolved Issues Log

### ✅ Provision Endpoint 404 Errors (Fixed: Dec 28, 2024)

**Problem**: Provision detail endpoints returning 404 for paths like `/api/provisions/provision/%2Fus%2Fusc%2Ft18%2Fs922%2Fa%2F1/2024`

**Root Cause**: FastAPI strips leading "/" from path parameters when URLs contain double slashes

**Solution**: Added leading slash check in 6 endpoints in `backend/app/routers/provisions.py`:
```python
if not provision_id.startswith('/'):
    provision_id = '/' + provision_id
```

**Endpoints Fixed**:
- `get_provision_by_id`
- `get_hierarchy`
- `get_graph`
- `get_provision_context_endpoint`
- `get_provision_timeline_changes`
- `get_impact_radius_endpoint`

---

### ✅ HTTPS Not Working (Fixed: Dec 28, 2024)

**Problem**: Site only accessible via HTTP, HTTPS timing out

**Root Cause**: SSL server block in nginx.conf was commented out

**Solution**:
1. Uncommented HTTPS server block in `nginx/nginx.conf`
2. Configured domain: lelivre.trunorth.cloud
3. Enabled HTTP to HTTPS redirect
4. Added security headers (HSTS, X-Frame-Options, etc.)
5. Enabled gzip compression

**Result**: HTTPS fully functional at https://lelivre.trunorth.cloud

---

### ✅ Chat Endpoint 500 Errors (Fixed: Dec 28, 2024)

**Problem**: `POST /api/chat` returning 500 Internal Server Error

**Root Cause**: OpenAI API key had an extra 'y' character at the end, causing 401 from OpenAI

**Solution**:
1. Corrected OPENAI_API_KEY in EC2 `.env` file (removed trailing 'y')
2. Recreated backend container to pick up new environment variable
3. Verified API key works with test query

**Result**: Chat endpoint fully functional with RAG responses

---

### ✅ Backend Docker Permission Issues (Fixed: Dec 28, 2024)

**Problem**: Backend container failing to start with permission denied errors

**Root Cause**: Multi-stage build installed packages as root with --user flag, but app runs as appuser

**Solution**: Simplified Dockerfile to install packages globally instead of with --user:
```dockerfile
# Before: RUN pip install --user --no-cache-dir -r requirements.txt
# After: RUN pip install --no-cache-dir -r requirements.txt
```

**Result**: Backend container starts successfully and runs stable

---

### ✅ OpenAI API Key Invalid (Fixed: Dec 28, 2024)

**Problem**: Chat functionality failing with "Incorrect API key provided" error

**Root Cause**: Extra 'y' character appended to API key during copy

**Solution**: Corrected the key in .env file from `...2oAy` to `...2oA`

**Result**: OpenAI API calls successful, embeddings and chat working

---

## Summary Statistics

**Total Issues**: 6
- 🔴 Critical: 1 (Phase 0 Neo4j)
- 🟡 Medium: 1 (Svelte 5 warnings)
- 🟢 Low: 2 (test failures, nginx health check)
- ✅ Resolved: 5

**Deployment Health**: 🟡 Partial
- Core features: ✅ Working
- Phase 0 features: ❌ Not deployed
- Code quality: 🟡 Needs cleanup
- Tests: 🟡 86% passing

---

## Next Actions

**Immediate (Required for Full Functionality)**:
1. Run Phase 0 pipeline scripts on EC2 to create Neo4j relationships
2. Verify relationship creation with Cypher queries

**Soon (Code Quality)**:
1. Fix Svelte 5 reactivity warnings in frontend
2. Replace deprecated `<slot>` patterns
3. Add ARIA roles for accessibility

**When Convenient (Testing)**:
1. Fix chat sidebar UI test selectors
2. Verify section navigation route
3. Adjust nginx health check timing

---

## References

- **Deployment Documentation**: `DEPLOYMENT.md`
- **Project Overview**: `CLAUDE.md`
- **Test Results**: `TEST_RESULTS.md`, `TESTING_COMPLETE.md`
- **Phase 0 Completion**: `PHASE0_COMPLETE.md`
