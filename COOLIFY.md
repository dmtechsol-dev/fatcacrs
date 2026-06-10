# Coolify Deployment

This repository is a single deployable application:

- React/Vite is compiled during the Docker build.
- FastAPI serves the compiled frontend at `/`.
- API endpoints remain under `/api`.
- Uvicorn listens on container port `8000`.

## Required Coolify Settings

| Setting | Value |
| --- | --- |
| Build pack | `Dockerfile` |
| Dockerfile location | `/Dockerfile` |
| Base directory | `/` |
| Start command | Leave empty; use the Dockerfile `CMD` |
| Optional start override | `uvicorn backend.main:app --host 0.0.0.0 --port 8000 --proxy-headers` |
| Container/exposed port | `8000` |
| Health check path | `/health` |
| Health check port | `8000` |
| Publish directory | Leave empty |

Do not use `main:app`. The ASGI application is defined in
`backend/main.py`, so its import path is `backend.main:app`.

The optional start override contains no shell metacharacters. Do not append
`&`, `|`, `;`, `$`, backticks, redirects, parentheses, or multiline commands.

## Domain Routing

Route the public domain to this one application on port `8000`. A separate
frontend Coolify service is not required:

- `/` serves the Vite application.
- `/health` is the deployment health check.
- `/docs` serves FastAPI API documentation.
- `/api/health` is the API health endpoint.
- `/api/upload-excel`, `/api/validate`, `/api/generate-xml`, and
  `/api/download/{fileId}` are the application API.

The frontend uses same-origin `/api` URLs by default. Do not set
`VITE_API_BASE_URL` for this single-service deployment.

No FastAPI `root_path` is required when the domain points to the application
root. If Coolify is configured with a path prefix, remove that prefix and use a
dedicated domain or subdomain. This avoids proxy path stripping or duplicated
`/api` prefixes.

## Expected Checks

After deployment:

```text
GET /          -> 200 text/html
GET /health    -> 200 application/json
GET /docs      -> 200 text/html
GET /api/health -> 200 application/json
```

If `/` still returns `{"detail":"Not Found"}`, confirm that Coolify rebuilt the
latest commit using the root Dockerfile and that the domain targets port
`8000`, not an older backend-only resource.
