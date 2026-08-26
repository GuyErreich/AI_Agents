# Lens — Backend / Data / Auth

Activate when Supabase, SQL, migrations, edge functions, RLS, auth, API routes, or secrets/env change. Load `project/platform/supabase` and `code/quality/security` when present.

## Hunt list

### Auth & tenancy
- RLS enabled and policies actually match the access model (no “open to anon” accidents)
- User/tenant id taken from auth context, never trusted from client body alone
- Privilege checks on every new RPC / edge path

### Data & migrations
- Migration forward-only, idempotent where required; destructive changes called out
- Defaults/nullability match app assumptions
- Indexes for new filter/join patterns; N+1 via chatty client loops

### API / edge
- Input validation at the boundary; size limits; method checks
- Secrets only in server/edge scope — never `VITE_`/public prefix
- Error responses do not leak internals; CORS/origins intentional

### Consistency
- Generated types / client queries updated with schema
- Branch vs production assumptions (local origins, service role misuse)

Escalate auth/RLS/migration findings — do not auto-fix casually in the loop.
