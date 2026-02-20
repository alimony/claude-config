# Django 6.0 Testing

## Core Concepts

| Class | DB Access | Transactions | Speed | Use When |
|-------|-----------|-------------|-------|----------|
| `SimpleTestCase` | No | N/A | Fastest | No database needed |
| `TransactionTestCase` | Yes | Real commit/rollback | Slowest | Testing transaction behavior |
| `TestCase` | Yes | Wrapped + rolled back | Fast | Most database tests |
| `LiveServerTestCase` | Yes | Real | Slow | Selenium / browser tests |

**Critical rule:** Use `django.test.TestCase`, not `unittest.TestCase`, for any test touching the database.

---

## Test Case Patterns

### Basic Test with Database

```python
from django.test import TestCase

class ArticleTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.article = Article.objects.create(title="Hello")

    def test_str(self):
        self.assertEqual(str(self.article), "Hello")
```

**Do this:** Use `setUpTestData` for read-only fixtures shared across methods.

### Testing Views with the Test Client

```python
class ArticleViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="john", password="secret")
        cls.article = Article.objects.create(title="Hello", author=cls.user)

    def test_list_page(self):
        response = self.client.get("/articles/")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "article_list.html")
        self.assertContains(response, "Hello")

    def test_create_requires_login(self):
        response = self.client.get("/articles/create/")
        self.assertRedirects(response, "/accounts/login/?next=/articles/create/")

    def test_authenticated_create(self):
        self.client.force_login(self.user)
        response = self.client.post("/articles/create/", {"title": "New"})
        self.assertEqual(Article.objects.count(), 2)
```

### Testing with RequestFactory

```python
from django.test import RequestFactory

class MyViewTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username="jacob", password="secret")

    def test_authenticated(self):
        request = self.factory.get("/my-url/")
        request.user = self.user
        response = MyView.as_view()(request)
        self.assertEqual(response.status_code, 200)
```

---

## Test Client Reference

```python
# GET with query parameters
response = self.client.get("/search/", query_params={"q": "django"})

# POST form data
response = self.client.post("/login/", {"username": "john", "password": "secret"})

# POST JSON
response = self.client.post("/api/items/", {"name": "Widget"}, content_type="application/json")

# Follow redirects
response = self.client.get("/old-url/", follow=True)

# Authentication
self.client.force_login(user)  # Preferred in tests
self.client.login(username="fred", password="secret")
self.client.logout()
```

---

## Key Assertions

```python
# Content
self.assertContains(response, "Welcome")
self.assertContains(response, "item", count=3)
self.assertNotContains(response, "Error")

# Templates
self.assertTemplateUsed(response, "index.html")

# Redirects
self.assertRedirects(response, "/new-url/")

# Forms
form = MyForm(data={"email": "bad"})
self.assertFormError(form, "email", "Enter a valid email address.")

# HTML
self.assertHTMLEqual('<p class="x" id="y">Hi</p>', '<p id="y" class="x">Hi</p>')
self.assertInHTML("<li>Item</li>", response.content.decode())

# QuerySets
self.assertQuerySetEqual(qs, [self.article1, self.article2])

# Query count
with self.assertNumQueries(2):
    list(Article.objects.all())
    list(Author.objects.all())
```

---

## Settings Override

```python
from django.test import TestCase, override_settings

@override_settings(LOGIN_URL="/custom-login/")
class MyTests(TestCase):
    def test_redirect(self):
        response = self.client.get("/protected/")
        self.assertRedirects(response, "/custom-login/?next=/protected/")

    def test_with_context_manager(self):
        with self.settings(LANGUAGE_CODE="fr"):
            response = self.client.get("/")
```

---

## Email Testing

```python
from django.core import mail

class EmailTests(TestCase):
    def test_send_welcome(self):
        send_welcome_email("user@example.com")
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "Welcome!")
```

---

## Testing on_commit Callbacks

```python
class ContactTests(TestCase):
    def test_email_sent_on_commit(self):
        with self.captureOnCommitCallbacks(execute=True) as callbacks:
            self.client.post("/contact/", {"message": "Hi"})
        self.assertEqual(len(mail.outbox), 1)
```

---

## Running Tests

```bash
./manage.py test                           # All tests
./manage.py test myapp                     # Specific app
./manage.py test myapp.tests.test_views    # Specific module
./manage.py test --parallel                # Parallel execution
./manage.py test --keepdb                  # Reuse test database
./manage.py test --failfast                # Stop on first failure
./manage.py test --shuffle                 # Randomize order
./manage.py test -k pattern               # Match name pattern
```

---

## Performance Tips

1. Use `setUpTestData` instead of `setUp` for shared read-only data.
2. Use `--keepdb` to skip database creation/destruction.
3. Use `--parallel` for large test suites.
4. Use faster password hashing in test settings:
   ```python
   PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
   ```
5. Use `force_login` instead of `login` when auth flow is not under test.

---

## Common Pitfalls

1. **Module-level DB queries** fail because test database doesn't exist during import.
2. **Test ordering dependencies** -- tests should be independent. Use `--shuffle`.
3. **Using `TestCase` for transaction tests** -- use `TransactionTestCase` or `captureOnCommitCallbacks`.
4. **Forgetting `view.setup(request)`** when testing CBV methods directly.
5. **Modifying `setUpTestData` objects** -- keep them read-only in test methods.
6. **DEBUG is always False** in tests.
7. **Caches are not cleared** between tests.
