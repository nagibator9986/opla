---
phase: 01-infrastructure-data-model
plan: 03
type: execute
wave: 2
title: "Backups and seed data"
depends_on: [01, 02]
requirements: [INFRA-06]  # partial: script only, cron scheduling deferred to Phase 8 (HARD-08)
autonomous: true
files_modified:
  - docker/postgres-backup.sh
  - backend/apps/core/management/__init__.py
  - backend/apps/core/management/commands/__init__.py
  - backend/apps/core/management/commands/seed_initial.py
  - backend/tests/test_seed.py
  - backend/tests/test_backup.py
nyquist_compliant: true
---

# Plan 03: Backups and Seed Data

## Goal

Create PostgreSQL backup script (pg_dump → MinIO via mc), idempotent seed management command with baseline data (5 industries, 3 tariffs, demo questionnaire templates), and their tests.

## must_haves

- `docker/postgres-backup.sh` runs pg_dump, gzips, uploads to MinIO, cleans old backups (7 day retention)
- `python manage.py seed_initial` creates 5 industries, 3 tariffs, 1 demo template per industry
- Seed is idempotent — running twice produces same result
- Tests verify seed idempotency and data creation

## Tasks

<task id="03-01">
<title>Create postgres-backup.sh</title>
<read_first>
- .planning/phases/01-infrastructure-data-model/01-CONTEXT.md (backup decisions)
- .planning/phases/01-infrastructure-data-model/01-RESEARCH.md (MinIO mc pattern)
- docker/docker-compose.yml
</read_first>
<action>
Create `docker/postgres-backup.sh`:

```bash
#!/bin/bash
set -euo pipefail

# Configuration from environment
DB_HOST="${POSTGRES_HOST:-db}"
DB_PORT="${POSTGRES_PORT:-5432}"
DB_NAME="${POSTGRES_DB:-baqsy}"
DB_USER="${POSTGRES_USER:-baqsy}"
MINIO_ALIAS="${MINIO_ALIAS:-local}"
MINIO_BUCKET="${MINIO_BUCKET:-baqsy}"
BACKUP_PREFIX="backups/db"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-7}"

TIMESTAMP=$(date +%Y-%m-%d_%H-%M-%S)
FILENAME="${DB_NAME}_${TIMESTAMP}.sql.gz"
REMOTE_PATH="${MINIO_ALIAS}/${MINIO_BUCKET}/${BACKUP_PREFIX}/${FILENAME}"

echo "[backup] Starting PostgreSQL backup: ${FILENAME}"

# Dump and compress
PGPASSWORD="${POSTGRES_PASSWORD}" pg_dump \
    -h "${DB_HOST}" \
    -p "${DB_PORT}" \
    -U "${DB_USER}" \
    -d "${DB_NAME}" \
    --no-owner \
    --no-acl \
    | gzip > "/tmp/${FILENAME}"

FILESIZE=$(du -h "/tmp/${FILENAME}" | cut -f1)
echo "[backup] Dump complete: ${FILESIZE}"

# Upload to MinIO
mc cp "/tmp/${FILENAME}" "${REMOTE_PATH}"
echo "[backup] Uploaded to ${REMOTE_PATH}"

# Clean up local file
rm -f "/tmp/${FILENAME}"

# Remove old backups (older than RETENTION_DAYS)
echo "[backup] Cleaning backups older than ${RETENTION_DAYS} days..."
mc find "${MINIO_ALIAS}/${MINIO_BUCKET}/${BACKUP_PREFIX}/" \
    --older-than "${RETENTION_DAYS}d" \
    --exec "mc rm {}" 2>/dev/null || true

echo "[backup] Done."
```

Make executable: `chmod +x docker/postgres-backup.sh`
</action>
<acceptance_criteria>
- `docker/postgres-backup.sh` exists and is executable
- `docker/postgres-backup.sh` contains `pg_dump`
- `docker/postgres-backup.sh` contains `mc cp`
- `docker/postgres-backup.sh` contains `mc find`
- `docker/postgres-backup.sh` contains `RETENTION_DAYS`
</acceptance_criteria>
</task>

<task id="03-02">
<title>Create seed_initial management command</title>
<read_first>
- .planning/phases/01-infrastructure-data-model/01-CONTEXT.md (seed data decisions)
- backend/apps/industries/models.py
- backend/apps/payments/models.py
- backend/apps/accounts/models.py
</read_first>
<action>
Create directory structure:
```
backend/apps/core/management/__init__.py       (empty)
backend/apps/core/management/commands/__init__.py  (empty)
backend/apps/core/management/commands/seed_initial.py
```

