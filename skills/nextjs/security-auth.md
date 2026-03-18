# Next.js: Security & Authentication
Based on Next.js documentation (App Router).

## Authentication Flow

Three concepts: **Authentication** (verify identity), **Session Management** (track auth state across requests), **Authorization** (control access to routes/data).

### Sign-up / Login with Server Actions

Use `<form>` with Server Actions and `useActionState` for secure server-side auth logic. Validate with Zod on the server, hash passwords with bcrypt, then create a session and redirect.

```tsx
// app/actions/auth.ts
export async function signup(state: FormState, formData: FormData) {
  // 1. Validate with Zod schema
  const validatedFields = SignupFormSchema.safeParse({
    name: formData.get('name'),
    email: formData.get('email'),
    password: formData.get('password'),
  })
  if (!validatedFields.success) {
    return { errors: validatedFields.error.flatten().fieldErrors }
  }

  // 2. Hash password and insert user
  const { name, email, password } = validatedFields.data
  const hashedPassword = await bcrypt.hash(password, 10)
  const data = await db.insert(users)
    .values({ name, email, password: hashedPassword })
    .returning({ id: users.id })

  if (!data[0]) return { message: 'An error occurred.' }

  // 3. Create session and redirect
  await createSession(data[0].id)
  redirect('/profile')
}
```

Client form uses `useActionState` for pending state and server validation errors:

```tsx
// app/ui/signup-form.tsx
'use client'
import { useActionState } from 'react'
import { signup } from '@/app/actions/auth'

export default function SignupForm() {
  const [state, action, pending] = useActionState(signup, undefined)
  return (
    <form action={action}>
      <input name="name" />
      {state?.errors?.name && <p>{state.errors.name}</p>}
      <input name="email" type="email" />
      {state?.errors?.email && <p>{state.errors.email}</p>}
      <input name="password" type="password" />
      {state?.errors?.password && (
        <ul>{state.errors.password.map((e) => <li key={e}>{e}</li>)}</ul>
      )}
      <button disabled={pending} type="submit">Sign Up</button>
    </form>
  )
}
```

## Session Management

Two strategies:

| Strategy | Storage | Pros | Cons |
|----------|---------|------|------|
| **Stateless (JWT)** | Cookie | Simple, no DB calls per request | Less secure if misconfigured |
| **Database** | DB + encrypted session ID cookie | More secure, revocable | More complex, uses server resources |

### Stateless Sessions (JWT with Jose)

```ts
// app/lib/session.ts
import 'server-only'
import { SignJWT, jwtVerify } from 'jose'
import { cookies } from 'next/headers'

const secretKey = process.env.SESSION_SECRET
const encodedKey = new TextEncoder().encode(secretKey)

export async function encrypt(payload: SessionPayload) {
  return new SignJWT(payload)
    .setProtectedHeader({ alg: 'HS256' })
    .setIssuedAt()
    .setExpirationTime('7d')
    .sign(encodedKey)
}

export async function decrypt(session: string | undefined = '') {
  try {
    const { payload } = await jwtVerify(session, encodedKey, {
      algorithms: ['HS256'],
    })
    return payload
  } catch (error) {
    console.log('Failed to verify session')
  }
}

export async function createSession(userId: string) {
  const expiresAt = new Date(Date.now() + 7 * 24 * 60 * 60 * 1000)
  const session = await encrypt({ userId, expiresAt })
  const cookieStore = await cookies()
  cookieStore.set('session', session, {
    httpOnly: true,
    secure: true,
    expires: expiresAt,
    sameSite: 'lax',
    path: '/',
  })
}

export async function deleteSession() {
  const cookieStore = await cookies()
  cookieStore.delete('session')
}
```

Generate secret: `openssl rand -base64 32`

Cookie options: **httpOnly** (no JS access), **secure** (HTTPS only), **sameSite: 'lax'**, **expires** or **Max-Age**, **path: '/'**.

### Database Sessions

