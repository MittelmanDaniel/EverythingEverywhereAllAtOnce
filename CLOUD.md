# Browser Use Cloud SDK

Both APIs are in the same package (`browser-use-sdk`):
- **BU Agent API (v3 Experimental)** — `browser-use-sdk/v3`
- **Browser Use Cloud v2** — `browser-use-sdk`

## Install
- Python: `pip install browser-use-sdk`
- TypeScript: `npm install browser-use-sdk`

## Setup
Set `BROWSER_USE_API_KEY` env var, or pass `api_key`/`apiKey` to the constructor.
Get a key at https://cloud.browser-use.com/settings?tab=api-keys

---

# BU Agent API (v3 Experimental)

## Python SDK (v3)

```python
from browser_use_sdk.v3 import AsyncBrowserUse, FileUploadItem
from pydantic import BaseModel

client = AsyncBrowserUse()

# Run a task (await for result)
result = await client.run("Find the top HN post")  # -> SessionResult[str]
print(result.output)   # str
print(result.id)       # session UUID
print(result.status)   # BuAgentSessionStatus (e.g. idle, stopped)

# Structured output
class Product(BaseModel):
    name: str
    price: float

result = await client.run("Get product info from amazon.com/dp/...", output_schema=Product)
print(result.output)  # Product(name=..., price=...)
```

### Constructor
```python
# Async client (recommended)
client = AsyncBrowserUse(api_key="...", base_url="...", timeout=30.0)

# Sync client (blocking, no async/await needed)
from browser_use_sdk.v3 import BrowserUse
client = BrowserUse(api_key="...", base_url="...", timeout=30.0)

# Context manager (sync only)
with BrowserUse() as client:
    result = client.run("Find the top HN post")
```
- `api_key: str` — default: `BROWSER_USE_API_KEY` env var
- `base_url: str` — default: `https://api.browser-use.com/api/v3`
- `timeout: float` — HTTP request timeout in seconds (default: `30.0`). Not the polling timeout.

### run() parameters (v3)
All optional keyword arguments:
- `model: str` — `"bu-mini"` (default) or `"bu-max"` (more capable)
- `output_schema: type[BaseModel]` — Pydantic model for structured output (alias: `schema`)
- `session_id: str` — reuse an existing session
- `keep_alive: bool` — keep session idle after task for follow-ups (default: `False`)
- `max_cost_usd: float` — cost cap in USD; agent stops if exceeded
- `profile_id: str` — persistent browser profile (cookies, localStorage)
- `proxy_country_code: str` — residential proxy country (e.g. `"us"`, `"de"`)

`run()` returns an `AsyncSessionRun` (async) or `SessionResult` (sync):
- **AsyncSessionRun**: awaitable. After `await`, gives a `SessionResult`. Also has `.session_id`, `.result`, `.output` properties.
- Polling defaults: interval **2 seconds**, timeout **300 seconds** (5 min). Raises `TimeoutError` if exceeded.
- Terminal statuses: `idle`, `stopped`, `timed_out`, `error`.

### SessionResult fields
- `output` — typed output (`str` or Pydantic model)
- `id` — session UUID
- `status` — `created`, `idle`, `running`, `stopped`, `timed_out`, `error`
- `model` — `bu-mini` or `bu-max`
- `title` — auto-generated title (or `None`)
- `live_url` — real-time browser monitoring URL
- `profile_id`, `proxy_country_code`, `max_cost_usd` — echo of request params
- `total_input_tokens`, `total_output_tokens` — token usage
- `llm_cost_usd`, `proxy_cost_usd`, `proxy_used_mb`, `total_cost_usd` — cost breakdown (strings)
- `created_at`, `updated_at` — timestamps

### Resources (v3)
```python
# Sessions — reusable browser environments
session = await client.sessions.create(proxy_country_code="us")
result1 = await client.run("Log into example.com", session_id=str(session.id), keep_alive=True)
result2 = await client.run("Now click settings", session_id=str(session.id))
await client.sessions.stop(str(session.id))

# Sessions with profiles — persistent login state (cookies, localStorage)
session = await client.sessions.create(profile_id="your-profile-uuid")

# Files — upload to a session before running a task
upload_resp = await client.sessions.upload_files(
    str(session.id),
    files=[FileUploadItem(name="data.csv", content_type="text/csv")],
)
# PUT each file to upload_resp.files[i].upload_url with matching Content-Type header
# Each FileUploadResponseItem has: .name, .upload_url, .path (S3-relative)

# Files — list/download from session workspace
file_list = await client.sessions.files(
    str(session.id),
    include_urls=True,    # presigned download URLs (60s expiry)
    prefix="outputs/",    # filter by path prefix
    limit=50,             # max per page (default 50, max 100)
    cursor=None,          # pagination cursor from previous response
)
# Each FileInfo has: .path, .size, .last_modified, .url
# FileListResponse has: .files, .next_cursor, .has_more

# Session management
sessions_list = await client.sessions.list(page=1, page_size=20)
# SessionListResponse has: .sessions, .total, .page, .page_size
details = await client.sessions.get(str(session.id))
await client.sessions.stop(str(session.id), strategy="task")     # stop task only, keep session
await client.sessions.stop(str(session.id), strategy="session")  # destroy sandbox (default)
await client.sessions.delete(str(session.id))

# Cost tracking (on any SessionResult)
print(result.total_cost_usd, result.llm_cost_usd, result.proxy_cost_usd)
print(result.total_input_tokens, result.total_output_tokens)

# Cleanup
await client.close()  # or client.close() for sync
```

### sessions.create() parameters (v3)
Creates a session and optionally dispatches a task. All optional:
- `task: str` — omit to create an idle session (e.g. for file uploads first)
- `model: str` — `"bu-mini"` (default) or `"bu-max"`
- `session_id: str` — dispatch to an existing idle session instead of creating new
- `keep_alive: bool` — keep session alive after task (default: `False`)
- `max_cost_usd: float` — cost cap in USD
- `profile_id: str` — browser profile to load
- `proxy_country_code: str` — residential proxy country
- `output_schema: dict` — JSON Schema for structured output (prefer `run()` with Pydantic/Zod instead)

