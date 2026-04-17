from django.db.models import Sum
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render

from apps.submissions.models import Submission
from apps.payments.models import Payment, Tariff
from apps.industries.models import Industry


def _build_filters(request):
    """Build ORM filters dict from GET params."""
    filters = {}
    industry = request.GET.get("industry")
    if industry:
        filters["client__industry_id"] = industry

    tariff = request.GET.get("tariff")
    if tariff:
        filters["tariff_id"] = tariff

    city = request.GET.get("city")
    if city:
        filters["client__city__icontains"] = city

    date_from = request.GET.get("date_from")
    if date_from:
        filters["created_at__date__gte"] = date_from

    date_to = request.GET.get("date_to")
    if date_to:
        filters["created_at__date__lte"] = date_to

    return filters


def dashboard_callback(request, context):
    """Inject dashboard stats into admin index template (UNFOLD DASHBOARD_CALLBACK)."""
    filters = _build_filters(request)
    qs_submissions = Submission.objects.filter(**filters)
    qs_payments = Payment.objects.filter(
        status="succeeded",
        submission__in=qs_submissions,
    )

    context.update({
        "stats": {
            "total": qs_submissions.count(),
            "in_progress": qs_submissions.filter(
                status__in=["in_progress_basic", "in_progress_full", "completed", "under_audit"]
            ).count(),
            "delivered": qs_submissions.filter(status="delivered").count(),
            "revenue": qs_payments.aggregate(total=Sum("amount"))["total"] or 0,
        },
        "filter_industries": Industry.objects.filter(is_active=True),
        "filter_tariffs": Tariff.objects.filter(is_active=True),
        "active_filters": request.GET.dict(),
    })
    return context


@staff_member_required
def dashboard_stats_partial(request):
    """HTMX endpoint: returns only stats cards fragment for filter updates."""
    context = dashboard_callback(request, {})
    return render(request, "admin/dashboard/_stats_cards.html", context)
