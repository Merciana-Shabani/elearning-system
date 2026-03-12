from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.generic import ListView

from apps.courses.models import Course
from apps.enrollment.models import Enrollment
from apps.users.models import User

from .forms import ModerationActionForm, RejectInstructorApplicationForm, ReportResolveForm
from .models import ContentReport, InstructorRoleApplication, ModerationAction, ModerationDispute


def _require_moderator(request):
    return request.user.is_authenticated and (request.user.is_moderator or request.user.is_staff)


@login_required
def moderation_dashboard(request):
    if not _require_moderator(request):
        messages.error(request, "You do not have permission to access this page.")
        return redirect("dashboard")

    user = request.user

    # Same personal data used on the generic dashboard
    enrolled_courses = user.enrollments.filter(
        status="active"
    ).select_related("course").order_by("-enrolled_at")[:6]

    taught_courses = []
    if user.is_instructor:
        taught_courses = user.taught_courses.filter(visible=True).order_by("-created_at")[:6]

    # Global stats and moderation queues
    pending_submissions = Course.objects.filter(status=Course.STATUS_SUBMITTED).count()
    flagged_content = ContentReport.objects.filter(status=ContentReport.STATUS_OPEN).count()
    open_disputes = ModerationDispute.objects.filter(status=ModerationDispute.STATUS_OPEN).count()

    total_users = User.objects.filter(is_active=True).count()
    total_courses = Course.objects.filter(visible=True).count()
    total_enrollments = Enrollment.objects.filter(status="active").count()

    return render(
        request,
        "moderation/dashboard.html",
        {
            "pending_submissions": pending_submissions,
            "flagged_content": flagged_content,
            "open_disputes": open_disputes,
            "enrolled_courses": enrolled_courses,
            "taught_courses": taught_courses,
            "total_users": total_users,
            "total_courses": total_courses,
            "total_enrollments": total_enrollments,
        },
    )


@login_required
def pending_courses(request):
    if not _require_moderator(request):
        messages.error(request, "You do not have permission to access this page.")
        return redirect("dashboard")
    return redirect("courses:pending_approval")


@login_required
def instructor_applications(request):
    if not _require_moderator(request):
        messages.error(request, "You do not have permission to access this page.")
        return redirect("dashboard")
    apps = InstructorRoleApplication.objects.select_related("user", "reviewed_by").all()
    status = (request.GET.get("status") or "").strip()
    if status:
        apps = apps.filter(status=status)
    return render(request, "moderation/instructor_applications.html", {"applications": apps})


@login_required
def approve_instructor_application(request, pk):
    if not _require_moderator(request):
        messages.error(request, "You do not have permission to access this page.")
        return redirect("dashboard")
    app = get_object_or_404(InstructorRoleApplication, pk=pk)
    if app.status != InstructorRoleApplication.STATUS_PENDING:
        messages.warning(request, "Application is not pending.")
        return redirect("moderation:instructor_applications")
    if request.method == "POST":
        app.status = InstructorRoleApplication.STATUS_APPROVED
        app.reviewed_by = request.user
        app.reviewed_at = timezone.now()
        app.decision_reason = (request.POST.get("decision_reason") or "").strip()
        app.save(update_fields=["status", "reviewed_by", "reviewed_at", "decision_reason"])

        # Grant instructor role
        u = app.user
        u.role = User.ROLE_TEACHER
        u.save(update_fields=["role", "updated_at"])
        messages.success(request, "Instructor application approved.")
        return redirect("moderation:instructor_applications")
    return render(request, "moderation/instructor_application_approve.html", {"application": app})


@login_required
def reject_instructor_application(request, pk):
    if not _require_moderator(request):
        messages.error(request, "You do not have permission to access this page.")
        return redirect("dashboard")
    app = get_object_or_404(InstructorRoleApplication, pk=pk)
    if app.status != InstructorRoleApplication.STATUS_PENDING:
        messages.warning(request, "Application is not pending.")
        return redirect("moderation:instructor_applications")

    if request.method == "POST":
        form = RejectInstructorApplicationForm(request.POST)
        if form.is_valid():
            app.status = InstructorRoleApplication.STATUS_REJECTED
            app.reviewed_by = request.user
            app.reviewed_at = timezone.now()
            app.decision_reason = form.cleaned_data["decision_reason"]
            app.save(update_fields=["status", "reviewed_by", "reviewed_at", "decision_reason"])
            messages.success(request, "Instructor application rejected.")
            return redirect("moderation:instructor_applications")
    else:
        form = RejectInstructorApplicationForm()
    return render(request, "moderation/instructor_application_reject.html", {"application": app, "form": form})


VALID_ROLES = {User.ROLE_STUDENT, User.ROLE_TEACHER, User.ROLE_MODERATOR, User.ROLE_ADMIN}


