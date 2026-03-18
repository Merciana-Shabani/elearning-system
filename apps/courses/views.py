from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import FileResponse, Http404
from apps.users.mixins import TeacherRequiredMixin, ModeratorRequiredMixin
from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import DetailView, ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from django.db.models import Q, Count, Max, Avg
from django.utils.text import slugify
import os
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from .models import (
    Course, CourseCategory, CourseSection, CourseModule, CoursePage, CourseFile,
    CourseAnnouncement, CourseModuleCompletion, CourseCertificate,
    Document, SavedDocument,
)
from .forms import (
    CourseForm, CourseSectionForm, CourseModuleForm, CoursePageForm, CourseFileForm,
    CourseAnnouncementForm,
    DocumentForm,
)


class CourseListView(ListView):
    """Course catalogue."""
    model = Course
    template_name = 'courses/course_list.html'
    context_object_name = 'courses'
    paginate_by = 12

    def get_queryset(self):
        # Students see only published courses
        qs = Course.objects.filter(
            visible=True, status=Course.STATUS_PUBLISHED
        ).select_related('category', 'teacher')
        q = self.request.GET.get('q')
        category_id = self.request.GET.get('category')
        if q:
            qs = qs.filter(Q(fullname__icontains=q) | Q(shortname__icontains=q) | Q(summary__icontains=q))
        if category_id:
            qs = qs.filter(category_id=category_id)
        return qs.annotate(student_count=Count('enrollments')).order_by('fullname')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = CourseCategory.objects.filter(visible=True)
        context['selected_category'] = self.request.GET.get('category')
        if self.request.user.is_authenticated:
            from apps.enrollment.models import Enrollment
            context['enrolled_course_ids'] = set(
                Enrollment.objects.filter(
                    user=self.request.user, status='active'
                ).values_list('course_id', flat=True)
            )
        else:
            context['enrolled_course_ids'] = set()
        return context


class DocumentsLibraryView(LoginRequiredMixin, ListView):
    """Normal Staff: browse all uploaded documents."""
    model = Document
    template_name = 'documents/library.html'
    context_object_name = 'documents'
    paginate_by = 20

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_normal_staff:
            messages.error(request, 'Access denied.')
            return redirect('dashboard')
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        qs = Document.objects.filter(visible=True)
        q = (self.request.GET.get('q') or '').strip()
        if q:
            qs = qs.filter(Q(title__icontains=q) | Q(description__icontains=q))
        return qs.order_by('-created_at')


class SavedDocumentsView(LoginRequiredMixin, ListView):
    """Normal Staff: list documents auto-saved on download."""
    model = SavedDocument
    template_name = 'documents/saved.html'
    context_object_name = 'saved'
    paginate_by = 20

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_normal_staff:
            messages.error(request, 'Access denied.')
            return redirect('dashboard')
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return (
            SavedDocument.objects.filter(user=self.request.user)
            .select_related('document', 'document__uploaded_by')
            .order_by('-saved_at')
        )


