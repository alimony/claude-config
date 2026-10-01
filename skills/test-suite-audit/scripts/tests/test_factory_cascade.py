"""factory_cascade.py against real INSERT counts, on a tiny Django project built in tmp_path.

Every check runs the script, and the project's own Python, in a subprocess, so
Django's configuration never reaches this test process.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

from conftest import SCRIPTS_DIR

pytest.importorskip("factory")
pytest.importorskip("django")

SCRIPT = SCRIPTS_DIR / "factory_cascade.py"

SETTINGS = """
SECRET_KEY = "factory-cascade-tests"
INSTALLED_APPS = ["fcapp"]
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
"""

MODELS = """
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


class Org(models.Model):
    name = models.CharField(max_length=100)


class Account(models.Model):
    org = models.ForeignKey(Org, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, default="a")


class Member(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE)


class Project(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    owner = models.ForeignKey(Member, on_delete=models.CASCADE, null=True)


class Tag(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)


class User(models.Model):
    username = models.CharField(max_length=100)


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)


class Audit(models.Model):
    note = models.CharField(max_length=100)


class SignalMember(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE)


@receiver(post_save, sender=SignalMember)
def _audit(sender, instance, created, **kwargs):
    if created:
        Audit.objects.create(note="member created")


class Invoice(models.Model):
    org = models.ForeignKey(Org, on_delete=models.CASCADE)
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
"""

FACTORIES = """
import factory
from factory.django import DjangoModelFactory

from . import models as m


class OrgFactory(DjangoModelFactory):
    class Meta:
        model = m.Org

    name = factory.Sequence(lambda n: f"org{n}")


class AccountFactory(DjangoModelFactory):
    class Meta:
        model = m.Account

    org = factory.SubFactory(OrgFactory)


class MemberFactory(DjangoModelFactory):
    class Meta:
        model = m.Member

    account = factory.SubFactory(AccountFactory)


class ProjectFactory(DjangoModelFactory):  # unshared parents: 1 + 2 + 3 = 6
    class Meta:
        model = m.Project

    account = factory.SubFactory(AccountFactory)
    owner = factory.SubFactory(MemberFactory)


class SharedProjectFactory(ProjectFactory):  # SubFactory keyword arguments share the account: 4
    owner = factory.SubFactory(MemberFactory, account=factory.SelfAttribute("..account"))


class ClassContextProjectFactory(ProjectFactory):  # class-level deep context shares it too: 4
    owner__account = factory.SelfAttribute("..account")


class MaybeProjectFactory(ProjectFactory):  # Maybe around a SubFactory: 6
    class Params:
        with_owner = True

    owner = factory.Maybe("with_owner", yes_declaration=factory.SubFactory(MemberFactory), no_declaration=None)


class LazyProjectFactory(ProjectFactory):  # a factory call inside LazyAttribute: 6, invisible
    owner = factory.LazyAttribute(lambda o: MemberFactory())


class ListProjectFactory(ProjectFactory):  # factory.List of 3 SubFactories: 6 + 9 = 15
    class Meta:
        exclude = ("members",)

    members = factory.List([factory.SubFactory(MemberFactory) for _ in range(3)])


class TagFactory(DjangoModelFactory):  # the child declares its parent: 1 + 6 = 7
    class Meta:
        model = m.Tag

    project = factory.SubFactory(ProjectFactory)


class ProjectWithTagsFactory(ProjectFactory):  # RelatedFactoryList passes project=the new object: 6 + 2 = 8
    class Meta:
        skip_postgeneration_save = True

    tags = factory.RelatedFactoryList(TagFactory, "project", size=2)


class PostGenProjectFactory(ProjectFactory):  # post_generation that creates rows: 8, flagged
    class Meta:
        skip_postgeneration_save = True

    @factory.post_generation
    def tags(obj, create, extracted, **kwargs):
        if create:
            TagFactory.create_batch(2, project=obj)


class ProfileFactory(DjangoModelFactory):  # factory_boy's documented profile example
    class Meta:
        model = m.Profile

    user = factory.SubFactory("fcapp.factories.UserFactory", profile=None)


class UserFactory(DjangoModelFactory):  # a user and its profile: 2
    class Meta:
        model = m.User
        skip_postgeneration_save = True

    username = factory.Sequence(lambda n: f"user{n}")
    profile = factory.RelatedFactory(ProfileFactory, factory_related_name="user")


class SignalMemberFactory(DjangoModelFactory):  # a post_save signal adds an Audit row: 4, invisible
    class Meta:
        model = m.SignalMember

    account = factory.SubFactory(AccountFactory)


class GetOrCreateOrgFactory(DjangoModelFactory):  # 1 on the first call, flagged
    class Meta:
        model = m.Org
        django_get_or_create = ("name",)

    name = "fixed"


