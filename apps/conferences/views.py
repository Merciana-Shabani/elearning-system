from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.views.generic import ListView
from . import views
from .models import ConferenceRoom
from .forms import ConferenceRoomForm


class RoomListView(LoginRequiredMixin, ListView):
    model = ConferenceRoom
    template_name = 'conferences/room_list.html'
    context_object_name = 'rooms'
    paginate_by = 20

    def get_queryset(self):
        return ConferenceRoom.objects.select_related(
            'host', 'course'
        ).order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_rooms'] = ConferenceRoom.objects.filter(
            is_active=True
        ).select_related('host', 'course')
        context['upcoming_rooms'] = ConferenceRoom.objects.filter(
            is_active=False, ended_at__isnull=True,
            scheduled_at__gte=timezone.now()
        ).select_related('host', 'course').order_by('scheduled_at')
        return context


@login_required
def create_room(request):
    if not request.user.can_manage_live_sessions:
        messages.error(request, "Instructor or moderator access required.")
        return redirect('conferences:list')
    if request.method == 'POST':
        form = ConferenceRoomForm(request.POST, user=request.user)
        if form.is_valid():
            room = form.save(commit=False)
            room.host = request.user
            room.save()
            messages.success(request, f'Room "{room.title}" created.')
            return redirect('conferences:room', slug=room.room_slug)
    else:
        form = ConferenceRoomForm(user=request.user)

    return render(request, 'conferences/create_room.html', {'form': form})


@login_required
def join_room(request, slug):
    room = get_object_or_404(ConferenceRoom, room_slug=slug)

    # Password check
    if room.require_password and room.host != request.user:
        submitted = request.POST.get('room_password', '')
        if request.method == 'POST' and submitted != room.room_password:
            messages.error(request, 'Incorrect room password.')
            return render(request, 'conferences/room_password.html', {'room': room})
        elif request.method == 'GET':
            return render(request, 'conferences/room_password.html', {'room': room})

    # Mark room as active when host joins
    if room.host == request.user and not room.is_active and not room.ended_at:
        room.is_active = True
        room.started_at = timezone.now()
        room.save(update_fields=['is_active', 'started_at'])

    return render(request, 'conferences/room.html', {'room': room})


@login_required
def end_room(request, slug):
    room = get_object_or_404(ConferenceRoom, room_slug=slug, host=request.user)
    if request.method == 'POST':
        room.is_active = False
        room.ended_at = timezone.now()
        room.save(update_fields=['is_active', 'ended_at'])
        messages.success(request, f'Session "{room.title}" has ended.')
    return redirect('conferences:list')


@login_required
def delete_room(request, slug):
    room = get_object_or_404(ConferenceRoom, room_slug=slug, host=request.user)
    if request.method == 'POST':
        title = room.title
        room.delete()
        messages.success(request, f'Room "{title}" deleted.')
    return redirect('conferences:list')

def set_signup_type(request):
    
    role = request.POST.get('signup_role', '')
    student_type = request.POST.get('signup_student_type', 'normal_staff')
    
    if role in ('student', 'teacher', 'moderator'):
        request.session['signup_role'] = role
        if role == 'student':
            request.session['signup_student_type'] = student_type
        else:
            request.session['signup_student_type'] = ''
    
    return redirect('account_signup')
 
 
 
def clear_signup_type(request):
    request.session.pop('signup_role', None)
    request.session.pop('signup_student_type', None)
    return redirect('account_signup')
