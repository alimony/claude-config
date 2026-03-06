# Vercel: Storage
Based on Vercel documentation.

## Overview: Choosing a Storage Product

| Product | Reads | Writes | Best For | Status |
|---------|-------|--------|----------|--------|
| **Blob** | Fast | Milliseconds | Large files (images, videos, documents) | Active |
| **Edge Config** | Ultra-fast (<1ms typical, <15ms P99) | Seconds (up to 10s propagation) | Feature flags, A/B tests, redirects | Active |
| **Postgres** | -- | -- | Relational data, ACID transactions | Deprecated -- use Neon via Marketplace |
| **KV (Redis)** | -- | -- | Caching, sessions, rate limiting | Deprecated -- use Upstash via Marketplace |

Vercel Postgres and Vercel KV were retired in December 2024. Existing stores were migrated to Neon and Upstash respectively. New projects should use the Vercel Marketplace for Postgres, Redis, NoSQL, and vector databases.

---

## Vercel Blob

Object storage for files (images, videos, audio, documents). Backed by S3 with 11 nines durability and 99.99% availability.

### Setup

```bash
npm i @vercel/blob
```

Create a Blob store in the Vercel Dashboard (Storage > Create Database > Blob). Choose **Private** or **Public** access -- this cannot be changed later. Pull the auto-created env var locally:

```bash
vercel env pull  # provides BLOB_READ_WRITE_TOKEN
```

### Private vs Public Storage

| | Private | Public |
|---|---------|--------|
| Write access | Authenticated (token) | Authenticated (token) |
| Read access | Authenticated (via `get()` in your Function) | Anyone with the URL |
| Delivery | Through your Vercel Function | Direct blob URL via CDN |
| Best for | Sensitive documents, gated content | Public media, images, videos |

### SDK Reference (`@vercel/blob`)

All methods default to `process.env.BLOB_READ_WRITE_TOKEN` for auth.

#### `put(pathname, body, options)` -- Upload

```js
import { put } from '@vercel/blob';

const blob = await put('avatars/user-123.jpg', file, {
  access: 'public',           // or 'private' (required)
  addRandomSuffix: true,      // default: false, recommended to avoid conflicts
  contentType: 'image/jpeg',  // auto-detected from extension if omitted
  cacheControlMaxAge: 2592000, // seconds, default: 1 month
  multipart: true,            // recommended for files > 100 MB
  allowOverwrite: false,      // default: false, throws on duplicate pathname
  // ifMatch: etag,           // conditional write (optimistic concurrency)
  // onUploadProgress: ({ loaded, total, percentage }) => {},
});
// Returns: { pathname, contentType, contentDisposition, url, downloadUrl, etag }
```

#### `get(urlOrPathname, options)` -- Download content

```js
import { get } from '@vercel/blob';

const response = await get('avatars/user-123.jpg', { access: 'private' });
// Returns: { stream, contentType, contentDisposition, etag, statusCode, ... }
// Returns null if not found.
// Use ifNoneMatch for conditional reads (returns statusCode: 304 if unchanged).
```

#### `head(urlOrPathname, options)` -- Metadata only

```js
import { head } from '@vercel/blob';

const metadata = await head('avatars/user-123.jpg');
// Returns: { pathname, contentType, contentDisposition, url, downloadUrl, uploadedAt, size, etag }
// Throws BlobNotFoundError if not found.
```

#### `del(urlOrPathname, options)` -- Delete

```js
import { del } from '@vercel/blob';

await del('avatars/user-123.jpg');
await del(['file1.jpg', 'file2.jpg']); // batch delete
// Returns void. Never throws if blob doesn't exist. Free of charge.
// ifMatch option available for single-URL conditional deletes.
```

#### `copy(fromUrl, toPathname, options)` -- Copy

```js
import { copy } from '@vercel/blob';

const blob = await copy('avatars/old.jpg', 'avatars/new.jpg', {
  access: 'public',
  // addRandomSuffix defaults to false (unlike put)
  // contentType and cacheControlMaxAge are NOT copied from source
});
```