class InvoiceFactory(DjangoModelFactory):  # a shared org through SubFactory keyword arguments: 3
    class Meta:
        model = m.Invoice

    org = factory.SubFactory(OrgFactory)
    account = factory.SubFactory(AccountFactory, org=factory.SelfAttribute("..org"))


class CallableSizeProjectFactory(ProjectFactory):  # a callable size (3): 6 + 3 = 9, flagged
    class Meta:
        skip_postgeneration_save = True

    tags = factory.RelatedFactoryList(TagFactory, "project", size=lambda: 3)
"""

# Ground truth: INSERT statements per create(), each in a transaction that is rolled back.
COUNT_INSERTS = """
import json
import os
import sys

os.environ["DJANGO_SETTINGS_MODULE"] = "fcsettings"
import django

django.setup()
from django.apps import apps
from django.db import connection, transaction

from fcapp import factories

with connection.schema_editor() as editor:
    for model in apps.get_app_config("fcapp").get_models():
        editor.create_model(model)


class Rollback(Exception):
    pass


def inserts(factory_class):
    count = 0

    def wrapper(execute, sql, params, many, context):
        nonlocal count
        if sql.lstrip().upper().startswith("INSERT"):
            count += 1
        return execute(sql, params, many, context)

    with connection.execute_wrapper(wrapper):
        try:
            with transaction.atomic():
                factory_class.create()
                raise Rollback
        except Rollback:
            pass
    return count


print(json.dumps({name: inserts(getattr(factories, name)) for name in sys.argv[1:]}))
"""

EXACT = {
    "OrgFactory", "AccountFactory", "MemberFactory", "ProjectFactory", "SharedProjectFactory",
    "ClassContextProjectFactory", "MaybeProjectFactory", "ListProjectFactory", "TagFactory",
    "ProjectWithTagsFactory", "UserFactory", "ProfileFactory", "GetOrCreateOrgFactory", "InvoiceFactory",
}
BLIND_SPOTS = {"LazyProjectFactory", "PostGenProjectFactory", "SignalMemberFactory", "CallableSizeProjectFactory"}


def clean_env() -> dict:
    env = dict(os.environ)
    env.pop("DJANGO_SETTINGS_MODULE", None)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env


def run(project: Path, *args: str, python: tuple = (sys.executable,)) -> subprocess.CompletedProcess:
    return subprocess.run([*python, str(SCRIPT), *args], cwd=project, capture_output=True, text=True, env=clean_env(), timeout=120)


@pytest.fixture
def project(tmp_path: Path) -> Path:
    root = tmp_path / "fcproject"
    (root / "fcapp").mkdir(parents=True)
    (root / "fcapp" / "__init__.py").write_text("")
    (root / "fcapp" / "models.py").write_text(textwrap.dedent(MODELS))
    (root / "fcapp" / "factories.py").write_text(textwrap.dedent(FACTORIES))
    (root / "fcsettings.py").write_text(textwrap.dedent(SETTINGS))
    (root / "count_inserts.py").write_text(textwrap.dedent(COUNT_INSERTS))
    return root


def estimates(report: dict) -> dict[str, dict]:
    return {entry["factory"].rpartition(".")[2]: entry for entry in report["factories"]}


def test_estimates_match_real_inserts_except_the_documented_blind_spots(project, tmp_path):
    result = run(project, "fcapp.factories", "--settings", "fcsettings", "--json-out", str(tmp_path / "out.json"))
    assert result.returncode == 0, result.stdout + result.stderr
    found = estimates(json.loads((tmp_path / "out.json").read_text()))
    assert set(found) == EXACT | BLIND_SPOTS

    truth = subprocess.run(
        [sys.executable, "count_inserts.py", *sorted(found)], cwd=project, capture_output=True, text=True, env=clean_env(), timeout=120
    )
    assert truth.returncode == 0, truth.stderr
    actual = json.loads(truth.stdout)
    assert {name: found[name]["rows"] for name in EXACT} == {name: actual[name] for name in EXACT}
    for name in BLIND_SPOTS:
        assert found[name]["rows"] < actual[name], name

    # The patterns that the research's first version got wrong.
    assert found["ProjectWithTagsFactory"]["rows"] == 8  # factory_related_name passes the parent in
    assert found["UserFactory"]["rows"] == 2  # factory_boy's own profile example
    assert found["ClassContextProjectFactory"]["rows"] == 4  # class-level deep context
    assert found["ListProjectFactory"]["rows"] == 15  # factory.List adds no row of its own
    assert found["ProjectFactory"]["models"] == {"Account": 2, "Org": 2, "Member": 1, "Project": 1}

    flags = {name: " ".join(entry["flags"]) for name, entry in found.items()}
    assert "post_generation hook" in flags["PostGenProjectFactory"]
    assert "callable size" in flags["CallableSizeProjectFactory"]
    assert "Maybe" in flags["MaybeProjectFactory"]
    assert "get_or_create" in flags["GetOrCreateOrgFactory"]
    assert flags["LazyProjectFactory"] == flags["SignalMemberFactory"] == ""  # invisible, so silent
    assert "factories: 18 in 1 module " in result.stdout
    assert result.stdout.splitlines()[2].split()[:2] == ["15", "fcapp.factories.ListProjectFactory"]


def test_find_reads_text_and_reports_import_errors(project, tmp_path):
    (project / "fcapp" / "broken_factories.py").write_text("import factory\nraise RuntimeError('broken at import')\n\n\nclass BrokenFactory(factory.Factory):\n    pass\n")
    (project / "fcapp" / "helpers.py").write_text("class NotAFactory:\n    pass\n")
    result = run(project, "--find", ".", "--settings", "fcsettings", "--json-out", str(tmp_path / "out.json"))
    assert result.returncode == 0, result.stdout + result.stderr
    report = json.loads((tmp_path / "out.json").read_text())
    assert report["modules"] == ["fcapp.broken_factories", "fcapp.factories"]
    assert report["import_errors"] == {"fcapp.broken_factories": "RuntimeError: broken at import"}
    assert len(report["factories"]) == 18


def test_without_settings_reports_the_missing_django_setup(project):
    result = run(project, "fcapp.factories")
    assert result.returncode == 1, result.stdout + result.stderr
    assert "import errors: 1" in result.stdout and "ImproperlyConfigured" in result.stdout
    assert "hint: pass --settings" in result.stdout


def test_without_factory_boy_says_which_python_to_use(project):
    result = run(project, "fcapp.factories", python=(sys.executable, "-S"))  # -S: no site-packages
    assert result.returncode == 2
    assert "run this script with the project's Python" in result.stdout


SA_FACTORIES = """
import factory
from factory.alchemy import SQLAlchemyModelFactory
from sqlalchemy import ForeignKey, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, scoped_session, sessionmaker


