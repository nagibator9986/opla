---
phase: 03-telegram-bot
plan: 00
type: execute
wave: 0
title: "Bot bootstrap — Wave 0 prerequisites and missing API endpoints"
depends_on: []
requirements: []
autonomous: true
files_modified:
  - bot/pyproject.toml
  - bot/config.py
  - backend/apps/submissions/models.py
  - backend/apps/submissions/migrations/0002_submission_last_reminded_at.py
  - backend/apps/accounts/views.py
  - backend/apps/accounts/bot_urls.py
  - backend/baqsy/settings/base.py
nyquist_compliant: true
---

# Plan 00: Bot Bootstrap — Prerequisites

## Goal

Add missing API endpoints needed by bot (JWT by telegram_id, active submission lookup), add `last_reminded_at` field to Submission, increase JWT lifetime for bot users, add pytest-asyncio to bot deps.

## must_haves

- `POST /api/v1/bot/jwt/` endpoint returns JWT for telegram_id (bot calls this for session recovery)
- `GET /api/v1/bot/active-submission/` returns in-progress submission by telegram_id
- `Submission.last_reminded_at` field exists for 24h reminder dedup
- JWT ACCESS_TOKEN_LIFETIME increased to 4h (or bot handles refresh)
- pytest-asyncio in bot dev deps

## Tasks

<task id="00-01">
<title>Add missing bot API endpoints</title>
<read_first>
- backend/apps/accounts/views.py
- backend/apps/accounts/bot_urls.py
- backend/apps/submissions/models.py
- .planning/phases/03-telegram-bot/03-RESEARCH.md
</read_first>
<action>
Add two new views to `backend/apps/accounts/views.py`:

```python
class BotJWTView(APIView):
    """POST /api/v1/bot/jwt/ — bot requests JWT for a telegram_id (session recovery)."""
    permission_classes = [IsBotAuthenticated]

    def post(self, request):
        telegram_id = request.data.get("telegram_id")
        if not telegram_id:
            return Response({"detail": "telegram_id required"}, status=400)
        try:
            profile = ClientProfile.objects.get(telegram_id=telegram_id)
        except ClientProfile.DoesNotExist:
            return Response({"detail": "Client not found"}, status=404)

        email = f"tg_{telegram_id}@baqsy.internal"
        user, _ = BaseUser.objects.get_or_create(email=email, defaults={"is_active": True})
        refresh = RefreshToken.for_user(user)
        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "client_profile_id": profile.id,
        })


class ActiveSubmissionView(APIView):
    """GET /api/v1/bot/active-submission/?telegram_id=N — find in-progress submission."""
    permission_classes = [IsBotAuthenticated]

    def get(self, request):
        telegram_id = request.query_params.get("telegram_id")
        if not telegram_id:
            return Response({"detail": "telegram_id required"}, status=400)
        try:
            profile = ClientProfile.objects.get(telegram_id=telegram_id)
        except ClientProfile.DoesNotExist:
            return Response({"detail": "No profile"}, status=404)

        from apps.submissions.models import Submission
        sub = Submission.objects.filter(
            client=profile,
            status__in=["in_progress_full", "paid", "in_progress_basic"]
        ).order_by("-created_at").first()

        if not sub:
            return Response({"detail": "No active submission"}, status=404)

        from apps.submissions.serializers import SubmissionDetailSerializer
        return Response(SubmissionDetailSerializer(sub).data)
```

Add to `backend/apps/accounts/bot_urls.py`:
```python
path("jwt/", BotJWTView.as_view(), name="bot-jwt"),
path("active-submission/", ActiveSubmissionView.as_view(), name="bot-active-submission"),
```

Import `BotJWTView, ActiveSubmissionView` in bot_urls.py.
</action>
<acceptance_criteria>
- `backend/apps/accounts/views.py` contains `class BotJWTView(APIView):`
- `backend/apps/accounts/views.py` contains `class ActiveSubmissionView(APIView):`
- `backend/apps/accounts/bot_urls.py` contains `path("jwt/"`
- `backend/apps/accounts/bot_urls.py` contains `path("active-submission/"`
</acceptance_criteria>
</task>

<task id="00-02">
<title>Add last_reminded_at to Submission + increase JWT lifetime</title>
<read_first>
- backend/apps/submissions/models.py
- backend/baqsy/settings/base.py (SIMPLE_JWT)
</read_first>
<action>
1. Add field to `backend/apps/submissions/models.py` Submission class:
```python
last_reminded_at = models.DateTimeField(null=True, blank=True)
```

2. Generate migration:
```bash
cd backend && python manage.py makemigrations submissions --name submission_last_reminded_at
```

3. Update `SIMPLE_JWT` in `backend/baqsy/settings/base.py`:
```python
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=4),  # was 1h, extended for bot questionnaire sessions
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
}
```

4. Add `pytest-asyncio` and `pytest-mock` to `bot/pyproject.toml`:
```bash
cd bot && poetry add --group dev pytest-asyncio pytest-mock
```
</action>
<acceptance_criteria>
- `backend/apps/submissions/models.py` contains `last_reminded_at = models.DateTimeField(null=True`
- `backend/baqsy/settings/base.py` contains `timedelta(hours=4)`
- `bot/pyproject.toml` contains `pytest-asyncio`
- Migration file exists for last_reminded_at
</acceptance_criteria>
</task>

## Verification

```bash
python manage.py migrate --check  # migration applies
python manage.py check            # no issues
pytest apps/accounts/tests/ -x    # new endpoints tested
```
