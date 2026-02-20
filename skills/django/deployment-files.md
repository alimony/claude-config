# Django: Deployment & File Handling

Based on Django 6.0 documentation.

## Deployment Overview

| Interface | Standard | Async Support | Use When |
|-----------|----------|---------------|----------|
| **WSGI** | PEP 3333 | No (sync only) | Traditional Django apps |
| **ASGI** | ASGI spec | Yes | WebSockets, async views, real-time |

### WSGI

```python
# myproject/wsgi.py
import os
from django.core.wsgi import get_wsgi_application
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "myproject.settings")
application = get_wsgi_application()
```

```bash
# Gunicorn (recommended)
gunicorn myproject.wsgi

# uWSGI
uwsgi --module=mysite.wsgi:application --master --processes=5
```

### ASGI

```python
# myproject/asgi.py
import os
from django.core.asgi import get_asgi_application
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "myproject.settings")
application = get_asgi_application()
```

```bash
# Uvicorn
uvicorn myproject.asgi:application

# Production with Gunicorn
gunicorn myproject.asgi:application -k uvicorn_worker.UvicornWorker

# Daphne
daphne myproject.asgi:application
```

---

## Production Checklist

```python
DEBUG = False
SECRET_KEY = os.environ["SECRET_KEY"]
ALLOWED_HOSTS = ["example.com", "www.example.com"]
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
```

Run `manage.py check --deploy` to audit.

---

## Static Files

```python
STATIC_URL = "static/"
STATIC_ROOT = "/var/www/example.com/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
```

```django
{% load static %}
<img src="{% static 'my_app/example.jpg' %}" alt="Example">
```

### Namespace Static Files

```
# DO: namespace with app name
my_app/static/my_app/style.css

# DON'T: bare files collide
my_app/static/style.css
```

```bash
python manage.py collectstatic
```

### Development Media Files

```python
# urls.py (development only)
from django.conf import settings
from django.conf.urls.static import static
urlpatterns = [...] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

---

## File Handling

### Model File Fields

```python
class Document(models.Model):
    upload = models.FileField(upload_to="documents/")
    photo = models.ImageField(upload_to="photos/")
```

```python
doc.upload.name    # "documents/report.pdf"
doc.upload.path    # "/media/documents/report.pdf"
doc.upload.url     # "/media/documents/report.pdf"
doc.upload.size    # 204800
```

### Saving Files to Models

```python
from django.core.files import File
from django.core.files.base import ContentFile

# From disk
with open("/some/file.pdf", "rb") as f:
    doc.upload = File(f, name="file.pdf")
    doc.save()

# From memory
doc.upload.save("report.txt", ContentFile(b"file contents"), save=True)
```

### Storage API

```python
from django.core.files.storage import default_storage

path = default_storage.save("uploads/test.txt", ContentFile(b"hello"))
default_storage.exists(path)
default_storage.url(path)
default_storage.delete(path)
```

### STORAGES Setting

```python
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}
```

### Custom Storage Per Field

```python
from django.core.files.storage import FileSystemStorage
private_storage = FileSystemStorage(location="/secure/uploads")

class SecureDocument(models.Model):
    file = models.FileField(storage=private_storage)
```

---

## File Uploads

```python
def handle_upload(request):
    uploaded = request.FILES["document"]
    uploaded.name          # "report.pdf"
    uploaded.size          # bytes
    uploaded.content_type  # "application/pdf"

    # Stream to destination (preferred for large files)
    with open(f"/uploads/{uploaded.name}", "wb") as dest:
        for chunk in uploaded.chunks():
            dest.write(chunk)
```

Never trust `content_type` from uploads -- validate actual file content.

---

## Upgrading Django

1. Read release notes for every version between current and target
2. Upgrade incrementally through each feature release
3. Enable deprecation warnings: `python -Wa manage.py test`
4. Fix all deprecation warnings before upgrading
5. Run full test suite after upgrade
6. **Clear your cache** after upgrading
