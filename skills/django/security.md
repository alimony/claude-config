# Django 6.0 Security

## CSRF Protection

### Template Usage

```html
<form method="post">{% csrf_token %}
    <input type="text" name="username">
    <button type="submit">Submit</button>
</form>
```

### AJAX Requests

```javascript
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
        const cookies = document.cookie.split(";");
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === name + "=") {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
const csrftoken = getCookie("csrftoken");

fetch("/api/endpoint/", {
    method: "POST",
    headers: { "X-CSRFToken": csrftoken },
    mode: "same-origin",
});
```

### CSRF Decorators

| Decorator | Purpose |
|-----------|---------|
| `@csrf_exempt` | Disable CSRF checks for a view |
| `@csrf_protect` | Enable CSRF checks for a view |
| `@requires_csrf_token` | Ensure `{% csrf_token %}` works without full middleware |
| `@ensure_csrf_cookie` | Force the CSRF cookie to be set |

### Key CSRF Settings

| Setting | Default | Notes |
|---------|---------|-------|
| `CSRF_COOKIE_SECURE` | `False` | Set `True` in production |
| `CSRF_COOKIE_HTTPONLY` | `False` | If `True`, JS cannot read cookie |
| `CSRF_USE_SESSIONS` | `False` | Store token in session instead of cookie |
| `CSRF_TRUSTED_ORIGINS` | `[]` | Allow cross-origin unsafe requests |

---

## Content Security Policy (CSP) -- New in Django 6.0

```python
MIDDLEWARE = [..., "django.middleware.csp.ContentSecurityPolicyMiddleware", ...]
```

```python
from django.utils.csp import CSP

SECURE_CSP = {
    "default-src": [CSP.SELF],
    "script-src": [CSP.SELF, CSP.NONCE],
    "style-src": [CSP.SELF, CSP.NONCE],
    "img-src": [CSP.SELF, "https://cdn.example.com"],
}
```

### Nonces in Templates

```python
# Add context processor
"django.template.context_processors.csp",
```

```html
<script nonce="{{ csp_nonce }}">console.log("allowed");</script>
```

**Caching pitfall:** Nonces are unique per request. Never cache pages that use `{{ csp_nonce }}`.

### Per-View Overrides

```python
from django.views.decorators.csp import csp_override

@csp_override({"default-src": [CSP.SELF], "img-src": [CSP.SELF, "data:"]})
def special_view(request): ...

@csp_override({})  # Disable CSP entirely for one view
def legacy_view(request): ...
```

Overrides **replace** the global policy completely; they do not merge.

---

## XSS Protection

Django templates **auto-escape** HTML characters by default.

```html
<!-- DO: let auto-escaping work -->
<p>{{ user_input }}</p>

<!-- DON'T: disable escaping without sanitization -->
<p>{{ user_input|safe }}</p>

<!-- DON'T: use in attribute context without quoting -->
<div class={{ var }}>  <!-- vulnerable -->
<div class="{{ var }}">  <!-- safer -->
```

---

## SQL Injection Protection

```python
# Safe: QuerySet API -- parameterized automatically
User.objects.filter(email=user_input)

# Safe: raw SQL with params
User.objects.raw("SELECT * FROM auth_user WHERE email = %s", [user_input])

# DANGEROUS: string formatting
cursor.execute(f"SELECT * FROM auth_user WHERE email = '{user_input}'")
```

---

## Cryptographic Signing

```python
from django.core.signing import Signer, TimestampSigner, BadSignature, SignatureExpired

signer = Signer()
signed = signer.sign("My string")
original = signer.unsign(signed)

# Salt for namespace isolation
activation_signer = Signer(salt="account-activation")
reset_signer = Signer(salt="password-reset")

# Time-limited signatures
from datetime import timedelta
signer = TimestampSigner()
token = signer.sign("hello")
value = signer.unsign(token, max_age=timedelta(hours=1))

# Complex data
from django.core import signing
token = signing.dumps({"user_id": 42})
data = signing.loads(token, max_age=3600)
```

---

## Secure Deployment Checklist

```python
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
ALLOWED_HOSTS = ["example.com", "www.example.com"]
SECURE_REFERRER_POLICY = "same-origin"
SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin"
```

---

## Common Pitfalls

1. **CSRF token after login** -- Django rotates the CSRF token on login. Reload the page or re-fetch the token.
2. **`@csrf_exempt` on API views** -- Use proper token-based auth instead.
3. **CSP overrides don't merge** -- `@csp_override` replaces the entire policy.
4. **Caching + nonces** -- Full-page caching serves stale CSP nonces.
5. **`mark_safe()` on user data** -- Completely disables XSS protection.
6. **Missing `ALLOWED_HOSTS`** -- With `DEBUG=False`, an empty list causes 400 errors.
7. **Signing without `salt`** -- Values can be replayed across contexts.

## Security Middleware Order

```python
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.csp.ContentSecurityPolicyMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
```