class DocumentUploadView(TeacherRequiredMixin, CreateView):
    """Instructor: upload a standalone document for Normal Staff."""
    model = Document
    form_class = DocumentForm
    template_name = 'documents/upload.html'

    def form_valid(self, form):
        form.instance.uploaded_by = self.request.user
        messages.success(self.request, 'Document uploaded successfully.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('courses:document_upload')


@login_required
def document_download(request, pk):
    """Normal Staff: download a document; auto-save to Saved Documents."""
    if not request.user.is_normal_staff:
        raise Http404('You do not have access to this content.')
    doc = get_object_or_404(Document, pk=pk, visible=True)
    if not doc.file:
        raise Http404('File not found.')
    SavedDocument.objects.get_or_create(user=request.user, document=doc)
    filename = os.path.basename(doc.file.name)
    if doc.title:
        ext = os.path.splitext(filename)[1]
        filename = slugify(doc.title)[:50] + (ext or '')
    as_attachment = True
    try:
        file_handle = doc.file.open('rb')
        return FileResponse(file_handle, as_attachment=as_attachment, filename=filename)
    except (ValueError, OSError, AttributeError):
        from django.http import HttpResponseRedirect
        return HttpResponseRedirect(doc.file.url)


@login_required
def document_view(request, pk):
    """Normal Staff: open a document inline (read in browser)."""
    if not request.user.is_normal_staff:
        raise Http404('You do not have access to this content.')
    doc = get_object_or_404(Document, pk=pk, visible=True)
    if not doc.file:
        raise Http404('File not found.')
    # Ensure it is saved once they open it for reading.
    SavedDocument.objects.get_or_create(user=request.user, document=doc)
    filename = os.path.basename(doc.file.name)
    if doc.title:
        ext = os.path.splitext(filename)[1]
        filename = slugify(doc.title)[:50] + (ext or '')
    try:
        file_handle = doc.file.open('rb')
        response = FileResponse(file_handle, as_attachment=False, filename=filename)
        response['Content-Disposition'] = 'inline; filename="{}"'.format(filename)
        return response
    except (ValueError, OSError, AttributeError):
        from django.http import HttpResponseRedirect
        return HttpResponseRedirect(doc.file.url)

class CourseTeachingListView(TeacherRequiredMixin, ListView):
    """Instructor: list courses owned by the current instructor (all statuses)."""
    model = Course
    template_name = 'courses/course_teaching_list.html'
    context_object_name = 'courses'
    paginate_by = 20

    def get_queryset(self):
        """Only courses this user teaches (created). Staff do not see all courses here; use 'View all courses' for that."""
        return (
            Course.objects.filter(teacher=self.request.user)
            .select_related('category', 'teacher')
            .order_by('-created_at')
        )


class CourseAllTableView(TeacherRequiredMixin, ListView):
    """Instructor: view ALL courses in table format (same as teaching list). Own courses get full actions; others get View only."""
    model = Course
    template_name = 'courses/course_list_all.html'
    context_object_name = 'courses'
    paginate_by = 25

    def get_queryset(self):
        return Course.objects.all().select_related('category', 'teacher').order_by('fullname')


class CourseDetailView(LoginRequiredMixin, DetailView):
    """Course detail: title, description, module outline, instructor. Public for guests."""
    model = Course
    template_name = 'courses/course_detail.html'
    context_object_name = 'course'

    def get_queryset(self):
        # Allow viewing if published, or if user is teacher/staff (see own draft/submitted)
        return Course.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course = self.get_object()
        is_teacher = course.teacher == self.request.user or self.request.user.is_staff
        if not is_teacher and course.status != Course.STATUS_PUBLISHED:
            from django.http import Http404
            raise Http404('Course not available.')
        context['sections'] = course.sections.filter(visible=True).prefetch_related('modules')
        context['is_enrolled'] = course.enrollments.filter(
            user=self.request.user, status='active'
        ).exists()
        context['is_teacher'] = is_teacher
        context['enrolled_count'] = course.enrolled_count
        return context


class CourseCreateView(TeacherRequiredMixin, CreateView):
    model = Course
    form_class = CourseForm
    template_name = 'courses/course_form.html'

    def form_valid(self, form):
        form.instance.teacher = self.request.user
        messages.success(self.request, 'Course created successfully.')
        return super().form_valid(form)


class CourseUpdateView(TeacherRequiredMixin, UpdateView):
    model = Course
    form_class = CourseForm
    template_name = 'courses/course_form.html'

    def get_queryset(self):
        if self.request.user.is_staff:
            return Course.objects.all()
        return Course.objects.filter(teacher=self.request.user)


class CourseDeleteView(TeacherRequiredMixin, DeleteView):
    model = Course
    template_name = 'courses/course_confirm_delete.html'
    success_url = reverse_lazy('courses:list')

    def get_queryset(self):
        if self.request.user.is_staff:
            return Course.objects.all()
        return Course.objects.filter(teacher=self.request.user)


class CategoryDetailView(LoginRequiredMixin, DetailView):
    model = CourseCategory
    template_name = 'courses/category_detail.html'
    context_object_name = 'category'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category = self.get_object()
        context['courses'] = Course.objects.filter(
            category=category, visible=True
        ).select_related('teacher')
        context['subcategories'] = category.children.filter(visible=True)
        return context


def _can_access_course_content(request, course):
    """Return True if user can access this course's content (requires authenticated user)."""
    if course.teacher == request.user or request.user.is_staff:
        return True
    if course.status != Course.STATUS_PUBLISHED:
        return False
    return course.enrollments.filter(user=request.user, status='active').exists()


def _is_course_teacher(request, course):
    """Return True if user is the course teacher or staff (can manage content)."""
    return course.teacher == request.user or request.user.is_staff


@login_required
def course_content(request, pk):
    """Display course content/modules for enrolled students."""
    course = get_object_or_404(Course, pk=pk, visible=True)
    if not _can_access_course_content(request, course):
        messages.warning(request, 'You must be enrolled to access this course content.')
        return redirect('courses:detail', pk=pk)

    # Teachers see all sections (including hidden); students see only visible
    if course.teacher == request.user or request.user.is_staff:
        sections = course.sections.all().prefetch_related('modules').order_by('sortorder', 'section')
    else:
        sections = course.sections.filter(visible=True).prefetch_related('modules').order_by('sortorder', 'section')
    pages = course.pages.all().order_by('id')
    files = course.files.all().order_by('id')

    # Prerequisites: which modules/sections are unlocked for this user
    completed_module_ids = set()
    if not _is_course_teacher(request, course):
        completed_module_ids = set(
            CourseModuleCompletion.objects.filter(
                user=request.user, module__course=course
            ).values_list('module_id', flat=True)
        )
    section_unlocked = {}
    module_unlocked = {}
    for sec in sections:
        section_unlocked[sec.id] = _user_can_access_section(request, sec)
        for mod in sec.modules.all():
            module_unlocked[mod.id] = (
                (mod.required_module_id is None or mod.required_module_id in completed_module_ids)
                or _is_course_teacher(request, course)
            )

    # Quiz visibility for students: hide quizzes until open
    open_quiz_ids = set()
    if not _is_course_teacher(request, course):
        from apps.quizzes.models import Quiz
        from django.db.models import Q
        now = timezone.now()
        quiz_ids = list(
            course.modules.filter(
                module_type=CourseModule.MODULE_QUIZ,
                visible=True,
                instance_id__isnull=False,
            ).values_list('instance_id', flat=True)
        )
        if quiz_ids:
            open_quiz_ids = set(
                Quiz.objects.filter(
                    pk__in=quiz_ids,
                    visible=True,
                ).filter(
                    Q(time_open__isnull=True) | Q(time_open__lte=now),
                    Q(time_close__isnull=True) | Q(time_close__gte=now),
                ).values_list('pk', flat=True)
            )

    return render(request, 'courses/course_content.html', {
        'course': course,
        'sections': sections,
        'pages': pages,
        'files': files,
        'is_teacher': course.teacher == request.user or request.user.is_staff,
        'section_unlocked': section_unlocked,
        'module_unlocked': module_unlocked,
        'open_quiz_ids': open_quiz_ids,
    })


@login_required
def view_page(request, pk, page_pk):
    """View a course page (lecture notes / learning material)."""
    course = get_object_or_404(Course, pk=pk, visible=True)
    page = get_object_or_404(CoursePage, pk=page_pk, course=course)
    if course.status != Course.STATUS_PUBLISHED:
        raise Http404('Course not available.')
    if not _can_access_course_content(request, course):
        raise Http404('You do not have access to this content.')
    # Prerequisite: check if this page is linked to a module and if so, require it
    mod = CourseModule.objects.filter(
        course=course, module_type=CourseModule.MODULE_PAGE, instance_id=page_pk
    ).first()
    if mod and not _user_can_access_module(request, mod):
        messages.warning(request, 'Complete the previous module before accessing this content.')
        return redirect('courses:content', pk=pk)
    if mod and mod.completion_view:
        CourseModuleCompletion.objects.get_or_create(user=request.user, module=mod)
    return render(request, 'courses/view_page.html', {
        'course': course,
        'page': page,
    })


@login_required
def download_file(request, pk, file_pk):
    """Download a course file (learning material)."""
    course = get_object_or_404(Course, pk=pk, visible=True)
    course_file = get_object_or_404(CourseFile, pk=file_pk, course=course)
    if not _can_access_course_content(request, course):
        raise Http404('You do not have access to this content.')
    mod = CourseModule.objects.filter(
        course=course, module_type=CourseModule.MODULE_FILE, instance_id=file_pk
    ).first()
    if mod and not _user_can_access_module(request, mod):
        messages.warning(request, 'Complete the previous module before accessing this content.')
        return redirect('courses:content', pk=pk)
    if mod and mod.completion_view:
        CourseModuleCompletion.objects.get_or_create(user=request.user, module=mod)
    if not course_file.file:
        raise Http404('File not found.')
    filename = os.path.basename(course_file.file.name)
    if course_file.name:
        ext = os.path.splitext(filename)[1]
        filename = slugify(course_file.name)[:50] + (ext or '')
    as_attachment = request.GET.get('view') != '1'
    try:
        file_handle = course_file.file.open('rb')
        response = FileResponse(file_handle, as_attachment=as_attachment, filename=filename)
        if not as_attachment:
            response['Content-Disposition'] = 'inline; filename="{}"'.format(filename)
        return response
    except (ValueError, OSError, AttributeError):
        from django.http import HttpResponseRedirect
        return HttpResponseRedirect(course_file.file.url)


# ----- Learning materials (teacher only) -----

@login_required
def course_page_add(request, pk):
    """Teacher: add a course page (lecture notes)."""
    course = get_object_or_404(Course, pk=pk)
    if not _is_course_teacher(request, course):
        messages.error(request, 'You can only add content to your own courses.')
        return redirect('courses:detail', pk=pk)
    if request.method == 'POST':
        form = CoursePageForm(request.POST)
        if form.is_valid():
            page = form.save(commit=False)
            page.course = course
            page.save()
            messages.success(request, 'Learning page added.')
            return redirect('courses:content', pk=pk)
    else:
        form = CoursePageForm()
    return render(request, 'courses/course_page_form.html', {
        'course': course,
        'form': form,
        'title': 'Add learning page',
    })


@login_required
def course_page_edit(request, pk, page_pk):
    """Teacher: edit a course page."""
    course = get_object_or_404(Course, pk=pk)
    if not _is_course_teacher(request, course):
        messages.error(request, 'You can only edit content in your own courses.')
        return redirect('courses:detail', pk=pk)
    page = get_object_or_404(CoursePage, pk=page_pk, course=course)
    if request.method == 'POST':
        form = CoursePageForm(request.POST, instance=page)
        if form.is_valid():
            form.save()
            messages.success(request, 'Page updated.')
            return redirect('courses:content', pk=pk)
    else:
        form = CoursePageForm(instance=page)
    return render(request, 'courses/course_page_form.html', {
        'course': course,
        'form': form,
        'page': page,
        'title': 'Edit learning page',
    })


@login_required
def course_page_delete(request, pk, page_pk):
    """Teacher: delete a course page."""
    course = get_object_or_404(Course, pk=pk)
    if not _is_course_teacher(request, course):
        messages.error(request, 'You can only delete content in your own courses.')
        return redirect('courses:detail', pk=pk)
    page = get_object_or_404(CoursePage, pk=page_pk, course=course)
    if request.method == 'POST':
        page.delete()
        messages.success(request, 'Page removed.')
        return redirect('courses:content', pk=pk)
    return render(request, 'courses/course_page_confirm_delete.html', {'course': course, 'page': page})


@login_required
def course_file_add(request, pk):
    """Teacher: add a course file (downloadable material)."""
    course = get_object_or_404(Course, pk=pk)
    if not _is_course_teacher(request, course):
        messages.error(request, 'You can only add content to your own courses.')
        return redirect('courses:detail', pk=pk)
    if request.method == 'POST':
        form = CourseFileForm(request.POST, request.FILES)
        if form.is_valid():
            course_file = form.save(commit=False)
            course_file.course = course
            course_file.save()
            messages.success(request, 'File added.')
            return redirect('courses:content', pk=pk)
    else:
        form = CourseFileForm()
    return render(request, 'courses/course_file_form.html', {
        'course': course,
        'form': form,
        'title': 'Add file',
    })


@login_required
def course_file_edit(request, pk, file_pk):
    """Teacher: edit a course file."""
    course = get_object_or_404(Course, pk=pk)
    if not _is_course_teacher(request, course):
        messages.error(request, 'You can only edit content in your own courses.')
        return redirect('courses:detail', pk=pk)
    course_file = get_object_or_404(CourseFile, pk=file_pk, course=course)
    if request.method == 'POST':
        form = CourseFileForm(request.POST, request.FILES, instance=course_file)
        if form.is_valid():
            form.save()
            messages.success(request, 'File updated.')
            return redirect('courses:content', pk=pk)
    else:
        form = CourseFileForm(instance=course_file)
    return render(request, 'courses/course_file_form.html', {
        'course': course,
        'form': form,
        'course_file': course_file,
        'title': 'Edit file',
    })


@login_required
def course_file_delete(request, pk, file_pk):
    """Teacher: delete a course file."""
    course = get_object_or_404(Course, pk=pk)
    if not _is_course_teacher(request, course):
        messages.error(request, 'You can only delete content in your own courses.')
        return redirect('courses:detail', pk=pk)
    course_file = get_object_or_404(CourseFile, pk=file_pk, course=course)
    if request.method == 'POST':
        course_file.delete()
        messages.success(request, 'File removed.')
        return redirect('courses:content', pk=pk)
    return render(request, 'courses/course_file_confirm_delete.html', {
        'course': course,
        'course_file': course_file,
    })


# ----- Course sections and modules (teacher only) -----

@login_required
def course_section_add(request, pk):
    """Teacher: add a course section."""
    course = get_object_or_404(Course, pk=pk)
    if not _is_course_teacher(request, course):
        messages.error(request, 'You can only add sections to your own courses.')
        return redirect('courses:detail', pk=pk)
    next_section = course.sections.aggregate(m=Max('section'))['m']
    next_section = (next_section or 0) + 1
    next_sort = course.sections.aggregate(m=Max('sortorder'))['m']
    next_sort = (next_sort or 0) + 1
    if request.method == 'POST':
        form = CourseSectionForm(request.POST, course=course)
        if form.is_valid():
            section = form.save(commit=False)
            section.course = course
            section.section = form.cleaned_data.get('section') or next_section
            section.sortorder = next_sort
            section.save()
            messages.success(request, 'Section added.')
            return redirect('courses:content', pk=pk)
    else:
        form = CourseSectionForm(initial={'section': next_section}, course=course)
    return render(request, 'courses/course_section_form.html', {
        'course': course,
        'form': form,
        'title': 'Add section',
    })


@login_required
def course_section_edit(request, pk, section_pk):
    """Teacher: edit a course section."""
    course = get_object_or_404(Course, pk=pk)
    if not _is_course_teacher(request, course):
        messages.error(request, 'You can only edit sections in your own courses.')
        return redirect('courses:detail', pk=pk)
    section = get_object_or_404(CourseSection, pk=section_pk, course=course)
    if request.method == 'POST':
        form = CourseSectionForm(request.POST, instance=section, course=course)
        if form.is_valid():
            form.save()
            messages.success(request, 'Section updated.')
            return redirect('courses:content', pk=pk)
    else:
        form = CourseSectionForm(instance=section, course=course)
    return render(request, 'courses/course_section_form.html', {
        'course': course,
        'form': form,
        'section': section,
        'title': 'Edit section',
    })


@login_required
def course_section_delete(request, pk, section_pk):
    """Teacher: delete a course section (and its modules)."""
    course = get_object_or_404(Course, pk=pk)
    if not _is_course_teacher(request, course):
        messages.error(request, 'You can only delete sections in your own courses.')
        return redirect('courses:detail', pk=pk)
    section = get_object_or_404(CourseSection, pk=section_pk, course=course)
    if request.method == 'POST':
        section.delete()
        messages.success(request, 'Section removed.')
        return redirect('courses:content', pk=pk)
    return render(request, 'courses/course_section_confirm_delete.html', {
        'course': course,
        'section': section,
    })


@login_required
def course_module_add(request, pk, section_pk):
    """Teacher: add a module to a section."""
    course = get_object_or_404(Course, pk=pk)
    if not _is_course_teacher(request, course):
        messages.error(request, 'You can only add modules to your own courses.')
        return redirect('courses:detail', pk=pk)
    section = get_object_or_404(CourseSection, pk=section_pk, course=course)
    if request.method == 'POST':
        form = CourseModuleForm(request.POST, course=course)
        if form.is_valid():
            form.save()
            messages.success(request, 'Module added.')
            return redirect('courses:content', pk=pk)
    else:
        form = CourseModuleForm(course=course, initial={'section': section} if section else None)
    return render(request, 'courses/course_module_form.html', {
        'course': course,
        'form': form,
        'section': section,
        'title': 'Add module',
    })


@login_required
def course_module_edit(request, pk, module_pk):
    """Teacher: edit a course module."""
    course = get_object_or_404(Course, pk=pk)
    if not _is_course_teacher(request, course):
        messages.error(request, 'You can only edit modules in your own courses.')
        return redirect('courses:detail', pk=pk)
    module = get_object_or_404(CourseModule, pk=module_pk, course=course)
    if request.method == 'POST':
        form = CourseModuleForm(request.POST, instance=module, course=course)
        if form.is_valid():
            form.save()
            messages.success(request, 'Module updated.')
            return redirect('courses:content', pk=pk)
    else:
        form = CourseModuleForm(instance=module, course=course)
    return render(request, 'courses/course_module_form.html', {
        'course': course,
        'form': form,
        'module': module,
        'title': 'Edit module',
    })


@login_required
def course_module_delete(request, pk, module_pk):
    """Teacher: delete a course module."""
    course = get_object_or_404(Course, pk=pk)
    if not _is_course_teacher(request, course):
        messages.error(request, 'You can only delete modules in your own courses.')
        return redirect('courses:detail', pk=pk)
    module = get_object_or_404(CourseModule, pk=module_pk, course=course)
    if request.method == 'POST':
        module.delete()
        messages.success(request, 'Module removed.')
        return redirect('courses:content', pk=pk)
    return render(request, 'courses/course_module_confirm_delete.html', {
        'course': course,
        'module': module,
    })


# ----- Course approval workflow (instructor submit, moderator approve/reject) -----

def _notify_course_status(course, approved, rejection_reason=''):
    """Send email to course teacher when course is approved or rejected."""
    if not course.teacher or not course.teacher.email:
        return
    subject = f'Course "{course.fullname}" has been {"approved" if approved else "rejected"}'
    if approved:
        body = f'Your course "{course.fullname}" has been approved and is now published.'
    else:
        body = f'Your course "{course.fullname}" has been rejected.'
        if rejection_reason:
            body += f'\n\nReason: {rejection_reason}'
    try:
        send_mail(
            subject,
            body,
            getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@elening.com'),
            [course.teacher.email],
            fail_silently=True,
        )
    except Exception:
        pass


@login_required
def submit_for_approval(request, pk):
    """Instructor: submit course for moderator approval."""
    course = get_object_or_404(Course, pk=pk)
    if not _is_course_teacher(request, course):
        messages.error(request, 'You can only submit your own courses.')
        return redirect('courses:detail', pk=pk)
    if course.status not in (Course.STATUS_DRAFT, Course.STATUS_REJECTED, Course.STATUS_NEEDS_REVISION):
        messages.warning(request, 'This course is not in draft or rejected state.')
        return redirect('courses:detail', pk=pk)
    course.status = Course.STATUS_SUBMITTED
    course.submitted_at = timezone.now()
    course.rejection_reason = ''
    course.revision_requests = ''
    course.returned_by = None
    course.returned_at = None
    course.save(update_fields=[
        'status', 'submitted_at', 'rejection_reason',
        'revision_requests', 'returned_by', 'returned_at',
        'updated_at',
    ])
    messages.success(request, 'Course submitted for moderator approval.')
    return redirect('courses:teaching')


class CoursePendingApprovalListView(ModeratorRequiredMixin, ListView):
    """Moderator: list courses submitted for approval."""
    model = Course
    template_name = 'courses/course_pending_approval_list.html'
    context_object_name = 'courses'
    paginate_by = 20

    def get_queryset(self):
        return Course.objects.filter(
            status=Course.STATUS_SUBMITTED
        ).select_related('category', 'teacher').order_by('-submitted_at')


@login_required
def approve_course(request, pk):
    """Moderator: approve course (publish it)."""
    if not (request.user.is_moderator or request.user.is_staff):
        messages.error(request, 'Only moderators can approve courses.')
        return redirect('dashboard')
    course = get_object_or_404(Course, pk=pk)
    if course.status != Course.STATUS_SUBMITTED:
        messages.warning(request, 'Course is not pending approval.')
        return redirect('courses:teaching')
    course.status = Course.STATUS_PUBLISHED
    course.approved_by = request.user
    course.approved_at = timezone.now()
    course.rejection_reason = ''
    course.save(update_fields=['status', 'approved_by', 'approved_at', 'rejection_reason', 'updated_at'])
    _notify_course_status(course, approved=True)
    messages.success(request, f'Course "{course.fullname}" has been approved and published.')
    return redirect('courses:pending_approval')


@login_required
def reject_course(request, pk):
    """Moderator: reject course and notify instructor."""
    if not (request.user.is_moderator or request.user.is_staff):
        messages.error(request, 'Only moderators can reject courses.')
        return redirect('dashboard')
    course = get_object_or_404(Course, pk=pk)
    if course.status != Course.STATUS_SUBMITTED:
        messages.warning(request, 'Course is not pending approval.')
        return redirect('courses:pending_approval')
    if request.method == 'GET':
        return render(request, 'courses/reject_course.html', {'course': course})
    reason = (request.POST.get('rejection_reason') or '').strip()
    if not reason:
        messages.error(request, 'Rejection reason is required.')
        return render(request, 'courses/reject_course.html', {'course': course})
    course.status = Course.STATUS_REJECTED
    course.approved_by = request.user
    course.approved_at = timezone.now()
    course.rejection_reason = reason
    course.save(update_fields=['status', 'approved_by', 'approved_at', 'rejection_reason', 'updated_at'])
    _notify_course_status(course, approved=False, rejection_reason=reason)
    messages.success(request, f'Course "{course.fullname}" has been rejected. Instructor will be notified.')
    return redirect('courses:pending_approval')


@login_required
def return_course_for_revision(request, pk):
    """Moderator: return course to instructor with specific revision requests."""
    if not (request.user.is_moderator or request.user.is_staff):
        messages.error(request, 'Only moderators can return courses for revision.')
        return redirect('dashboard')
    course = get_object_or_404(Course, pk=pk)
    if course.status != Course.STATUS_SUBMITTED:
        messages.warning(request, 'Course is not pending approval.')
        return redirect('courses:pending_approval')
    if request.method == 'GET':
        return render(request, 'courses/return_course.html', {'course': course})
    revision_requests = (request.POST.get('revision_requests') or '').strip()
    if not revision_requests:
        messages.error(request, 'Revision requests are required.')
        return render(request, 'courses/return_course.html', {'course': course})
    course.status = Course.STATUS_NEEDS_REVISION
    course.revision_requests = revision_requests
    course.returned_by = request.user
    course.returned_at = timezone.now()
    course.save(update_fields=['status', 'revision_requests', 'returned_by', 'returned_at', 'updated_at'])
    # Email reuse: send as "rejected" but with revision requests for now
    _notify_course_status(course, approved=False, rejection_reason=f'Revision requested:\n{revision_requests}')
    messages.success(request, f'Course "{course.fullname}" returned for revision.')
    return redirect('courses:pending_approval')


# ----- Moderator: manage course categories -----


class CategoryManageListView(ModeratorRequiredMixin, ListView):
    model = CourseCategory
    template_name = 'courses/category_manage_list.html'
    context_object_name = 'categories'
    paginate_by = 50

    def get_queryset(self):
        qs = CourseCategory.objects.all().select_related('parent').order_by('sortorder', 'name')
        q = (self.request.GET.get('q') or '').strip()
        if q:
            qs = qs.filter(name__icontains=q)
        return qs


@login_required
def category_create(request):
    if not (request.user.is_moderator or request.user.is_staff):
        messages.error(request, 'Only moderators can manage categories.')
        return redirect('dashboard')
    from django.forms import ModelForm

    class _Form(ModelForm):
        class Meta:
            model = CourseCategory
            fields = ['name', 'parent', 'sortorder', 'visible', 'idnumber', 'description']

    if request.method == 'POST':
        form = _Form(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category created.')
            return redirect('courses:categories_manage')
    else:
        form = _Form()
    return render(request, 'courses/category_form.html', {'form': form, 'title': 'Create category'})


@login_required
def category_edit(request, pk):
    if not (request.user.is_moderator or request.user.is_staff):
        messages.error(request, 'Only moderators can manage categories.')
        return redirect('dashboard')
    from django.forms import ModelForm
    cat = get_object_or_404(CourseCategory, pk=pk)

    class _Form(ModelForm):
        class Meta:
            model = CourseCategory
            fields = ['name', 'parent', 'sortorder', 'visible', 'idnumber', 'description']

    if request.method == 'POST':
        form = _Form(request.POST, instance=cat)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category updated.')
            return redirect('courses:categories_manage')
    else:
        form = _Form(instance=cat)
    return render(request, 'courses/category_form.html', {'form': form, 'title': 'Edit category', 'category': cat})


@login_required
def category_deactivate(request, pk):
    if not (request.user.is_moderator or request.user.is_staff):
        messages.error(request, 'Only moderators can manage categories.')
        return redirect('dashboard')
    cat = get_object_or_404(CourseCategory, pk=pk)
    if request.method == 'POST':
        cat.visible = False
        cat.save(update_fields=['visible', 'updated_at'])
        messages.success(request, 'Category deactivated.')
        return redirect('courses:categories_manage')
    return render(request, 'courses/category_deactivate_confirm.html', {'category': cat})


# ----- Announcements (instructor post, visible to enrolled) -----

@login_required
def course_announcements_list(request, pk):
    """List announcements for a course. Instructors see manage links; enrolled students see list."""
    course = get_object_or_404(Course, pk=pk)
    if not _can_access_course_content(request, course):
        messages.warning(request, 'You do not have access to this course.')
        return redirect('courses:detail', pk=pk)
    announcements = course.announcements.all().select_related('author')[:50]
    return render(request, 'courses/announcements_list.html', {
        'course': course,
        'announcements': announcements,
        'is_teacher': _is_course_teacher(request, course),
    })


@login_required
def course_announcement_add(request, pk):
    """Instructor: post a new announcement."""
    course = get_object_or_404(Course, pk=pk)
    if not _is_course_teacher(request, course):
        messages.error(request, 'Only instructors can post announcements.')
        return redirect('courses:detail', pk=pk)
    if request.method == 'POST':
        form = CourseAnnouncementForm(request.POST)
        if form.is_valid():
            ann = form.save(commit=False)
            ann.course = course
            ann.author = request.user
            ann.save()
            messages.success(request, 'Announcement posted.')
            return redirect('courses:announcements_list', pk=pk)
    else:
        form = CourseAnnouncementForm()
    return render(request, 'courses/announcement_form.html', {
        'course': course,
        'form': form,
        'title': 'New announcement',
    })


# ----- Prerequisites: check and record module completion -----

def _user_has_completed_module(user, module):
    """Return True if user has completed the given module."""
    return CourseModuleCompletion.objects.filter(user=user, module=module).exists()


def _user_can_access_module(request, module):
    """Return True if user can access this module (prerequisites met). Teachers/staff bypass."""
    if _is_course_teacher(request, module.course):
        return True
    if not module.required_module_id:
        return True
    return _user_has_completed_module(request.user, module.required_module)


def _user_can_access_section(request, section):
    """Return True if user can access this section (required_section completed)."""
    if _is_course_teacher(request, section.course):
        return True
    if not section.required_section_id:
        return True
    # Section "complete" if all its modules are completed (or no modules)
    from .models import CourseModuleCompletion
    modules = section.modules.filter(visible=True)
    if not modules.exists():
        return True
    for m in modules:
        if not _user_has_completed_module(request.user, m):
            return False
    return True


def _record_module_completion(user, course, module_type, instance_id):
    """Record that user completed a module (e.g. viewed a page)."""
    if not instance_id:
        return
    mod = CourseModule.objects.filter(
        course=course, module_type=module_type, instance_id=instance_id
    ).first()
    if mod and mod.completion_view:
        CourseModuleCompletion.objects.get_or_create(user=user, module=mod)


# ----- Analytics & export -----

@login_required
def course_analytics(request, pk):
    """Instructor: per-lesson engagement, quiz scores, drop-off."""
    course = get_object_or_404(Course, pk=pk)
    if not _is_course_teacher(request, course):
        messages.error(request, 'Access denied.')
        return redirect('courses:detail', pk=pk)
    from apps.quizzes.models import QuizAttempt
    enrollments = course.enrollments.filter(status='active').count()
    module_completions = CourseModuleCompletion.objects.filter(
        module__course=course
    ).values('module_id').annotate(count=Count('user', distinct=True))
    module_stats = {mc['module_id']: mc['count'] for mc in module_completions}
    modules = list(course.modules.select_related('section').order_by('section__sortorder', 'sortorder'))
    module_completion_list = [(m, module_stats.get(m.id, 0)) for m in modules]
    quiz_attempts = QuizAttempt.objects.filter(
        quiz__course=course
    ).values('quiz_id', 'quiz__name').annotate(
        attempts=Count('id'),
        users=Count('user', distinct=True),
        avg_grade=Avg('sumgrades'),
    )
    return render(request, 'courses/analytics.html', {
        'course': course,
        'enrollments': enrollments,
        'module_completion_list': module_completion_list,
        'quiz_attempts': list(quiz_attempts),
    })


@login_required
def course_export_reports(request, pk):
    """Instructor: export enrolment and revenue reports as CSV or PDF."""
    course = get_object_or_404(Course, pk=pk)
    if not _is_course_teacher(request, course):
        messages.error(request, 'Access denied.')
        return redirect('courses:detail', pk=pk)
    fmt = request.GET.get('format')
    if fmt not in ('csv', 'pdf'):
        return render(request, 'courses/export_reports.html', {'course': course})
    from django.http import HttpResponse
    from apps.enrollment.models import Enrollment
    enrollments = Enrollment.objects.filter(
        course=course, status='active'
    ).select_related('user').order_by('enrolled_at')
    if fmt == 'csv':
        import csv
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="enrollment_{course.shortname}.csv"'
        w = csv.writer(response)
        w.writerow(['User', 'Email', 'Enrolled at'])
        for e in enrollments:
            w.writerow([e.user.get_full_name(), e.user.email, e.enrolled_at.strftime('%Y-%m-%d %H:%M')])
        return response
    else:
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
            from reportlab.lib import colors
            from reportlab.lib.styles import getSampleStyleSheet
            from io import BytesIO
        except ImportError:
            messages.warning(request, 'PDF export requires the reportlab package. Use CSV for now.')
            return redirect('courses:detail', pk=pk)
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        data = [['User', 'Email', 'Enrolled at']]
        for e in enrollments:
            data.append([e.user.get_full_name(), e.user.email, e.enrolled_at.strftime('%Y-%m-%d %H:%M')])
        t = Table(data)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ]))
        doc.build([Paragraph(f'Enrollment report: {course.fullname}', styles['Heading1']), t])
        response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="enrollment_{course.shortname}.pdf"'
        return response