#### `list(options)` -- List blobs

```js
import { list } from '@vercel/blob';

const { blobs, cursor, hasMore, folders } = await list({
  prefix: 'avatars/',  // filter by folder
  limit: 1000,         // default: 1000
  cursor: prevCursor,  // for pagination
  mode: 'folded',      // 'expanded' (default) or 'folded' (groups by folder)
});
```

Blobs are returned in lexicographical order by pathname, not by date. For date ordering, include timestamps in pathnames (e.g., `reports/2026-03-06-quarterly.pdf`).

### Client Uploads (files > 4.5 MB)

Server uploads are limited to 4.5 MB (Vercel Functions body limit). For larger files, use client uploads:

```js
// Browser code
import { upload } from '@vercel/blob/client';

const blob = await upload('video.mp4', file, {
  access: 'public',
  handleUploadUrl: '/api/upload', // your server route
  multipart: true,                // recommended for large files
  // onUploadProgress: ({ loaded, total, percentage }) => {},
});
```

```js
// Server route (e.g., app/api/upload/route.ts)
import { handleUpload } from '@vercel/blob/client';

export async function POST(request) {
  const body = await request.json();
  const response = await handleUpload({
    body,
    request,
    onBeforeGenerateToken: async (pathname) => ({
      allowedContentTypes: ['image/*', 'video/*'],
      maximumSizeInBytes: 100 * 1024 * 1024, // 100 MB
      addRandomSuffix: true,
    }),
    onUploadCompleted: async ({ blob, tokenPayload }) => {
      // Update database with blob.url
      // NOTE: Does not work on localhost -- use ngrok for local dev
    },
  });
  return Response.json(response);
}
```

### Caching Behavior

- CDN caches all blobs up to 1 month by default (configurable via `cacheControlMaxAge`).
- After delete/overwrite, up to **60 seconds** for CDN cache invalidation.
- Browser caches persist independently -- append a query param (`?v=timestamp`) to bust.
- **Best practice**: Treat blobs as immutable. Create new pathnames instead of overwriting.

### Conditional Writes (Optimistic Concurrency)

```js
import { head, put, BlobPreconditionFailedError } from '@vercel/blob';

const metadata = await head('config.json');
try {
  await put('config.json', newData, {
    access: 'private',
    allowOverwrite: true,
    ifMatch: metadata.etag, // only succeeds if unchanged
  });
} catch (e) {
  if (e instanceof BlobPreconditionFailedError) { /* conflict */ }
}
```

Available on `put()`, `copy()`, and `del()`.

### Key Limits

- Server upload body limit: **4.5 MB** (use client uploads for larger files)
- Max file size: **5 TB** (via multipart)
- Multipart part minimum: **5 MB** per part (except last)
- Region: chosen at store creation, **cannot be changed**
- Access mode (private/public): **cannot be changed** after creation
- Deletes: free; `list`/`put`/`copy`/`upload` count as billed operations
- Dashboard browsing counts toward operation limits

---

## Edge Config

Global key-value store optimized for ultra-low-latency reads. Data is replicated to all Vercel CDN regions. Ideal for data read often, updated rarely.

### Setup

```bash
npm i @vercel/edge-config
```

Create in Dashboard (Storage > Create Database > Edge Config). Pull env var:

```bash
vercel env pull  # provides EDGE_CONFIG (connection string)
```

### SDK Reference (`@vercel/edge-config`)

The SDK is **read-only**. Writes require the Vercel REST API.

```js
import { get, getAll, has, digest } from '@vercel/edge-config';

// Read single value
const flag = await get('feature_new_ui');

// Read multiple values (counts as 1 read)
const items = await getAll(['feature_new_ui', 'maintenance_mode']);

// Read all values
const everything = await getAll();

// Check key existence
const exists = await has('feature_new_ui');

// Check config version (hash)
const version = await digest();
```