### FileUploadItem fields
- `name: str` — filename, e.g. `"data.csv"` (required)
- `content_type: str` — MIME type, e.g. `"text/csv"` (default: `"application/octet-stream"`)

### Error handling (v3)
```python
from browser_use_sdk.v3 import AsyncBrowserUse, BrowserUseError

try:
    result = await client.run("Do something")
except TimeoutError:
    print("SDK polling timed out (5 min default)")
except BrowserUseError as e:
    print(f"API error: {e}")
```

## TypeScript SDK (v3)

```typescript
import { BrowserUse } from "browser-use-sdk/v3";
import { readFileSync } from "fs";
import { z } from "zod";

const client = new BrowserUse();

const result = await client.run("Find the top HN post");
console.log(result.output);

// Structured output (Zod)
const Product = z.object({ name: z.string(), price: z.number() });
const typed = await client.run("Get product info", { schema: Product });

// Resources: client.sessions
const session = await client.sessions.create({ proxyCountryCode: "us" });
await client.run("Log in", { sessionId: session.id, keepAlive: true });
await client.run("Click settings", { sessionId: session.id });
await client.sessions.stop(session.id);

// File upload
const upload = await client.sessions.uploadFiles(session.id, {
  files: [{ name: "data.csv", contentType: "text/csv" }],
});
await fetch(upload.files[0].uploadUrl, { method: "PUT", body: readFileSync("data.csv") });

// File listing
const files = await client.sessions.files(session.id, {
  includeUrls: true, prefix: "outputs/", limit: 50, cursor: null,
});

// Session management
const list = await client.sessions.list({ page: 1, page_size: 20 });
const details = await client.sessions.get(session.id);
await client.sessions.stop(session.id, { strategy: "task" });
await client.sessions.delete(session.id);
```

### Constructor options (v3)
```typescript
const client = new BrowserUse({
  apiKey: "...",       // default: process.env.BROWSER_USE_API_KEY
  baseUrl: "...",      // default: https://api.browser-use.com/api/v3
  maxRetries: 2,       // retry count for 429 errors
  timeout: 30_000,     // HTTP request timeout in ms (not polling timeout)
});
```

### run() options (v3, second argument)
- `model` — `"bu-mini"` (default) or `"bu-max"`
- `schema` — Zod schema for structured output
- `sessionId` — reuse an existing session
- `keepAlive` — keep session alive after task (default: `false`)
- `maxCostUsd` — cost cap in USD
- `profileId` — persistent browser profile UUID
- `proxyCountryCode` — residential proxy country code
- `outputSchema` — raw JSON Schema object (prefer `schema` with Zod)
- `timeout` — max polling time in ms (default: `300_000`)
- `interval` — polling interval in ms (default: `2_000`)

`run()` returns a `SessionRun<T>` — awaitable. After `await`, gives a `SessionResult<T>`. Also has `.sessionId` and `.result` properties.

## Key concepts (v3)
- **Task**: text prompt → agent browses → returns output
- **Session**: stateful browser sandbox. Auto-created by default, or create manually for follow-up tasks
- **Profile**: persistent browser state (cookies, localStorage). Survives across sessions
- **Profile Sync**: upload local cookies to cloud: `curl -fsSL https://browser-use.com/profile.sh | sh`
- **Proxies**: set `proxy_country_code` on session or `run()`. 195+ countries. CAPTCHAs handled automatically
- **Stealth**: on by default. Anti-detect, CAPTCHA solving, ad blocking
- **Models**: `bu-mini` (default, faster/cheaper) and `bu-max` (more capable)
- **Cost control**: set `max_cost_usd` to cap spending. Check `total_cost_usd` on the result
- **Autonomous execution**: the agent decides how many steps to take. There is no max steps parameter
- **keep_alive**: if `true`, session stays idle after task for follow-ups. If `false` (default), session auto-stops
- **Live URL**: every session has a `live_url` for real-time browser monitoring
- **File I/O**: upload files to a session before a task, download from workspace after. Max 10 files per upload, presigned URLs expire in 60s (downloads)
- **Stop strategies**: `strategy="session"` (default) destroys sandbox. `strategy="task"` stops task only
- **Integrations**: the agent can automatically discover and use third-party service integrations (email, Slack, calendars, etc.). When a task involves an external service, just describe the action — the agent will find the right integration and handle auth

---

# Browser Use Cloud v2 SDK

## Python SDK (v2)

```python
from browser_use_sdk import AsyncBrowserUse
from pydantic import BaseModel

client = AsyncBrowserUse()

# Run a task (await for result)
result = await client.run("Find the top HN post")  # -> TaskResult[str]
print(result.output)   # str
print(result.id)       # task ID
print(result.status)   # "finished"

# Structured output
class Product(BaseModel):
    name: str
    price: float

result = await client.run("Get product info from amazon.com/dp/...", output_schema=Product)
print(result.output)  # Product(name=..., price=...)

# Stream steps (async for)
async for step in client.run("Go to google.com and search for 'browser use'"):
    print(f"[{step.number}] {step.next_goal} — {step.url}")
```

### run() parameters (v2)
All optional keyword arguments:
- `session_id: str` — reuse an existing session
- `llm: str` — model override (default: Browser Use LLM)
- `start_url: str` — initial page URL
- `max_steps: int` — max agent steps (default 100)
- `output_schema: type[BaseModel]` — Pydantic model for structured output (alias: `schema`)
- `secrets: dict[str, str]` — domain-specific credentials
- `allowed_domains: list[str]` — restrict agent to these domains
- `session_settings: SessionSettings` — proxy, profile, browser config
- `flash_mode: bool` — faster but less careful
- `thinking: bool` — extended reasoning
- `vision: bool | str` — vision/screenshot mode
- `highlight_elements: bool` — highlight interactive elements
- `system_prompt_extension: str` — append to system prompt
- `judge: bool` — enable quality judge
- `skill_ids: list[str]` — skills to use
- `op_vault_id: str` — 1Password vault ID for 2FA/credentials
- `metadata: dict[str, str]` — custom metadata