# ----- Certificates (instructor issues to qualifying students) -----

@login_required
def course_certificates(request, pk):
    """Instructor: view qualifying students and issue certificates."""
    course = get_object_or_404(Course, pk=pk)
    if not _is_course_teacher(request, course):
        messages.error(request, 'Access denied.')
        return redirect('courses:detail', pk=pk)
    from .models import CourseCompletion
    enrolled = course.enrollments.filter(
        status='active', role='student'
    ).select_related('user')
    completed_ids = set(
        CourseCompletion.objects.filter(
            course=course, status__in=(CourseCompletion.STATUS_COMPLETE, CourseCompletion.STATUS_COMPLETE_PASS)
        ).values_list('user_id', flat=True)
    )
    already_issued = set(
        CourseCertificate.objects.filter(course=course).values_list('user_id', flat=True)
    )
    qualifying = [e for e in enrolled if e.user_id in completed_ids and e.user_id not in already_issued]
    issued = CourseCertificate.objects.filter(course=course).select_related('user', 'issued_by')
    return render(request, 'courses/certificates.html', {
        'course': course,
        'qualifying': qualifying,
        'already_issued': already_issued,
        'issued': issued,
    })


@login_required
def course_certificate_issue(request, pk, user_pk):
    """Instructor: issue certificate to a qualifying student."""
    course = get_object_or_404(Course, pk=pk)
    if not _is_course_teacher(request, course):
        messages.error(request, 'Access denied.')
        return redirect('courses:detail', pk=pk)
    from apps.users.models import User
    student = get_object_or_404(User, pk=user_pk)
    from .models import CourseCompletion
    comp = CourseCompletion.objects.filter(
        course=course, user=student,
        status__in=(CourseCompletion.STATUS_COMPLETE, CourseCompletion.STATUS_COMPLETE_PASS)
    ).first()
    if not comp:
        messages.error(request, 'Student has not completed the course.')
        return redirect('courses:certificates', pk=pk)
    cert, created = CourseCertificate.objects.get_or_create(
        user=student, course=course,
        defaults={'issued_by': request.user}
    )
    if not created:
        cert.issued_by = request.user
        cert.save(update_fields=['issued_by'])
    messages.success(request, f'Certificate issued to {student.get_full_name()}.')
    return redirect('courses:certificates', pk=pk)