In `seed_initial.py`:
```python
import os
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.accounts.models import BaseUser
from apps.industries.models import Industry, QuestionnaireTemplate, Question
from apps.payments.models import Tariff


INDUSTRIES = [
    {"name": "Ритейл", "code": "retail", "description": "Розничная торговля"},
    {"name": "IT/Digital", "code": "it-digital", "description": "IT и цифровые технологии"},
    {"name": "Производство", "code": "manufacturing", "description": "Производственные предприятия"},
    {"name": "Услуги", "code": "services", "description": "Сфера услуг"},
    {"name": "F&B", "code": "food-beverage", "description": "Еда и напитки, HoReCa"},
]

TARIFFS = [
    {"code": "ashide_1", "title": "Ashıde 1", "price_kzt": 45000, "description": "Базовый аудит — 7-9 параметров"},
    {"code": "ashide_2", "title": "Ashıde 2", "price_kzt": 135000, "description": "Расширенный аудит — 18-24 параметра"},
    {"code": "upsell", "title": "Upsell Ashıde 1→2", "price_kzt": 90000, "description": "Доплата за переход с Ashıde 1 на Ashıde 2"},
]

# Demo questions: 5 block A (common) + 1 block B + 3 block C
DEMO_QUESTIONS = [
    {"order": 1, "text": "Официальное название предприятия и бренд", "field_type": "text", "block": "A"},
    {"order": 2, "text": "Ссылки на сайт и соцсети", "field_type": "text", "block": "A"},
    {"order": 3, "text": "Страна и город", "field_type": "text", "block": "A"},
    {"order": 4, "text": "Масштаб (оборот)", "field_type": "choice",
     "options": {"choices": ["До 100к$", "До 1М$", "До 10М$", "Выше 10М$"]}, "block": "A"},
    {"order": 5, "text": "Общее количество сотрудников", "field_type": "number", "block": "A"},
    {"order": 6, "text": "Краткое описание деятельности (3-4 предложения)", "field_type": "text", "block": "B"},
    {"order": 7, "text": "Опишите вашу текущую маркетинговую стратегию", "field_type": "text", "block": "C"},
    {"order": 8, "text": "Какие каналы продаж вы используете?", "field_type": "multichoice",
     "options": {"choices": ["Офлайн точки", "Сайт", "Маркетплейсы", "Социальные сети", "Другое"]}, "block": "C"},
    {"order": 9, "text": "Основные конкуренты и ваши отличия от них", "field_type": "text", "block": "C"},
]


class Command(BaseCommand):
    help = "Seed initial data: superuser, industries, tariffs, demo templates"

    @transaction.atomic
    def handle(self, *args, **options):
        self._create_superuser()
        self._create_industries()
        self._create_tariffs()
        self._create_demo_templates()
        self.stdout.write(self.style.SUCCESS("Seed complete."))

    def _create_superuser(self):
        email = os.getenv("DJANGO_SUPERUSER_EMAIL", "admin@baqsy.kz")
        password = os.getenv("DJANGO_SUPERUSER_PASSWORD", "admin")
        if not BaseUser.objects.filter(email=email).exists():
            BaseUser.objects.create_superuser(email=email, password=password)
            self.stdout.write(f"  Created superuser: {email}")
        else:
            self.stdout.write(f"  Superuser exists: {email}")

    def _create_industries(self):
        for data in INDUSTRIES:
            obj, created = Industry.objects.get_or_create(
                code=data["code"],
                defaults={"name": data["name"], "description": data["description"]},
            )
            status = "created" if created else "exists"
            self.stdout.write(f"  Industry {obj.name}: {status}")

    def _create_tariffs(self):
        for data in TARIFFS:
            obj, created = Tariff.objects.get_or_create(
                code=data["code"],
                defaults={"title": data["title"], "price_kzt": data["price_kzt"], "description": data["description"]},
            )
            status = "created" if created else "exists"
            self.stdout.write(f"  Tariff {obj.title}: {status}")

    def _create_demo_templates(self):
        for industry in Industry.objects.all():
            if QuestionnaireTemplate.objects.filter(industry=industry).exists():
                self.stdout.write(f"  Template for {industry.name}: exists")
                continue
            template = QuestionnaireTemplate.objects.create(
                industry=industry,
                version=1,
                is_active=True,
                name=f"Демо-анкета: {industry.name}",
            )
            for q_data in DEMO_QUESTIONS:
                Question.objects.create(
                    template=template,
                    order=q_data["order"],
                    text=q_data["text"],
                    field_type=q_data["field_type"],
                    options=q_data.get("options", {}),
                    required=True,
                    block=q_data["block"],
                )
            self.stdout.write(f"  Template for {industry.name}: created ({template.questions.count()} questions)")
```
</action>
<acceptance_criteria>
- `backend/apps/core/management/commands/seed_initial.py` contains `class Command(BaseCommand):`
- `backend/apps/core/management/commands/seed_initial.py` contains `get_or_create`
- `backend/apps/core/management/commands/seed_initial.py` contains `INDUSTRIES =`
- `backend/apps/core/management/commands/seed_initial.py` contains `TARIFFS =`
- `backend/apps/core/management/commands/seed_initial.py` contains `DEMO_QUESTIONS =`
- `python manage.py seed_initial` exits 0
</acceptance_criteria>
</task>