@login_required
def user_moderate(request, pk):
    if not _require_moderator(request):
        messages.error(request, "You do not have permission to access this page.")
        return redirect("dashboard")
    target = get_object_or_404(User, pk=pk)

    if request.method == "POST":
        # Reactivate account (only when explicitly requested)
        if request.POST.get("reactivate") == "1":
            target.is_active = True
            target.save(update_fields=["is_active", "updated_at"])
            messages.success(request, "Account reactivated.")
            return redirect("moderation:user_moderate", pk=pk)

        # Change role and can_teach only when the role form was submitted (not the action form)
        if request.POST.get("role_form") == "1":
            new_role = request.POST.get("new_role")
            if new_role in VALID_ROLES:
                role_changed = new_role != target.role
                target.role = new_role
                # Moderators/Admins can also be instructors (can_teach). Instructors get it via role; students do not.
                if new_role in (User.ROLE_MODERATOR, User.ROLE_ADMIN):
                    target.can_teach = request.POST.get("can_teach") == "on"
                elif new_role == User.ROLE_TEACHER:
                    target.can_teach = False  # instructor capability comes from role
                else:
                    target.can_teach = False
                # Only update role/can_teach; never change is_active here
                target.save(update_fields=["role", "can_teach", "updated_at"])
                if role_changed:
                    messages.success(request, f"Role updated to {target.get_role_display()}.")
                else:
                    messages.success(request, "Settings updated.")
                return redirect("moderation:user_moderate", pk=pk)

        form = ModerationActionForm(request.POST)
        if form.is_valid():
            action = ModerationAction.objects.create(
                moderator=request.user,
                user=target,
                action_type=form.cleaned_data["action_type"],
                reason=form.cleaned_data["reason"],
                expires_at=form.build_expires_at(),
            )
            action.apply()
            messages.success(request, "Moderation action recorded.")
            return redirect("moderation:user_moderate", pk=pk)
    else:
        form = ModerationActionForm()

    actions = ModerationAction.objects.filter(user=target).select_related("moderator")[:25]
    return render(
        request,
        "moderation/user_moderate.html",
        {"target_user": target, "form": form, "actions": actions},
    )


@login_required
def reports_list(request):
    if not _require_moderator(request):
        messages.error(request, "You do not have permission to access this page.")
        return redirect("dashboard")
    qs = ContentReport.objects.select_related("reporter", "reviewed_by", "content_type").all()
    status = (request.GET.get("status") or "").strip()
    if status:
        qs = qs.filter(status=status)
    return render(request, "moderation/reports_list.html", {"reports": qs[:200]})


def _hide_object(obj):
    for field in ("visible", "is_active"):
        if hasattr(obj, field):
            setattr(obj, field, False)
            obj.save(update_fields=[field])
            return True, f"Set {field}=False"
    return False, "No supported hide field found"


@login_required
def report_detail(request, pk):
    if not _require_moderator(request):
        messages.error(request, "You do not have permission to access this page.")
        return redirect("dashboard")
    report = get_object_or_404(ContentReport, pk=pk)
    obj = report.content_object

    if request.method == "POST":
        form = ReportResolveForm(request.POST)
        if form.is_valid():
            action = form.cleaned_data["action"]
            notes = (form.cleaned_data.get("resolution_notes") or "").strip()

            if action == "hide" and obj is not None:
                ok, msg = _hide_object(obj)
                if not ok:
                    messages.error(request, msg)
                    return redirect("moderation:report_detail", pk=pk)
                report.resolution_notes = (notes + ("\n" if notes else "") + f"Action: hide ({msg})").strip()
            elif action == "remove" and obj is not None:
                obj.delete()
                report.resolution_notes = (notes + ("\n" if notes else "") + "Action: removed content").strip()
            else:
                report.resolution_notes = notes

            report.status = ContentReport.STATUS_CLOSED
            report.reviewed_by = request.user
            report.reviewed_at = timezone.now()
            report.save(update_fields=["status", "reviewed_by", "reviewed_at", "resolution_notes"])
            messages.success(request, "Report resolved.")
            return redirect("moderation:reports")
    else:
        form = ReportResolveForm()

    return render(request, "moderation/report_detail.html", {"report": report, "object": obj, "form": form})


@login_required
def disputes_list(request):
    if not _require_moderator(request):
        messages.error(request, "You do not have permission to access this page.")
        return redirect("dashboard")
    disputes = ModerationDispute.objects.select_related("opened_by", "against_user").all()[:200]
    return render(request, "moderation/disputes_list.html", {"disputes": disputes})


class EnrollmentListView(LoginRequiredMixin, ListView):
    """Moderator view: list all enrollments (user, course, date, status)."""
    model = Enrollment
    template_name = "moderation/enrollment_list.html"
    context_object_name = "enrollments"
    paginate_by = 25

    def get_queryset(self):
        if not _require_moderator(self.request):
            return Enrollment.objects.none()
        return (
            Enrollment.objects
            .select_related("user", "course", "course__category")
            .order_by("-enrolled_at")
        )

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not _require_moderator(request):
            messages.error(request, "You do not have permission to access this page.")
            return redirect("dashboard")
        return super().dispatch(request, *args, **kwargs)


@login_required
def apply_instructor_role(request):
    """Instructor role is assigned by a moderator. Redirect with message."""
    messages.info(
        request,
        "Instructor role is assigned by a moderator. Contact a moderator or go to Users and ask them to change your role.",
    )
    return redirect("dashboard")

