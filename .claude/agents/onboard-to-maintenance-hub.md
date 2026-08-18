---
name: onboard-to-maintenance-hub
description: Work out everything the dev-maintenance hub needs to monitor THIS repository — deployed URLs, a health endpoint, the stack, whether it handles health data — verify the URLs actually respond, and emit the exact repos.json entry to hand back. Use when asked to "onboard this repo to the maintenance hub", "onboard to dev-maintenance", "get this repo monitored", or "generate the maintenance hub config".
tools: Bash, Read, Glob, Grep
---

# Onboard this repository to the dev-maintenance hub

The hub (`bwill619/dev-maintenance`) monitors projects from the outside: it
probes URLs and reads the repo over the GitHub API. It needs **no workflow and
no code in this repository** — only facts about it.

Your job is to find those facts, prove the URLs work, and print a config entry
that can be pasted straight into the hub's `repos.json`.

**Never invent a URL.** A guessed endpoint produces a monitor that alerts
forever on something that was never real. If you cannot find something, say so
and ask.

## 1. Identify the repo

```bash
git remote get-url origin
```

The `owner/name` slug is what the hub files issues against. The project's `name`
in the config is the repo name unless the user prefers something else.

## 2. Find the deployed URLs

Look, in this order, and stop when you have a confident answer:

| Where | What it gives |
| --- | --- |
| `render.yaml` | Render services and their names — the URL is usually `https://<name>.onrender.com` |
| `vercel.json`, `.vercel/project.json` | Vercel project |
| `netlify.toml` | Netlify site |
| `fly.toml` | Fly app — `https://<app>.fly.dev` |
| `.env.example`, `.env.sample`, `.env.template` | `API_URL`, `VITE_API_URL`, `NEXT_PUBLIC_API_URL`, `REACT_APP_API_URL`, `BASE_URL` |
| Backend CORS config | The allowed origins *are* the frontend URLs |
| `package.json` → `homepage` | Frontend URL |
| `README.md` | Links and badges to the live site |

```bash
grep -rInE "(https?://[a-z0-9.-]+\.(com|io|dev|app|net|org|onrender\.com|vercel\.app|netlify\.app|fly\.dev))" \
  --include="*.md" --include="*.json" --include="*.yaml" --include="*.yml" \
  --include=".env*" --include="*.ts" --include="*.js" . \
  | grep -viE "(node_modules|schema|w3\.org|json-schema|example\.com|localhost)" | head -40
```

A repo usually has two: the API and the site. Name them `backend_url` and
`frontend_url`. If there is only one, use `url`.

**Never take a URL from a real `.env`** — those are gitignored for a reason, and
anything in one is a secret. Only `.env.example` and its siblings.

## 3. Find the health endpoint

The hub wants something cheap that returns **200** when the service is up.

```bash
grep -rInE "['\"]/(health|healthz|_health|ping|status|readyz)['\"]" \
  --include="*.ts" --include="*.js" --include="*.py" --include="*.rb" --include="*.go" . \
  | grep -v node_modules | head -20
```

If there is no health route, the site root or an unauthenticated `GET` endpoint
is acceptable — say which you picked and why. Do **not** pick an endpoint that
requires auth, and do not pick one that writes.

## 4. Pick performance endpoints

Two or three that represent real work: the health route, a login (with
deliberately invalid credentials — the hub measures how fast it *rejects*), and
one read-heavy route.

Every endpoint must be safe to call every six hours forever. **Nothing that
writes, sends email, charges anything or mutates state.** A login with invalid
credentials is safe; a signup is not.

## 5. Decide whether the PHI audit applies

It flags source lines where a health-data identifier reaches a log, analytics
call, browser storage, cookie or query string.

```bash
grep -rInE "(patient|diagnosis|prescription|medical|hipaa|phi|insurance|mrn)" \
  --include="*.ts" --include="*.js" --include="*.tsx" . | grep -v node_modules | head -20
```

- **Handles health data** → include `phi-audit`.
- **Handles other sensitive personal data** (athlete records, financial, minors)
  → still include it, and propose a `phiTerms` list matching this domain's own
  identifiers rather than the medical defaults.
- **Neither** → say so and leave it out; a check that can only produce false
  positives trains people to ignore the tool.

## 6. Verify before reporting

Do not hand over a URL you have not seen respond.

```bash
for url in <each url you found>; do
  echo "== $url"
  curl -s -o /dev/null -w "  status=%{http_code} time=%{time_total}s\n" --max-time 70 "$url"
done
```

Interpret honestly:

- **200 quickly** — good, use the defaults.
- **First call slow (>10s), second fast** — the host spins down when idle. Say
  so, and set `timeoutMs: 60000`, `retries: 3`, `retryDelayMs: 5000`, or the hub
  will report it down every run while it is merely waking.
- **401/403** — the endpoint needs auth. Find a different one, or add the
  observed status to `expectStatus` if that response genuinely proves it is up.
- **Never responds** — report that. Do not put it in the config.

## 7. Output

Print exactly this, filled in, and nothing invented. If you have a local
checkout of the hub repo (`bwill619/dev-maintenance`) handy, pipe it straight
in instead of asking the user to paste it: `... | node src/index.js add`
merges it into `repos.json` by `repo` slug — creating the entry if it's new,
or adding these checks to an existing one (from `discover --add`, say)
without disturbing its `enabled` state or other checks. Once run, delete this
file from this repo — it isn't part of this project's own tooling.

```json
{
  "name": "<repo name>",
  "repo": "<owner/name>",
  "enabled": false,
  "checks": {
    "uptime": {
      "backend_url": "<verified api url>",
      "frontend_url": "<verified site url>"
    },
    "performance": {
      "baseUrl": "<api base>",
      "endpoints": [
        { "name": "health", "path": "/health" }
      ]
    },
    "phi-audit": {},
    "deps": { "failOn": "high" }
  }
}
```

Then a short report:

- **Stack** — what this is, and where the manifests live (`/`, `/backend`, `/frontend`).
- **URLs** — each one with the status and response time you measured.
- **Spin-down** — yes or no, and the timeouts you set because of it.
- **Health endpoint** — which, and why that one.
- **PHI audit** — included or not, and why.
- **Left out** — anything you could not find, stated plainly rather than guessed.
- **Still needs a human**: install the maintenance app on this repo, and turn on
  Dependabot alerts under **Settings → Code security** (no API exists for that
  toggle).

Omit any check you have no verified input for. A missing check is a gap someone
can close later; a wrong one is an alarm that cries wolf until it is switched
off.