Store session in DB, encrypt the session ID into a cookie for optimistic middleware checks. More secure (revocable, trackable) but requires DB calls for full verification.

```ts
export async function createSession(id: number) {
  const expiresAt = new Date(Date.now() + 7 * 24 * 60 * 60 * 1000)
  const data = await db.insert(sessions).values({ userId: id, expiresAt })
    .returning({ id: sessions.id })
  const session = await encrypt({ sessionId: data[0].id, expiresAt })
  const cookieStore = await cookies()
  cookieStore.set('session', session, {
    httpOnly: true, secure: true, expires: expiresAt,
    sameSite: 'lax', path: '/',
  })
}
```

## Authorization

### Data Access Layer (DAL)

Centralize authorization in a DAL. Use `cache()` to deduplicate calls within a render pass.

```ts
// app/lib/dal.ts
import 'server-only'
import { cache } from 'react'
import { cookies } from 'next/headers'
import { decrypt } from '@/app/lib/session'
import { redirect } from 'next/navigation'

export const verifySession = cache(async () => {
  const cookie = (await cookies()).get('session')?.value
  const session = await decrypt(cookie)
  if (!session?.userId) {
    redirect('/login')
  }
  return { isAuth: true, userId: session.userId }
})

export const getUser = cache(async () => {
  const session = await verifySession()
  if (!session) return null
  try {
    const data = await db.query.users.findMany({
      where: eq(users.id, session.userId),
      columns: { id: true, name: true, email: true },
    })
    return data[0]
  } catch (error) {
    console.log('Failed to fetch user')
    return null
  }
})
```

### Middleware Auth Checks

Use middleware for optimistic (cookie-only) route protection. Never do DB calls in middleware.

```ts
// middleware.ts
import { NextRequest, NextResponse } from 'next/server'
import { decrypt } from '@/app/lib/session'
import { cookies } from 'next/headers'

const protectedRoutes = ['/dashboard']
const publicRoutes = ['/login', '/signup', '/']

export default async function middleware(req: NextRequest) {
  const path = req.nextUrl.pathname
  const isProtectedRoute = protectedRoutes.includes(path)
  const isPublicRoute = publicRoutes.includes(path)

  const cookie = (await cookies()).get('session')?.value
  const session = await decrypt(cookie)

  if (isProtectedRoute && !session?.userId) {
    return NextResponse.redirect(new URL('/login', req.nextUrl))
  }
  if (isPublicRoute && session?.userId &&
      !req.nextUrl.pathname.startsWith('/dashboard')) {
    return NextResponse.redirect(new URL('/dashboard', req.nextUrl))
  }
  return NextResponse.next()
}

export const config = {
  matcher: ['/((?!api|_next/static|_next/image|.*\\.png$).*)'],
}
```

**Important:** Middleware is not the only line of defense. Always verify authorization close to data access (in the DAL).

### Protecting Server Actions

Treat Server Actions as public API endpoints. Always verify authorization.

```ts
'use server'
import { verifySession } from '@/app/lib/dal'

export async function serverAction(formData: FormData) {
  const session = await verifySession()
  if (session?.user?.role !== 'admin') {
    return null
  }
  // Proceed with the action
}
```

### Protecting Route Handlers

```ts
import { verifySession } from '@/app/lib/dal'

export async function GET() {
  const session = await verifySession()
  if (!session) return new Response(null, { status: 401 })
  if (session.user.role !== 'admin') return new Response(null, { status: 403 })
  // Continue for authorized users
}
```

### Role-Based Access in Server Components

```tsx
import { verifySession } from '@/app/lib/dal'

export default async function Dashboard() {
  const session = await verifySession()
  if (session?.user?.role === 'admin') return <AdminDashboard />
  if (session?.user?.role === 'user') return <UserDashboard />
  redirect('/login')
}
```

**Avoid auth checks in layouts.** Layouts don't re-render on navigation (partial rendering). Check auth in page components or leaf components instead.

### Data Transfer Objects (DTOs)

Return only necessary fields to prevent data leaks:

```ts
// app/lib/dto.ts
import 'server-only'
import { getUser } from '@/app/lib/dal'

export async function getProfileDTO(slug: string) {
  const [rows] = await sql`SELECT * FROM user WHERE slug = ${slug}`
  const user = rows[0]
  const currentUser = await getUser(user.id)

  return {
    username: canSeeUsername(currentUser) ? user.username : null,
    phonenumber: canSeePhoneNumber(currentUser, user.team) ? user.phonenumber : null,
  }
}
```

## Auth Interrupts (Experimental, v15.1.0+)

Enable `forbidden()` and `unauthorized()` functions with custom error pages.

### Configuration

```js
// next.config.js
module.exports = {
  experimental: {
    authInterrupts: true,
  },
}
```

### `unauthorized()` -- 401 Not Authenticated

Import from `next/navigation`. Renders `unauthorized.tsx` with a 401 status. Cannot be called in root layout.

```tsx
// app/dashboard/page.tsx
import { verifySession } from '@/app/lib/dal'
import { unauthorized } from 'next/navigation'

export default async function DashboardPage() {
  const session = await verifySession()
  if (!session) {
    unauthorized()
  }
  return <div>Dashboard</div>
}
```

```tsx
// app/unauthorized.tsx
import Login from '@/app/components/Login'

export default function Unauthorized() {
  return (
    <main>
      <h1>401 - Unauthorized</h1>
      <p>Please log in to access this page.</p>
      <Login />
    </main>
  )
}
```

### `forbidden()` -- 403 Not Authorized

Import from `next/navigation`. Renders `forbidden.tsx` with a 403 status. Cannot be called in root layout.

```tsx
// app/admin/page.tsx
import { verifySession } from '@/app/lib/dal'
import { forbidden } from 'next/navigation'

export default async function AdminPage() {
  const session = await verifySession()
  if (session.role !== 'admin') {
    forbidden()
  }
  return <h1>Admin Dashboard</h1>
}
```

```tsx
// app/forbidden.tsx
import Link from 'next/link'

export default function Forbidden() {
  return (
    <div>
      <h2>Forbidden</h2>
      <p>You are not authorized to access this resource.</p>
      <Link href="/">Return Home</Link>
    </div>
  )
}
```

Both functions work in Server Components, Server Actions, and Route Handlers. File conventions (`forbidden.tsx`, `unauthorized.tsx`) accept no props.

## Content Security Policy (CSP)

### Nonce-Based CSP via Middleware

Every request generates a fresh nonce. Requires dynamic rendering. Add `'unsafe-eval'` in dev only (React debugging).

```ts
// middleware.ts
import { NextRequest, NextResponse } from 'next/server'

export function middleware(request: NextRequest) {
  const nonce = Buffer.from(crypto.randomUUID()).toString('base64')
  const isDev = process.env.NODE_ENV === 'development'
  const cspHeader = `
    default-src 'self';
    script-src 'self' 'nonce-${nonce}' 'strict-dynamic'${isDev ? " 'unsafe-eval'" : ''};
    style-src 'self' 'nonce-${nonce}';
    img-src 'self' blob: data:;
    font-src 'self';
    object-src 'none';
    base-uri 'self';
    form-action 'self';
    frame-ancestors 'none';
    upgrade-insecure-requests;
  `
  const cspValue = cspHeader.replace(/\s{2,}/g, ' ').trim()
  const requestHeaders = new Headers(request.headers)
  requestHeaders.set('x-nonce', nonce)
  requestHeaders.set('Content-Security-Policy', cspValue)
  const response = NextResponse.next({ request: { headers: requestHeaders } })
  response.headers.set('Content-Security-Policy', cspValue)
  return response
}

export const config = {
  matcher: [{
    source: '/((?!api|_next/static|_next/image|favicon.ico).*)',
    missing: [
      { type: 'header', key: 'next-router-prefetch' },
      { type: 'header', key: 'purpose', value: 'prefetch' },
    ],
  }],
}
```