<task id="03-03">
<title>Write tests for seed command</title>
<read_first>
- backend/apps/core/management/commands/seed_initial.py
- .planning/phases/01-infrastructure-data-model/01-VALIDATION.md (test map: 1-03-01, 1-03-02)
</read_first>
<action>
In `backend/tests/test_seed.py`:

```python
import pytest
from django.core.management import call_command

from apps.industries.models import Industry, QuestionnaireTemplate, Question
from apps.payments.models import Tariff
from apps.accounts.models import BaseUser


@pytest.mark.django_db
def test_seed_creates_baseline_data():
    call_command("seed_initial")
    
    assert Industry.objects.count() == 5
    assert Tariff.objects.count() == 3
    assert QuestionnaireTemplate.objects.filter(is_active=True).count() == 5
    assert BaseUser.objects.filter(is_superuser=True).exists()
    
    # Each template has 9 demo questions
    for tmpl in QuestionnaireTemplate.objects.all():
        assert tmpl.questions.count() == 9

    # Verify specific tariffs
    assert Tariff.objects.filter(code="ashide_1", price_kzt=45000).exists()
    assert Tariff.objects.filter(code="ashide_2", price_kzt=135000).exists()
    assert Tariff.objects.filter(code="upsell", price_kzt=90000).exists()


@pytest.mark.django_db
def test_seed_initial_idempotent():
    call_command("seed_initial")
    count_industries_1 = Industry.objects.count()
    count_tariffs_1 = Tariff.objects.count()
    count_templates_1 = QuestionnaireTemplate.objects.count()
    
    call_command("seed_initial")
    
    assert Industry.objects.count() == count_industries_1
    assert Tariff.objects.count() == count_tariffs_1
    assert QuestionnaireTemplate.objects.count() == count_templates_1
```
</action>
<acceptance_criteria>
- `backend/tests/test_seed.py` contains `def test_seed_creates_baseline_data`
- `backend/tests/test_seed.py` contains `def test_seed_initial_idempotent`
- `backend/tests/test_seed.py` contains `call_command("seed_initial")`
- `pytest tests/test_seed.py -x` exits 0
</acceptance_criteria>
</task>

<task id="03-04">
<title>Integration smoke: full stack docker-compose up + migrate + seed</title>
<read_first>
- docker/docker-compose.yml
- docker/entrypoint.sh
</read_first>
<action>
This is a manual verification task. Run:

```bash
docker-compose down -v
docker-compose up -d
docker-compose exec web python manage.py migrate --check
docker-compose exec web python manage.py seed_initial
docker-compose exec web python manage.py check
```

Verify:
1. All containers are healthy: `docker-compose ps` shows all services Up (healthy)
2. Admin accessible at http://localhost/admin/ with seeded superuser
3. 5 industries visible in admin
4. 3 tariffs visible in admin
5. 5 questionnaire templates visible in admin (1 per industry)

If any step fails, fix the issue and re-run.
</action>
<acceptance_criteria>
- `docker-compose ps` shows all services as healthy
- `docker-compose exec web python manage.py migrate --check` exits 0
- `docker-compose exec web python manage.py seed_initial` exits 0
- `docker-compose exec web python manage.py check` exits 0
</acceptance_criteria>
</task>

## Verification

After all tasks complete:
```bash
docker/postgres-backup.sh           # manual test: pg_dump runs
python manage.py seed_initial       # seed data created
python manage.py seed_initial       # idempotent re-run
pytest tests/test_seed.py -x -q     # seed tests pass
```