### Resources (v2)
```python
# Sessions — reusable browser environments
session = await client.sessions.create(proxy_country_code="us")
result1 = await client.run("Log into example.com", session_id=session.id)
result2 = await client.run("Now click settings", session_id=session.id)
await client.sessions.stop(session.id)

# Profiles — persistent login state (cookies, localStorage)
profile = await client.profiles.create(name="my-profile")
session = await client.sessions.create(profile_id=profile.id)

# Files
url_info = await client.files.session_url(session_id, file_name="input.pdf", content_type="application/pdf", size_bytes=1024)
output = await client.files.task_output(task_id, file_id)

# Browser API — direct CDP access
browser = await client.browsers.create(proxy_country_code="de")
# Connect via browser.cdp_url with Playwright/Puppeteer/Selenium

# Skills — turn websites into APIs
skill = await client.skills.create(goal="Extract product data from Amazon", agent_prompt="...")
result = await client.skills.execute(skill.id, parameters={"url": "..."})

# Marketplace
skills = await client.marketplace.list()
result = await client.marketplace.execute(skill_id, parameters={...})

# Billing
account = await client.billing.account()
```

## TypeScript SDK (v2)

```typescript
import { BrowserUse } from "browser-use-sdk";
import { z } from "zod";

const client = new BrowserUse();

const result = await client.run("Find the top HN post");
console.log(result.output);

// Structured output (Zod)
const Product = z.object({ name: z.string(), price: z.number() });
const typed = await client.run("Get product info", { schema: Product });

// Stream steps
for await (const step of client.run("Go to google.com")) {
  console.log(`[${step.number}] ${step.nextGoal}`);
}

// Resources: client.tasks, client.sessions, client.profiles,
// client.browsers, client.files, client.skills, client.marketplace, client.billing
```

### run() options (v2, second argument)
- `sessionId`, `llm`, `startUrl`, `maxSteps`, `schema` (Zod)
- `secrets`, `allowedDomains`, `sessionSettings`
- `flashMode`, `thinking`, `vision`, `highlightElements`
- `systemPromptExtension`, `judge`, `skillIds`, `opVaultId`
- `timeout` (ms, default 300000), `interval` (ms, default 2000)

## Key concepts (v2)
- **Task**: text prompt → agent browses → returns output
- **Session**: stateful browser. Auto-created by default, or create manually for follow-up tasks
- **Profile**: persistent browser state (cookies, localStorage). Survives across sessions
- **Profile Sync**: upload local cookies to cloud: `curl -fsSL https://browser-use.com/profile.sh | sh`
- **Proxies**: set `proxy_country_code` on session. 195+ countries. CAPTCHAs handled automatically
- **Stealth**: on by default. Anti-detect, CAPTCHA solving, ad blocking
- **Browser Use LLM**: default model, optimized for browser tasks. 15× cheaper
- **Vision**: agent can take screenshots. Enable with `vision=True`
- **1Password**: auto-fill passwords and 2FA/TOTP codes with `op_vault_id`