#### Multiple Edge Configs

```js
import { createClient } from '@vercel/edge-config';

const flags = createClient(process.env.FEATURE_FLAGS_CONFIG);
const redirects = createClient(process.env.REDIRECTS_CONFIG);

const flag = await flags.get('new_ui');
const url = await redirects.get('old_page');
```

### Writing via REST API

```bash
# Create Edge Config
curl -X POST 'https://api.vercel.com/v1/edge-config' \
  -H 'Authorization: Bearer $VERCEL_API_TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{"slug": "my-config"}'

# Update items (PATCH)
curl -X PATCH 'https://api.vercel.com/v1/edge-config/{id}/items' \
  -H 'Authorization: Bearer $VERCEL_API_TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{
    "items": [
      {"operation": "upsert", "key": "feature_flag", "value": true},
      {"operation": "delete", "key": "old_key"}
    ]
  }'
```

Operations: `create`, `update`, `upsert`, `delete`. If any operation in a PATCH fails, the entire request fails.

### Usage in Middleware

```js
import { NextResponse } from 'next/server';
import { get } from '@vercel/edge-config';

export const config = { matcher: '/welcome' };

export async function middleware() {
  const greeting = await get('greeting');
  return NextResponse.json(greeting);
}
```

### Limits by Plan

| Resource | Hobby | Pro | Enterprise |
|----------|-------|-----|-----------|
| Max store size | 8 KB | 64 KB | 512 KB+ |
| Max stores (total) | 1 | 3 | 10+ |
| Max stores per project | 1 | 3 | 3 |
| Key name max length | 256 chars | 256 chars | 256 chars |
| Write propagation | up to 10s | up to 10s | up to 10s |
| Backup retention | 7 days | 90 days | 365 days |

Key names must match `[A-Za-z0-9_-]+`.

### Optimization Tips

- Use `getAll(['a', 'b'])` instead of separate `get()` calls -- counts as 1 read.
- Fewer large stores > many small stores (better latency).
- SDK reads are optimized only on Vercel deployments (local dev uses public internet, higher latency).
- For frequently updated data, consider Upstash Redis instead.

---

## Marketplace Storage (Postgres, KV, NoSQL)

For relational databases, Redis, and other storage, use the Vercel Marketplace:

| Need | Provider | SDK |
|------|----------|-----|
| Postgres | Neon, Supabase | Provider's own SDK |
| Redis/KV | Upstash | `@upstash/redis` |
| NoSQL | MongoDB, DynamoDB | Provider's SDK |
| Vector DB | Pinecone, etc. | Provider's SDK |

Provision from Dashboard or CLI. Vercel auto-injects credentials as environment variables.

---

## Best Practices

### Data Locality
- Deploy databases in regions closest to your Functions to minimize roundtrips.
- Blob store region is set at creation time and cannot be changed.

### Caching Strategy
- Use CDN cache headers and ISR for data fetched from stores.
- Middleware runs before the CDN cache layer and cannot use cache-control headers.
- Treat blobs as immutable when possible for best cache performance.

### Common Pitfalls

| Pitfall | Details |
|---------|---------|
| Blob access mode is permanent | Private vs public cannot be changed after store creation |
| Blob region is permanent | Choose carefully at store creation |
| Edge Config is not for frequent writes | Up to 10s propagation delay; use Redis for dynamic data |
| Edge Config size is small | Max 8 KB (Hobby) to 512 KB (Enterprise) |
| Server upload body limit | 4.5 MB max; use client uploads for larger files |
| Dashboard browsing costs operations | Listing/viewing blobs in dashboard counts toward billing |
| Blob overwrites need 60s to propagate | CDN + browser caches may serve stale content |
| `onUploadCompleted` won't fire on localhost | Use ngrok or similar tunnel for local client upload testing |
| Edge Config local reads are slower | Optimized reads only work on Vercel deployments |