**How nonces work:** Middleware sets `Content-Security-Policy` and `x-nonce` headers. Next.js auto-extracts the nonce and applies it to framework scripts, page bundles, and inline styles. For third-party scripts, read the nonce from headers:

```tsx
import { headers } from 'next/headers'
import Script from 'next/script'

export default async function Page() {
  const nonce = (await headers()).get('x-nonce')
  return <Script src="https://www.googletagmanager.com/gtag/js" strategy="afterInteractive" nonce={nonce} />
}
```

Force dynamic rendering with `await connection()` from `next/server` if needed.

### CSP Without Nonces (Static-Compatible)

For apps that don't need strict inline script control, set CSP in `next.config.js` with `'unsafe-inline'`:

```js
// next.config.js
const cspHeader = `
  default-src 'self'; script-src 'self' 'unsafe-inline';
  style-src 'self' 'unsafe-inline'; img-src 'self' blob: data:;
  font-src 'self'; object-src 'none'; base-uri 'self';
  form-action 'self'; frame-ancestors 'none'; upgrade-insecure-requests;
`
module.exports = {
  async headers() {
    return [{
      source: '/(.*)',
      headers: [{ key: 'Content-Security-Policy', value: cspHeader.replace(/\n/g, '') }],
    }]
  },
}
```

### Subresource Integrity (SRI) -- Experimental

Hash-based CSP alternative that preserves static generation. Webpack + App Router only.

```js
// next.config.js
module.exports = {
  experimental: {
    sri: { algorithm: 'sha256' },  // or 'sha384', 'sha512'
  },
}
```

## Data Security

### Server Actions Security

Server Actions create public HTTP endpoints. Built-in protections:
- **Secure action IDs**: Encrypted, non-deterministic, recalculated between builds.
- **Dead code elimination**: Unused Server Actions removed from client bundle.
- **CSRF protection**: `POST`-only + Origin/Host header comparison.
- **Closure encryption**: Closed-over variables automatically encrypted with per-build keys.

For self-hosted multi-server deployments, set a consistent encryption key:

```bash
export NEXT_SERVER_ACTIONS_ENCRYPTION_KEY=$(openssl rand -base64 32)
```

Configure allowed origins for reverse proxy setups:

```js
// next.config.js
module.exports = {
  experimental: {
    serverActions: {
      allowedOrigins: ['my-proxy.com', '*.my-proxy.com'],
    },
  },
}
```

### Preventing Data Leaks

- **Always validate on the server.** Never trust client input (searchParams, form data, headers). Re-verify auth from cookies/session, not from query params.
- **Use `server-only` package** (`import 'server-only'`) to cause build errors if server code is imported in client modules.
- **No mutations during rendering.** Use Server Actions for mutations. Never delete cookies or revalidate cache as a render side effect.
- **Only `NEXT_PUBLIC_*` env vars** are exposed to the client. Keep `process.env` access inside the DAL.

### Taint API (Experimental)

Prevent objects/values from being passed to Client Components. Enable with `experimental: { taint: true }` in `next.config.js`.

- `experimental_taintObjectReference(obj, message)` -- blocks entire objects
- `experimental_taintUniqueValue(value, message)` -- blocks specific values (tokens, keys)

Additional safety layer on top of DAL filtering. Not a replacement for proper data sanitization.

## Security Audit Checklist

- **Data Access Layer**: Isolated? DB packages and env vars not imported outside it?
- **`"use client"` files**: Props expecting private data? Type signatures overly broad?
- **`"use server"` files**: Arguments validated? User re-authorized in every action?
- **`/[param]/` routes**: Dynamic params validated and sanitized?
- **`middleware.ts` and `route.ts`**: Audited with traditional techniques? Pen-tested?

## Auth Libraries

NextAuth.js, Clerk, Auth0, Better Auth, Supabase, Kinde, Logto, Stack Auth, WorkOS, Stytch, Descope, Ory.

Session management libraries: iron-session, Jose.