class Base(DeclarativeBase):
    pass


class Org(Base):
    __tablename__ = "org"
    id: Mapped[int] = mapped_column(primary_key=True)


class Account(Base):
    __tablename__ = "account"
    id: Mapped[int] = mapped_column(primary_key=True)
    org_id: Mapped[int] = mapped_column(ForeignKey("org.id"))
    org = relationship(Org)


class Member(Base):
    __tablename__ = "member"
    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("account.id"))
    account = relationship(Account)
    org_id: Mapped[int] = mapped_column(ForeignKey("org.id"))
    org = relationship(Org)


engine = create_engine("sqlite://")
Base.metadata.create_all(engine)
Session = scoped_session(sessionmaker(bind=engine))


class OrgFactory(SQLAlchemyModelFactory):
    class Meta:
        model = Org
        sqlalchemy_session = Session
        sqlalchemy_session_persistence = "flush"


class AccountFactory(SQLAlchemyModelFactory):
    class Meta:
        model = Account
        sqlalchemy_session = Session
        sqlalchemy_session_persistence = "flush"

    org = factory.SubFactory(OrgFactory)


class MemberFactory(SQLAlchemyModelFactory):  # an unshared org: 1 + 2 + 1 = 4
    class Meta:
        model = Member
        sqlalchemy_session = Session
        sqlalchemy_session_persistence = "flush"

    account = factory.SubFactory(AccountFactory)
    org = factory.SubFactory(OrgFactory)


class SharedMemberFactory(MemberFactory):  # a shared org: 3
    org = factory.SelfAttribute("account.org")
"""

SA_COUNT_INSERTS = """
import json
import sys

from sqlalchemy import event

import safactories

count = {"inserts": 0}


@event.listens_for(safactories.engine, "before_cursor_execute")
def _count(conn, cursor, statement, parameters, context, executemany):
    if statement.lstrip().upper().startswith("INSERT"):
        count["inserts"] += 1


actual = {}
for name in sys.argv[1:]:
    count["inserts"] = 0
    getattr(safactories, name).create()
    safactories.Session.rollback()
    actual[name] = count["inserts"]
print(json.dumps(actual))
"""


def test_sqlalchemy_factories_need_no_django_settings(tmp_path):
    pytest.importorskip("sqlalchemy")
    root = tmp_path / "saproject"
    root.mkdir()
    (root / "safactories.py").write_text(textwrap.dedent(SA_FACTORIES))
    (root / "count_inserts.py").write_text(textwrap.dedent(SA_COUNT_INSERTS))
    result = run(root, "safactories", "--json-out", str(tmp_path / "out.json"))
    assert result.returncode == 0, result.stdout + result.stderr
    found = {name: entry["rows"] for name, entry in estimates(json.loads((tmp_path / "out.json").read_text())).items()}
    assert found == {"OrgFactory": 1, "AccountFactory": 2, "MemberFactory": 4, "SharedMemberFactory": 3}
    truth = subprocess.run([sys.executable, "count_inserts.py", *found], cwd=root, capture_output=True, text=True, env=clean_env(), timeout=120)
    assert truth.returncode == 0, truth.stderr
    assert json.loads(truth.stdout) == found