## V3 openapi specs
{
  "openapi": "3.1.0",
  "info": {
    "title": "Browser Use Public API v3",
    "summary": "Browser Use session-based agent API (v3)",
    "version": "3.0.0"
  },
  "servers": [
    {
      "url": "https://api.browser-use.com/api/v3",
      "description": "Production server"
    }
  ],
  "paths": {
    "/sessions": {
      "post": {
        "tags": [
          "Sessions"
        ],
        "summary": "Create Session",
        "description": "Create a session and/or dispatch a task.\n\n- Without session_id, without task: creates a new idle session (e.g. for file uploads).\n- Without session_id, with task: creates a new session and dispatches the task.\n- With session_id, with task: dispatches the task to an existing idle session.\n- With session_id, without task: 422 — task is required when targeting an existing session.\n\nIf keep_alive is false (default), the session auto-stops when the task finishes.\nIf keep_alive is true, the session stays idle after the task, ready for follow-ups.",
        "operationId": "create_session_sessions_post",
        "security": [
          {
            "APIKeyHeader": []
          }
        ],
        "requestBody": {
          "required": true,
          "content": {
            "application/json": {
              "schema": {
                "$ref": "#/components/schemas/RunTaskRequest"
              }
            }
          }
        },
        "responses": {
          "200": {
            "description": "Successful Response",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/SessionResponse"
                }
              }
            }
          },
          "422": {
            "description": "Validation Error",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            }
          }
        }
      },
      "get": {
        "tags": [
          "Sessions"
        ],
        "summary": "List Sessions",
        "description": "List sessions for the authenticated project.",
        "operationId": "list_sessions_sessions_get",
        "security": [
          {
            "APIKeyHeader": []
          }
        ],
        "parameters": [
          {
            "name": "page",
            "in": "query",
            "required": false,
            "schema": {
              "type": "integer",
              "minimum": 1,
              "default": 1,
              "title": "Page"
            }
          },
          {
            "name": "page_size",
            "in": "query",
            "required": false,
            "schema": {
              "type": "integer",
              "maximum": 100,
              "minimum": 1,
              "default": 20,
              "title": "Page Size"
            }
          }
        ],
        "responses": {
          "200": {
            "description": "Successful Response",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/SessionListResponse"
                }
              }
            }
          },
          "422": {
            "description": "Validation Error",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            }
          }
        }
      }
    },
    "/sessions/{session_id}": {
      "get": {
        "tags": [
          "Sessions"
        ],
        "summary": "Get Session",
        "description": "Get session details. Use this to poll for task completion and output.",
        "operationId": "get_session_sessions__session_id__get",
        "security": [
          {
            "APIKeyHeader": []
          }
        ],
        "parameters": [
          {
            "name": "session_id",
            "in": "path",
            "required": true,
            "schema": {
              "type": "string",
              "format": "uuid",
              "title": "Session Id"
            }
          }
        ],
        "responses": {
          "200": {
            "description": "Successful Response",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/SessionResponse"
                }
              }
            }
          },
          "422": {
            "description": "Validation Error",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            }
          }
        }
      },
      "delete": {
        "tags": [
          "Sessions"
        ],
        "summary": "Delete Session",
        "description": "Soft-delete a session. Stops the sandbox first if still running.",
        "operationId": "delete_session_sessions__session_id__delete",
        "security": [
          {
            "APIKeyHeader": []
          }
        ],
        "parameters": [
          {
            "name": "session_id",
            "in": "path",
            "required": true,
            "schema": {
              "type": "string",
              "format": "uuid",
              "title": "Session Id"
            }
          }
        ],
        "responses": {
          "204": {
            "description": "Successful Response"
          },
          "422": {
            "description": "Validation Error",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            }
          }
        }
      }
    },
    "/sessions/{session_id}/stop": {
      "post": {
        "tags": [
          "Sessions"
        ],
        "summary": "Stop Session",
        "description": "Stop a session or the running task.\n\n- strategy=session (default): destroy sandbox entirely, session → stopped.\n- strategy=task: stop the running query, session stays alive (→ idle).",
        "operationId": "stop_session_sessions__session_id__stop_post",
        "security": [
          {
            "APIKeyHeader": []
          }
        ],
        "parameters": [
          {
            "name": "session_id",
            "in": "path",
            "required": true,
            "schema": {
              "type": "string",
              "format": "uuid",
              "title": "Session Id"
            }
          }
        ],
        "requestBody": {
          "content": {
            "application/json": {
              "schema": {
                "anyOf": [
                  {
                    "$ref": "#/components/schemas/StopSessionRequest"
                  },
                  {
                    "type": "null"
                  }
                ],
                "title": "Body"
              }
            }
          }
        },
        "responses": {
          "200": {
            "description": "Successful Response",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/SessionResponse"
                }
              }
            }
          },
          "422": {
            "description": "Validation Error",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            }
          }
        }
      }
    },
    "/sessions/{session_id}/files": {
      "get": {
        "tags": [
          "Files"
        ],
        "summary": "List Session Files",
        "description": "List files in a session's workspace.\n\nReturns paginated file metadata. Pass includeUrls=true to get\npresigned download URLs (60s expiry) inline with each file.",
        "operationId": "list_session_files_sessions__session_id__files_get",
        "security": [
          {
            "APIKeyHeader": []
          }
        ],
        "parameters": [
          {
            "name": "session_id",
            "in": "path",
            "required": true,
            "schema": {
              "type": "string",
              "format": "uuid",
              "title": "Session Id"
            }
          },
          {
            "name": "prefix",
            "in": "query",
            "required": false,
            "schema": {
              "type": "string",
              "default": "",
              "title": "Prefix"
            }
          },
          {
            "name": "limit",
            "in": "query",
            "required": false,
            "schema": {
              "type": "integer",
              "maximum": 100,
              "minimum": 1,
              "default": 50,
              "title": "Limit"
            }
          },
          {
            "name": "cursor",
            "in": "query",
            "required": false,
            "schema": {
              "anyOf": [
                {
                  "type": "string"
                },
                {
                  "type": "null"
                }
              ],
              "title": "Cursor"
            }
          },
          {
            "name": "includeUrls",
            "in": "query",
            "required": false,
            "schema": {
              "type": "boolean",
              "default": false,
              "title": "Includeurls"
            }
          },
          {
            "name": "shallow",
            "in": "query",
            "required": false,
            "schema": {
              "type": "boolean",
              "default": false,
              "title": "Shallow"
            }
          }
        ],
        "responses": {
          "200": {
            "description": "Successful Response",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/FileListResponse"
                }
              }
            }
          },
          "422": {
            "description": "Validation Error",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            }
          }
        }
      }
    },
    "/sessions/{session_id}/files/upload": {
      "post": {
        "tags": [
          "Files"
        ],
        "summary": "Upload Session Files",
        "description": "Get presigned PUT URLs for uploading files to a session's workspace.\n\nFiles are placed under ``uploads/`` in the session's S3 prefix. After\nreceiving the URLs, PUT each file directly to S3 using the returned\n``uploadUrl`` with the matching ``Content-Type`` header.",
        "operationId": "upload_session_files_sessions__session_id__files_upload_post",
        "security": [
          {
            "APIKeyHeader": []
          }
        ],
        "parameters": [
          {
            "name": "session_id",
            "in": "path",
            "required": true,
            "schema": {
              "type": "string",
              "format": "uuid",
              "title": "Session Id"
            }
          }
        ],
        "requestBody": {
          "required": true,
          "content": {
            "application/json": {
              "schema": {
                "$ref": "#/components/schemas/FileUploadRequest"
              }
            }
          }
        },
        "responses": {
          "200": {
            "description": "Successful Response",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/FileUploadResponse"
                }
              }
            }
          },
          "422": {
            "description": "Validation Error",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            }
          }
        }
      }
    },
    "/workspaces": {
      "get": {
        "tags": [
          "Workspaces"
        ],
        "summary": "List Workspaces",
        "description": "Get paginated list of workspaces.",
        "operationId": "list_workspaces_workspaces_get",
        "security": [
          {
            "APIKeyHeader": []
          }
        ],
        "parameters": [
          {
            "name": "pageSize",
            "in": "query",
            "required": false,
            "schema": {
              "type": "integer",
              "maximum": 100,
              "minimum": 1,
              "default": 10,
              "title": "Pagesize"
            }
          },
          {
            "name": "pageNumber",
            "in": "query",
            "required": false,
            "schema": {
              "type": "integer",
              "minimum": 1,
              "default": 1,
              "title": "Pagenumber"
            }
          }
        ],
        "responses": {
          "200": {
            "description": "Successful Response",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/WorkspaceListResponse"
                }
              }
            }
          },
          "422": {
            "description": "Validation Error",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            }
          }
        }
      },
      "post": {
        "tags": [
          "Workspaces"
        ],
        "summary": "Create Workspace",
        "description": "Create a new workspace for persistent shared file storage across sessions.",
        "operationId": "create_workspace_workspaces_post",
        "security": [
          {
            "APIKeyHeader": []
          }
        ],
        "requestBody": {
          "content": {
            "application/json": {
              "schema": {
                "$ref": "#/components/schemas/WorkspaceCreateRequest"
              }
            }
          }
        },
        "responses": {
          "201": {
            "description": "Successful Response",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/WorkspaceView"
                }
              }
            }
          },
          "422": {
            "description": "Validation Error",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            }
          }
        }
      }
    },
    "/workspaces/{workspace_id}": {
      "get": {
        "tags": [
          "Workspaces"
        ],
        "summary": "Get Workspace",
        "description": "Get workspace details.",
        "operationId": "get_workspace_workspaces__workspace_id__get",
        "security": [
          {
            "APIKeyHeader": []
          }
        ],
        "parameters": [
          {
            "name": "workspace_id",
            "in": "path",
            "required": true,
            "schema": {
              "type": "string",
              "format": "uuid",
              "title": "Workspace Id"
            }
          }
        ],
        "responses": {
          "200": {
            "description": "Successful Response",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/WorkspaceView"
                }
              }
            }
          },
          "422": {
            "description": "Validation Error",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            }
          }
        }
      },
      "patch": {
        "tags": [
          "Workspaces"
        ],
        "summary": "Update Workspace",
        "description": "Update a workspace's name.",
        "operationId": "update_workspace_workspaces__workspace_id__patch",
        "security": [
          {
            "APIKeyHeader": []
          }
        ],
        "parameters": [
          {
            "name": "workspace_id",
            "in": "path",
            "required": true,
            "schema": {
              "type": "string",
              "format": "uuid",
              "title": "Workspace Id"
            }
          }
        ],
        "requestBody": {
          "required": true,
          "content": {
            "application/json": {
              "schema": {
                "$ref": "#/components/schemas/WorkspaceUpdateRequest"
              }
            }
          }
        },
        "responses": {
          "200": {
            "description": "Successful Response",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/WorkspaceView"
                }
              }
            }
          },
          "422": {
            "description": "Validation Error",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            }
          }
        }
      },
      "delete": {
        "tags": [
          "Workspaces"
        ],
        "summary": "Delete Workspace",
        "description": "Delete a workspace and its S3 data.",
        "operationId": "delete_workspace_workspaces__workspace_id__delete",
        "security": [
          {
            "APIKeyHeader": []
          }
        ],
        "parameters": [
          {
            "name": "workspace_id",
            "in": "path",
            "required": true,
            "schema": {
              "type": "string",
              "format": "uuid",
              "title": "Workspace Id"
            }
          }
        ],
        "responses": {
          "204": {
            "description": "Successful Response"
          },
          "422": {
            "description": "Validation Error",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            }
          }
        }
      }
    },
    "/workspaces/{workspace_id}/files": {
      "get": {
        "tags": [
          "Workspaces"
        ],
        "summary": "List Workspace Files",
        "description": "List files in a workspace's S3 prefix.",
        "operationId": "list_workspace_files_workspaces__workspace_id__files_get",
        "security": [
          {
            "APIKeyHeader": []
          }
        ],
        "parameters": [
          {
            "name": "workspace_id",
            "in": "path",
            "required": true,
            "schema": {
              "type": "string",
              "format": "uuid",
              "title": "Workspace Id"
            }
          },
          {
            "name": "prefix",
            "in": "query",
            "required": false,
            "schema": {
              "type": "string",
              "default": "",
              "title": "Prefix"
            }
          },
          {
            "name": "limit",
            "in": "query",
            "required": false,
            "schema": {
              "type": "integer",
              "maximum": 100,
              "minimum": 1,
              "default": 50,
              "title": "Limit"
            }
          },
          {
            "name": "cursor",
            "in": "query",
            "required": false,
            "schema": {
              "anyOf": [
                {
                  "type": "string"
                },
                {
                  "type": "null"
                }
              ],
              "title": "Cursor"
            }
          },
          {
            "name": "includeUrls",
            "in": "query",
            "required": false,
            "schema": {
              "type": "boolean",
              "default": false,
              "title": "Includeurls"
            }
          },
          {
            "name": "shallow",
            "in": "query",
            "required": false,
            "schema": {
              "type": "boolean",
              "default": false,
              "title": "Shallow"
            }
          }
        ],
        "responses": {
          "200": {
            "description": "Successful Response",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/FileListResponse"
                }
              }
            }
          },
          "422": {
            "description": "Validation Error",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            }
          }
        }
      },
      "delete": {
        "tags": [
          "Workspaces"
        ],
        "summary": "Delete Workspace File",
        "description": "Delete a single file from a workspace.",
        "operationId": "delete_workspace_file_workspaces__workspace_id__files_delete",
        "security": [
          {
            "APIKeyHeader": []
          }
        ],
        "parameters": [
          {
            "name": "workspace_id",
            "in": "path",
            "required": true,
            "schema": {
              "type": "string",
              "format": "uuid",
              "title": "Workspace Id"
            }
          },
          {
            "name": "path",
            "in": "query",
            "required": true,
            "schema": {
              "type": "string",
              "description": "Relative file path to delete",
              "title": "Path"
            },
            "description": "Relative file path to delete"
          }
        ],
        "responses": {
          "204": {
            "description": "Successful Response"
          },
          "422": {
            "description": "Validation Error",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            }
          }
        }
      }
    },
    "/workspaces/{workspace_id}/size": {
      "get": {
        "tags": [
          "Workspaces"
        ],
        "summary": "Get Workspace Size",
        "description": "Get current storage usage for a workspace.",
        "operationId": "get_workspace_size_workspaces__workspace_id__size_get",
        "security": [
          {
            "APIKeyHeader": []
          }
        ],
        "parameters": [
          {
            "name": "workspace_id",
            "in": "path",
            "required": true,
            "schema": {
              "type": "string",
              "format": "uuid",
              "title": "Workspace Id"
            }
          }
        ],
        "responses": {
          "200": {
            "description": "Successful Response",
            "content": {
              "application/json": {
                "schema": {

                }
              }
            }
          },
          "422": {
            "description": "Validation Error",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            }
          }
        }
      }
    },
    "/workspaces/{workspace_id}/files/upload": {
      "post": {
        "tags": [
          "Workspaces"
        ],
        "summary": "Upload Workspace Files",
        "description": "Get presigned PUT URLs for uploading files to a workspace.",
        "operationId": "upload_workspace_files_workspaces__workspace_id__files_upload_post",
        "security": [
          {
            "APIKeyHeader": []
          }
        ],
        "parameters": [
          {
            "name": "workspace_id",
            "in": "path",
            "required": true,
            "schema": {
              "type": "string",
              "format": "uuid",
              "title": "Workspace Id"
            }
          },
          {
            "name": "prefix",
            "in": "query",
            "required": false,
            "schema": {
              "type": "string",
              "description": "Directory prefix to upload into (e.g. \"uploads/\")",
              "default": "",
              "title": "Prefix"
            },
            "description": "Directory prefix to upload into (e.g. \"uploads/\")"
          }
        ],
        "requestBody": {
          "required": true,
          "content": {
            "application/json": {
              "schema": {
                "$ref": "#/components/schemas/FileUploadRequest"
              }
            }
          }
        },
        "responses": {
          "200": {
            "description": "Successful Response",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/FileUploadResponse"
                }
              }
            }
          },
          "422": {
            "description": "Validation Error",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            }
          }
        }
      }
    }
  },
  "components": {
    "schemas": {
      "BuAgentSessionStatus": {
        "type": "string",
        "enum": [
          "created",
          "idle",
          "running",
          "stopped",
          "timed_out",
          "error"
        ],
        "title": "BuAgentSessionStatus"
      },
      "BuModel": {
        "type": "string",
        "enum": [
          "bu-mini",
          "bu-max"
        ],
        "title": "BuModel"
      },
      "FileInfo": {
        "properties": {
          "path": {
            "type": "string",
            "title": "Path"
          },
          "size": {
            "type": "integer",
            "title": "Size"
          },
          "lastModified": {
            "type": "string",
            "format": "date-time",
            "title": "Lastmodified"
          },
          "url": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "Url"
          }
        },
        "type": "object",
        "required": [
          "path",
          "size",
          "lastModified"
        ],
        "title": "FileInfo",
        "description": "A file in a session's workspace."
      },
      "FileListResponse": {
        "properties": {
          "files": {
            "items": {
              "$ref": "#/components/schemas/FileInfo"
            },
            "type": "array",
            "title": "Files"
          },
          "folders": {
            "items": {
              "type": "string"
            },
            "type": "array",
            "title": "Folders",
            "description": "Immediate sub-folder names at this prefix level"
          },
          "nextCursor": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "Nextcursor"
          },
          "hasMore": {
            "type": "boolean",
            "title": "Hasmore",
            "default": false
          }
        },
        "type": "object",
        "required": [
          "files"
        ],
        "title": "FileListResponse",
        "description": "Paginated file listing with optional presigned download URLs."
      },
      "FileUploadItem": {
        "properties": {
          "name": {
            "type": "string",
            "maxLength": 255,
            "minLength": 1,
            "title": "Name",
            "description": "Filename, e.g. \"data.csv\""
          },
          "contentType": {
            "type": "string",
            "maxLength": 255,
            "title": "Contenttype",
            "description": "MIME type, e.g. \"text/csv\"",
            "default": "application/octet-stream"
          },
          "size": {
            "anyOf": [
              {
                "type": "integer",
                "minimum": 1
              },
              {
                "type": "null"
              }
            ],
            "title": "Size",
            "description": "File size in bytes (required for workspace uploads)"
          }
        },
        "type": "object",
        "required": [
          "name"
        ],
        "title": "FileUploadItem",
        "description": "A single file to upload."
      },
      "FileUploadRequest": {
        "properties": {
          "files": {
            "items": {
              "$ref": "#/components/schemas/FileUploadItem"
            },
            "type": "array",
            "maxItems": 10,
            "minItems": 1,
            "title": "Files"
          }
        },
        "type": "object",
        "required": [
          "files"
        ],
        "title": "FileUploadRequest",
        "description": "Request body for generating presigned upload URLs."
      },
      "FileUploadResponse": {
        "properties": {
          "files": {
            "items": {
              "$ref": "#/components/schemas/FileUploadResponseItem"
            },
            "type": "array",
            "title": "Files"
          }
        },
        "type": "object",
        "required": [
          "files"
        ],
        "title": "FileUploadResponse",
        "description": "Presigned upload URLs for the requested files."
      },
      "FileUploadResponseItem": {
        "properties": {
          "name": {
            "type": "string",
            "title": "Name"
          },
          "uploadUrl": {
            "type": "string",
            "title": "Uploadurl"
          },
          "path": {
            "type": "string",
            "title": "Path",
            "description": "S3-relative path, e.g. \"uploads/data.csv\""
          }
        },
        "type": "object",
        "required": [
          "name",
          "uploadUrl",
          "path"
        ],
        "title": "FileUploadResponseItem",
        "description": "Presigned upload URL for a single file."
      },
      "HTTPValidationError": {
        "properties": {
          "detail": {
            "items": {
              "$ref": "#/components/schemas/ValidationError"
            },
            "type": "array",
            "title": "Detail"
          }
        },
        "type": "object",
        "title": "HTTPValidationError"
      },
      "ProxyCountryCode": {
        "type": "string",
        "enum": [
          "ad",
          "ae",
          "af",
          "ag",
          "ai",
          "al",
          "am",
          "an",
          "ao",
          "aq",
          "ar",
          "as",
          "at",
          "au",
          "aw",
          "az",
          "ba",
          "bb",
          "bd",
          "be",
          "bf",
          "bg",
          "bh",
          "bi",
          "bj",
          "bl",
          "bm",
          "bn",
          "bo",
          "bq",
          "br",
          "bs",
          "bt",
          "bv",
          "bw",
          "by",
          "bz",
          "ca",
          "cc",
          "cd",
          "cf",
          "cg",
          "ch",
          "ck",
          "cl",
          "cm",
          "co",
          "cr",
          "cs",
          "cu",
          "cv",
          "cw",
          "cx",
          "cy",
          "cz",
          "de",
          "dj",
          "dk",
          "dm",
          "do",
          "dz",
          "ec",
          "ee",
          "eg",
          "eh",
          "er",
          "es",
          "et",
          "fi",
          "fj",
          "fk",
          "fm",
          "fo",
          "fr",
          "ga",
          "gd",
          "ge",
          "gf",
          "gg",
          "gh",
          "gi",
          "gl",
          "gm",
          "gn",
          "gp",
          "gq",
          "gr",
          "gs",
          "gt",
          "gu",
          "gw",
          "gy",
          "hk",
          "hm",
          "hn",
          "hr",
          "ht",
          "hu",
          "id",
          "ie",
          "il",
          "im",
          "in",
          "iq",
          "ir",
          "is",
          "it",
          "je",
          "jm",
          "jo",
          "jp",
          "ke",
          "kg",
          "kh",
          "ki",
          "km",
          "kn",
          "kp",
          "kr",
          "kw",
          "ky",
          "kz",
          "la",
          "lb",
          "lc",
          "li",
          "lk",
          "lr",
          "ls",
          "lt",
          "lu",
          "lv",
          "ly",
          "ma",
          "mc",
          "md",
          "me",
          "mf",
          "mg",
          "mh",
          "mk",
          "ml",
          "mm",
          "mn",
          "mo",
          "mp",
          "mq",
          "mr",
          "ms",
          "mt",
          "mu",
          "mv",
          "mw",
          "mx",
          "my",
          "mz",
          "na",
          "nc",
          "ne",
          "nf",
          "ng",
          "ni",
          "nl",
          "no",
          "np",
          "nr",
          "nu",
          "nz",
          "om",
          "pa",
          "pe",
          "pf",
          "pg",
          "ph",
          "pk",
          "pl",
          "pm",
          "pn",
          "pr",
          "ps",
          "pt",
          "pw",
          "py",
          "qa",
          "re",
          "ro",
          "rs",
          "ru",
          "rw",
          "sa",
          "sb",
          "sc",
          "sd",
          "se",
          "sg",
          "sh",
          "si",
          "sj",
          "sk",
          "sl",
          "sm",
          "sn",
          "so",
          "sr",
          "ss",
          "st",
          "sv",
          "sx",
          "sy",
          "sz",
          "tc",
          "td",
          "tf",
          "tg",
          "th",
          "tj",
          "tk",
          "tl",
          "tm",
          "tn",
          "to",
          "tr",
          "tt",
          "tv",
          "tw",
          "tz",
          "ua",
          "ug",
          "uk",
          "us",
          "uy",
          "uz",
          "va",
          "vc",
          "ve",
          "vg",
          "vi",
          "vn",
          "vu",
          "wf",
          "ws",
          "xk",
          "ye",
          "yt",
          "za",
          "zm",
          "zw"
        ],
        "title": "ProxyCountryCode"
      },
      "RunTaskRequest": {
        "properties": {
          "task": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "Task"
          },
          "model": {
            "$ref": "#/components/schemas/BuModel",
            "default": "bu-mini"
          },
          "sessionId": {
            "anyOf": [
              {
                "type": "string",
                "format": "uuid"
              },
              {
                "type": "null"
              }
            ],
            "title": "Sessionid"
          },
          "keepAlive": {
            "type": "boolean",
            "title": "Keepalive",
            "default": false
          },
          "maxCostUsd": {
            "anyOf": [
              {
                "type": "number"
              },
              {
                "type": "string",
                "pattern": "^(?!^[-+.]*$)[+-]?0*\\d*\\.?\\d*$"
              },
              {
                "type": "null"
              }
            ],
            "title": "Maxcostusd"
          },
          "profileId": {
            "anyOf": [
              {
                "type": "string",
                "format": "uuid"
              },
              {
                "type": "null"
              }
            ],
            "title": "Profileid"
          },
          "workspaceId": {
            "anyOf": [
              {
                "type": "string",
                "format": "uuid"
              },
              {
                "type": "null"
              }
            ],
            "title": "Workspaceid"
          },
          "proxyCountryCode": {
            "anyOf": [
              {
                "$ref": "#/components/schemas/ProxyCountryCode"
              },
              {
                "type": "null"
              }
            ]
          },
          "outputSchema": {
            "anyOf": [
              {
                "additionalProperties": true,
                "type": "object"
              },
              {
                "type": "null"
              }
            ],
            "title": "Outputschema"
          }
        },
        "type": "object",
        "title": "RunTaskRequest",
        "description": "Unified request for creating a session or dispatching a task.\n\n- Without session_id + without task: creates a new idle session (for file uploads, etc.)\n- Without session_id + with task: creates a new session and dispatches the task\n- With session_id + with task: dispatches the task to an existing idle session\n- With session_id + without task: 422 (task required when dispatching to existing session)"
      },
      "SessionListResponse": {
        "properties": {
          "sessions": {
            "items": {
              "$ref": "#/components/schemas/SessionResponse"
            },
            "type": "array",
            "title": "Sessions"
          },
          "total": {
            "type": "integer",
            "title": "Total"
          },
          "page": {
            "type": "integer",
            "title": "Page"
          },
          "pageSize": {
            "type": "integer",
            "title": "Pagesize"
          }
        },
        "type": "object",
        "required": [
          "sessions",
          "total",
          "page",
          "pageSize"
        ],
        "title": "SessionListResponse"
      },
      "SessionResponse": {
        "properties": {
          "id": {
            "type": "string",
            "format": "uuid",
            "title": "Id"
          },
          "status": {
            "$ref": "#/components/schemas/BuAgentSessionStatus"
          },
          "model": {
            "$ref": "#/components/schemas/BuModel"
          },
          "title": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "Title"
          },
          "output": {
            "anyOf": [
              {

              },
              {
                "type": "null"
              }
            ],
            "title": "Output"
          },
          "outputSchema": {
            "anyOf": [
              {
                "additionalProperties": true,
                "type": "object"
              },
              {
                "type": "null"
              }
            ],
            "title": "Outputschema"
          },
          "liveUrl": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "Liveurl"
          },
          "profileId": {
            "anyOf": [
              {
                "type": "string",
                "format": "uuid"
              },
              {
                "type": "null"
              }
            ],
            "title": "Profileid"
          },
          "workspaceId": {
            "anyOf": [
              {
                "type": "string",
                "format": "uuid"
              },
              {
                "type": "null"
              }
            ],
            "title": "Workspaceid"
          },
          "proxyCountryCode": {
            "anyOf": [
              {
                "$ref": "#/components/schemas/ProxyCountryCode"
              },
              {
                "type": "null"
              }
            ]
          },
          "maxCostUsd": {
            "anyOf": [
              {
                "type": "string",
                "pattern": "^(?!^[-+.]*$)[+-]?0*\\d*\\.?\\d*$"
              },
              {
                "type": "null"
              }
            ],
            "title": "Maxcostusd"
          },
          "totalInputTokens": {
            "type": "integer",
            "title": "Totalinputtokens",
            "default": 0
          },
          "totalOutputTokens": {
            "type": "integer",
            "title": "Totaloutputtokens",
            "default": 0
          },
          "proxyUsedMb": {
            "type": "string",
            "pattern": "^(?!^[-+.]*$)[+-]?0*\\d*\\.?\\d*$",
            "title": "Proxyusedmb",
            "default": "0"
          },
          "llmCostUsd": {
            "type": "string",
            "pattern": "^(?!^[-+.]*$)[+-]?0*\\d*\\.?\\d*$",
            "title": "Llmcostusd",
            "default": "0"
          },
          "proxyCostUsd": {
            "type": "string",
            "pattern": "^(?!^[-+.]*$)[+-]?0*\\d*\\.?\\d*$",
            "title": "Proxycostusd",
            "default": "0"
          },
          "totalCostUsd": {
            "type": "string",
            "pattern": "^(?!^[-+.]*$)[+-]?0*\\d*\\.?\\d*$",
            "title": "Totalcostusd",
            "default": "0"
          },
          "createdAt": {
            "type": "string",
            "format": "date-time",
            "title": "Createdat"
          },
          "updatedAt": {
            "type": "string",
            "format": "date-time",
            "title": "Updatedat"
          }
        },
        "type": "object",
        "required": [
          "id",
          "status",
          "model",
          "createdAt",
          "updatedAt"
        ],
        "title": "SessionResponse"
      },
      "StopSessionRequest": {
        "properties": {
          "strategy": {
            "$ref": "#/components/schemas/StopStrategy",
            "default": "session"
          }
        },
        "type": "object",
        "title": "StopSessionRequest"
      },
      "StopStrategy": {
        "type": "string",
        "enum": [
          "task",
          "session"
        ],
        "title": "StopStrategy"
      },
      "ValidationError": {
        "properties": {
          "loc": {
            "items": {
              "anyOf": [
                {
                  "type": "string"
                },
                {
                  "type": "integer"
                }
              ]
            },
            "type": "array",
            "title": "Location"
          },
          "msg": {
            "type": "string",
            "title": "Message"
          },
          "type": {
            "type": "string",
            "title": "Error Type"
          }
        },
        "type": "object",
        "required": [
          "loc",
          "msg",
          "type"
        ],
        "title": "ValidationError"
      },
      "WorkspaceCreateRequest": {
        "properties": {
          "name": {
            "anyOf": [
              {
                "type": "string",
                "maxLength": 100
              },
              {
                "type": "null"
              }
            ],
            "title": "Name",
            "description": "Optional name for the workspace"
          }
        },
        "type": "object",
        "title": "WorkspaceCreateRequest",
        "description": "Request model for creating a new workspace."
      },
      "WorkspaceListResponse": {
        "properties": {
          "items": {
            "items": {
              "$ref": "#/components/schemas/WorkspaceView"
            },
            "type": "array",
            "title": "Items",
            "description": "List of workspace views for the current page"
          },
          "totalItems": {
            "type": "integer",
            "title": "Total Items",
            "description": "Total number of items in the list"
          },
          "pageNumber": {
            "type": "integer",
            "title": "Page Number",
            "description": "Page number"
          },
          "pageSize": {
            "type": "integer",
            "title": "Page Size",
            "description": "Number of items per page"
          }
        },
        "type": "object",
        "required": [
          "items",
          "totalItems",
          "pageNumber",
          "pageSize"
        ],
        "title": "WorkspaceListResponse",
        "description": "Response model for paginated workspace list requests."
      },
      "WorkspaceUpdateRequest": {
        "properties": {
          "name": {
            "anyOf": [
              {
                "type": "string",
                "maxLength": 100
              },
              {
                "type": "null"
              }
            ],
            "title": "Name",
            "description": "Optional name for the workspace"
          }
        },
        "type": "object",
        "title": "WorkspaceUpdateRequest",
        "description": "Request model for updating a workspace."
      },
      "WorkspaceView": {
        "properties": {
          "id": {
            "type": "string",
            "format": "uuid",
            "title": "ID",
            "description": "Unique identifier for the workspace"
          },
          "name": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "Name",
            "description": "Optional name for the workspace"
          },
          "createdAt": {
            "type": "string",
            "format": "date-time",
            "title": "Created At",
            "description": "Timestamp when the workspace was created"
          },
          "updatedAt": {
            "type": "string",
            "format": "date-time",
            "title": "Updated At",
            "description": "Timestamp when the workspace was last updated"
          }
        },
        "type": "object",
        "required": [
          "id",
          "createdAt",
          "updatedAt"
        ],
        "title": "WorkspaceView",
        "description": "View model for a workspace — persistent shared storage across sessions."
      }
    },
    "securitySchemes": {
      "APIKeyHeader": {
        "type": "apiKey",
        "in": "header",
        "name": "X-Browser-Use-API-Key"
      }
    }
  }
}
