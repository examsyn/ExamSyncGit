import random
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseForbidden, JsonResponse, HttpResponseRedirect
from django.urls import reverse
import json
from ExamSync import settings
from .models import User, Role, UserRole, Course, Building, Program, College, Room, Section, SectionYearSem, Availability, UserAvailability, CourseModality, ExamSchedule, ProgramSection, CourseYearSem, ExamRemarks
from .forms import UserForm, RoleForm, UserRoleForm, CourseForm, BuildingForm, ProgramForm, CollegeForm, RoomForm, SectionForm, CourseYearSem, UserAvailabilityForm, CourseProgram, ExamScheduleForm, ExamRemarksForm, ExamScheduleUpdateForm
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .decorators import role_required, guest_required
from django.contrib.auth.hashers import make_password
from datetime import timedelta, datetime, time, date
from collections import defaultdict
from django.contrib import messages
from django import template
from django.conf import settings
from django.core.mail import send_mail
from django.utils.dateparse import parse_date
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.db import connection
from collections import defaultdict


def unauthorized_access(request):
    return render(request, 'unauthorized_access.html')

@login_required
@role_required('administrator')
def manage_users(request):
    search_query = request.GET.get('search', '')
    
    if search_query:
        users = User.objects.filter(
            Q(username__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )
    else:
        users = User.objects.all()
    
    user_roles = UserRole.objects.select_related('role').select_related('user').all()

    user_role_map = {}
    for user_role in user_roles:
        if user_role.user.user_id not in user_role_map:
            user_role_map[user_role.user.user_id] = []
        user_role_map[user_role.user.user_id].append(user_role.role.role_name)

    users_with_roles = [{'user': user, 'roles': user_role_map.get(user.user_id, [])} for user in users]

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'users': [
                {
                    'username': user['user'].username,
                    'first_name': user['user'].first_name,
                    'middle_name': user['user'].middle_name,
                    'last_name': user['user'].last_name,
                    'email_address': user['user'].email_address,
                    'contact_number': user['user'].contact_number,
                    'work_time': user['user'].work_time,
                    'status': user['user'].status,
                    'roles': user['roles'],
                    'user_id': user['user'].user_id
                }
                for user in users_with_roles
            ]
        })
    
    return render(request, 'manage_users.html', {'users_with_roles': users_with_roles, 'search_query': search_query})


@login_required
@role_required('administrator')
def create_user(request):
    search_query = request.GET.get('search', '')

    if search_query:
        users = User.objects.filter(
            Q(username__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )
    else:
        users = User.objects.all()
    
    user_roles = UserRole.objects.select_related('role').select_related('user').all()
    
    user_role_map = {}
    for user_role in user_roles:
        if user_role.user.user_id not in user_role_map:
            user_role_map[user_role.user.user_id] = []
        user_role_map[user_role.user.user_id].append(user_role.role.role_name)
    
    users_with_roles = [{'user': user, 'roles': user_role_map.get(user.user_id, [])} for user in users]

    if request.method == 'POST':
        form = UserForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)

            if user.work_time == "Full-Time":
                user.save()

                full_time_availability_ids = [1,2,3, 4,5,6, 7,8,9, 10,11,12, 13,14,15, 16,17,18]

                full_time_availability = Availability.objects.filter(availability_id__in=full_time_availability_ids)

                for availability in full_time_availability:
                    UserAvailability.objects.create(user=user, availability=availability)

                assigned_ids = [a.availability_id for a in full_time_availability]
                print("Assigned Availability IDs for Full-Time User:", assigned_ids)

            user.save()

            return redirect('manage_users')

        else:
            error_message = "There was an error creating this user. Make sure the user does not exist!"
            print(form.errors)
    else:
        form = UserForm()
        error_message = None

    return render(request, 'manage_users.html', {
        'form': form,
        'error_message': error_message,
        'users_with_roles': users_with_roles,
        'search_query': search_query
    })



@login_required
@role_required('administrator')
def edit_user(request, user_id):
    user = get_object_or_404(User, pk=user_id)

    if request.method == 'POST':
        form = UserForm(request.POST, instance=user)

        if form.is_valid():
            cleaned_data = form.cleaned_data

            new_password = cleaned_data.get('password')
            if new_password:
                user.set_password(new_password)

            user.username = cleaned_data.get('username', user.username)
            user.first_name = cleaned_data.get('first_name', user.first_name)
            user.middle_name = cleaned_data.get('middle_name', user.middle_name)
            user.last_name = cleaned_data.get('last_name', user.last_name)
            user.email_address = cleaned_data.get('email_address', user.email_address)
            user.contact_number = cleaned_data.get('contact_number', user.contact_number)
            
            new_work_time = cleaned_data.get('work_time', user.work_time)
            user.status = cleaned_data.get('status', user.status)

            user.save()

            if new_work_time == "Full-Time":
                UserAvailability.objects.filter(user=user).delete()

                full_time_availability_ids = [1,2,3, 4,5,6, 7,8,9, 10,11,12, 13,14,15, 16,17,18]

                full_time_availability = Availability.objects.filter(availability_id__in=full_time_availability_ids)

                for availability in full_time_availability:
                    UserAvailability.objects.create(user=user, availability=availability)

                assigned_ids = [a.availability_id for a in full_time_availability]
                print("Assigned Availability IDs for Full-Time User:", assigned_ids)

            roles_selected = request.POST.getlist('roles')
            UserRole.objects.filter(user=user).delete()

            for role_id in roles_selected:
                role = get_object_or_404(Role, pk=role_id)
                UserRole.objects.create(user=user, role=role)

            return redirect('manage_users')

    else:
        form = UserForm(instance=user)
        form.fields['password'].widget.attrs['placeholder'] = 'Enter current password to keep the same!'

    roles = Role.objects.all()
    user_roles = user.user_roles.values_list('role_id', flat=True)
    
    return render(request, 'manage_users.html', {
        'form': form, 
        'user': user, 
        'roles': roles, 
        'user_roles': user_roles
    })


@login_required
@role_required('administrator')
def delete_user(request, user_id):
    user = get_object_or_404(User, user_id=user_id)
    if request.method == 'POST':
        user.delete()
        return redirect('manage_users')
    return render(request, 'confirm_delete.html', {'user': user})


@login_required
@role_required('administrator')
def add_role(request, user_id):
    if request.method == "POST":
        role_name = request.POST.get("role")
        user = get_object_or_404(User, id=user_id)
        role = get_object_or_404(Role, name=role_name)
        user.roles.add(role)
        return JsonResponse({'success': True})
    return JsonResponse({'success': False}, status=400)

@login_required
@role_required('administrator')
def add_role_to_user(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    
    if request.method == 'POST':
        role_id = request.POST.get('role_id')
        if role_id:
            role = get_object_or_404(Role, pk=role_id)
            user.roles.add(role)
            user.save()
            return redirect('edit_user', user_id=user.id)
    
    roles = Role.objects.all()
    return render(request, 'manage_users.html', {'user': user, 'roles': roles})

def custom_404_view(request, exception=None):
    return redirect('login_page')

@guest_required
def login_view(request, role=None):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            if user.status != 'Active':
                error_message = 'Your account is not active. Please contact support.'
                return render(request, 'login-pages/login.html', {'role': role, 'error': error_message})

            user_roles = UserRole.objects.filter(user=user).values_list('role__role_name', flat=True)
            user_roles_lower = [r.lower() for r in user_roles]

            if user_roles_lower:
                if role.lower() in user_roles_lower:
                    login(request, user)
                    return redirect(f'/dashboard-{role}/')
                else:
                    first_role = user_roles_lower[0]
                    login(request, user)
                    return redirect(f'/dashboard-{first_role}/')
            else:
                error_message = 'You do not have any roles assigned. Please contact support.'
                return render(request, 'login-pages/login.html', {'role': role, 'error': error_message})
        else:
            return render(request, 'login-pages/login.html', {'role': role, 'error': 'Invalid credentials'})

    return render(request, 'login-pages/login.html')

# DASHBOARDS
@login_required
def dashboard_view(request, role):
    user_roles = UserRole.objects.filter(user=request.user).values_list('role__role_name', flat=True)
    if role not in [r.lower() for r in user_roles]:
        return redirect('login_administrator')

    context = {'user': request.user}

    if role == 'faculty':
        schedules = ExamSchedule.objects.filter(proctor=request.user).select_related(
            'courseYearSem__course', 'room', 'sectionYearSem__section'
        )
        context['schedules'] = schedules

    elif role == 'dean':
        remarks = ExamRemarks.objects.filter(status='Pending').select_related('examSchedule', 'examSchedule__proctor')
        context['remarks'] = remarks

    return render(request, f'dashboard-pages/dashboard-{role}.html', context)



def logout_view(request):
    logout(request)
    return redirect('login_page')


register = template.Library()

@register.filter
def has_role(user, role_name):
    role = Role.objects.filter(role_name=role_name).first()
    return UserRole.objects.filter(user=user, role=role).exists()

# MANAGE COURSES
@login_required
@role_required('scheduler')
def manage_courses(request):
    return render(request, 'course-management/manage_courses.html')


@login_required
@role_required('scheduler')
def course_list(request):
    search_query = request.GET.get('search', '')
    
    if search_query:
        courses = Course.objects.filter(
            Q(course_code__icontains=search_query) |
            Q(course_name__icontains=search_query)
        )
    else:
        courses = Course.objects.all()
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'courses': [
                {
                    'course_code': course.course_code,
                    'course_name': course.course_name,
                    'course_id': course.course_id
                }
                for course in courses
            ]
        })
    
    return render(request, 'course-management/course_list.html', {'courses': courses, 'search_query': search_query})


@login_required
@role_required('scheduler')
def create_course(request):
    if request.method == 'POST':
        form = CourseForm(request.POST)
        if form.is_valid():
            course = form.save(commit=False)
            course.save()

            program = form.cleaned_data['program']
            course_program = CourseProgram(course=course, program=program)
            course_program.save()

            semester = form.cleaned_data['semester']
            course_year_sem = CourseYearSem(course=course, courseProgram=course_program, yearSem=semester)
            course_year_sem.save()

            return redirect('course_list')
    else:
        form = CourseForm()

    return render(request, 'course-management/create_course.html', {'form': form})


@login_required
@role_required('scheduler')
def edit_course(request, course_id):
    course = get_object_or_404(Course, course_id=course_id)
    existing_course_program = CourseProgram.objects.filter(course=course).first()
    existing_course_year_sem = CourseYearSem.objects.filter(course=course).first()

    if request.method == 'POST':
        form = CourseForm(request.POST, instance=course)
        if form.is_valid():
            course = form.save()

            new_program = form.cleaned_data['program']
            if existing_course_program and existing_course_program.program != new_program:
                existing_course_program.program = new_program
                existing_course_program.save()
            elif not existing_course_program:
                CourseProgram.objects.create(course=course, program=new_program)

            new_year_sem = form.cleaned_data['semester']
            if existing_course_year_sem and existing_course_year_sem.yearSem != new_year_sem:
                existing_course_year_sem.yearSem = new_year_sem
                existing_course_year_sem.save()
            elif not existing_course_year_sem:
                course_program = CourseProgram.objects.filter(course=course).first()
                CourseYearSem.objects.create(course=course, courseProgram=course_program, yearSem=new_year_sem)

            return redirect('course_list') 
    else:
        initial_data = {
            'program': existing_course_program.program if existing_course_program else None,
            'semester': existing_course_year_sem.yearSem if existing_course_year_sem else None,
        }
        form = CourseForm(instance=course, initial=initial_data)

    return render(request, 'course-management/edit_course.html', {'form': form, 'course': course})



@login_required
@role_required('scheduler')
def delete_course(request, course_id):
    course = get_object_or_404(Course, course_id=course_id)
    if request.method == 'POST':
        course.delete()
        return redirect('course_list')
    return render(request, 'course-management/confirm_delete_course.html', {'course': course})


# MANAGE BUILDINGS


@login_required
@role_required('scheduler')
def building_list(request):
    search_query = request.GET.get('search', '')

    if request.method == 'POST':  
        form = BuildingForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Building created successfully!")
            return redirect('building_list')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = BuildingForm()

    if search_query:
        buildings = Building.objects.filter(
            Q(building_name__icontains=search_query) |
            Q(building_code__icontains=search_query)
        )
    else:
        buildings = Building.objects.all()

    return render(request, 'building-management/building_list.html', {
        'buildings': buildings,
        'form': form,
        'search_query': search_query
    })


@login_required
@role_required('scheduler')
def edit_building(request, building_id):
    building = get_object_or_404(Building, building_id=building_id)
    if request.method == 'POST':
        form = BuildingForm(request.POST, instance=building)
        if form.is_valid():
            form.save()
            return redirect('building_list')
    else:
        form = BuildingForm(instance=building)
    
    return render(request, 'building-management/edit_building.html', {'form': form, 'building': building})


@login_required
@role_required('scheduler')
def delete_building(request, building_id):
    building = get_object_or_404(Building, building_id=building_id)
    if request.method == 'POST':
        building.delete()
        return redirect('building_list')
    return render(request, 'building-management/confirm_delete_building.html', {'building': building})


# MANAGE ROOMS
@login_required
@role_required('scheduler')
def room_list(request):
    search_query = request.GET.get('search', '')

    if request.method == 'POST':
        form = RoomForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Room created successfully!")
            return redirect('room_list')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = RoomForm()

    if search_query:  # Handle search
        rooms = Room.objects.filter(
            Q(room_name__icontains=search_query) |
            Q(room_id__icontains=search_query)
        )
    else:
        rooms = Room.objects.all()

    return render(request, 'room-management/room_list.html', {
        'rooms': rooms,
        'form': form,
        'search_query': search_query
    })


@login_required
@role_required('scheduler')
def edit_room(request, room_id):
    room = get_object_or_404(Room, room_id=room_id)
    buildings = Building.objects.all()
    
    if request.method == 'POST':
        form = RoomForm(request.POST, instance=room)
        if form.is_valid():
            form.save()
            return redirect('room_list')
        else:
            print(form.errors)
    else:
        form = RoomForm(instance=room)
    
    return render(request, 'room-management/edit_room.html', {'form': form, 'buildings': buildings, 'room': room})



@login_required
@role_required('scheduler')
def delete_room(request, room_id):
    room = get_object_or_404(Room, room_id=room_id)
    if request.method == 'POST':
        room.delete()
        return redirect('room_list')
    return render(request, 'room-management/confirm_delete_room.html', {'room': room})


# MANAGE PROGRAMS
@login_required
@role_required('scheduler')
def program_list(request):
    search_query = request.GET.get('search', '')

    if search_query:
        programs = Program.objects.filter(
            Q(program_name__icontains=search_query) |
            Q(program_id__icontains=search_query)
        )
    else:
        programs = Program.objects.all()

    if request.method == 'POST':
        form = ProgramForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('program_list')

    else:
        form = ProgramForm()

    return render(request, 'program-management/program_list.html', {
        'programs': programs,
        'search_query': search_query,
        'form': form
    })


@login_required
@role_required('scheduler')
def edit_program(request, program_id):
    program = get_object_or_404(Program, pk=program_id)
    colleges = College.objects.all()

    if request.method == 'POST':
        form = ProgramForm(request.POST, instance=program)
        if form.is_valid():
            form.save()
            return redirect('program_list')
    else:
        form = ProgramForm(instance=program)

    return render(request, 'program-management/edit_program.html', {
        'program': program,
        'colleges': colleges,
        'form': form
    })


@login_required
@role_required('scheduler')
def delete_program(request, program_id):
    program = get_object_or_404(Program, program_id=program_id)
    if request.method == 'POST':
        program.delete()
        return redirect('program_list')
    return render(request, 'program-management/confirm_delete_program.html', {'program': program})


# MANAGE COLLEGES
@login_required
@role_required('scheduler')
def college_list(request):
    search_query = request.GET.get('search', '')

    if search_query:
        colleges = College.objects.filter(
            Q(college_name__icontains=search_query)
        )
    else:
        colleges = College.objects.all()

    if request.method == 'POST':
        form = CollegeForm(request.POST)
        if form.is_valid():
            college = form.save()
            return redirect('college_list')

    else:
        form = CollegeForm()

    return render(request, 'college-management/college_list.html', {
        'colleges': colleges,
        'search_query': search_query,
        'form': form
    })


@login_required
@role_required('scheduler')
def edit_college(request, college_id):
    college = get_object_or_404(College, college_id=college_id)
    if request.method == 'POST':
        form = CollegeForm(request.POST, instance=college)
        if form.is_valid():
            form.save()
            return redirect('college_list')
    else:
        form = CollegeForm(instance=college)
    
    return render(request, 'college-management/edit_college.html', {'form': form, 'college': college})


@login_required
@role_required('scheduler')
def delete_college(request, college_id):
    college = get_object_or_404(College, college_id=college_id)
    if request.method == 'POST':
        college.delete()
        return redirect('college_list')
    return render(request, 'college-management/confirm_delete_college.html', {'college': college})



# MANAGE SECTIONS
@login_required
@role_required('scheduler')
def manage_sections(request):
    return render(request, 'section-management/manage_sections.html')


@login_required
@role_required('scheduler')
def section_list(request):
    search_query = request.GET.get('search', '')
    
    if search_query:
        sections = Section.objects.filter(
            Q(section_name__icontains=search_query)
        )
    else:
        sections = Section.objects.all()
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'sections': [
                {
                    'section_name': section.section_name,
                    'section_id': section.section_id
                }
                for section in sections
            ]
        })
    
    return render(request, 'section-management/section_list.html', {'sections': sections, 'search_query': search_query})


@login_required
@role_required('scheduler')
def create_section(request):
    if request.method == 'POST':
        form = SectionForm(request.POST)
        if form.is_valid():
            section = form.save()

            program = form.cleaned_data['program']
            program_section = ProgramSection.objects.create(section=section, program=program)

            year_semesters = form.cleaned_data['year_semesters']
            for year_semester in year_semesters:
                SectionYearSem.objects.create(
                    section=section,
                    yearSem=year_semester,
                    programSection=program_section
                )

            return redirect('section_list')
    else:
        form = SectionForm()

    return render(request, 'section-management/create_section.html', {'form': form})



@login_required
@role_required('scheduler')
def edit_section(request, section_id):
    section = get_object_or_404(Section, pk=section_id)

    program_section = ProgramSection.objects.filter(section=section).first()

    existing_year_sems = SectionYearSem.objects.filter(section=section)

    if request.method == 'POST':
        form = SectionForm(request.POST, instance=section)
        if form.is_valid():
            section = form.save()

            program_section_obj = form.cleaned_data.get('program')
            if program_section:
                program_section.program = program_section_obj
                program_section.save()
            else:
                ProgramSection.objects.create(section=section, program=program_section_obj)

            selected_year_sems = form.cleaned_data.get('year_semesters', [])

            for year_sem in existing_year_sems:
                if year_sem.yearSem not in selected_year_sems:
                    year_sem.delete()

            for year_semester in selected_year_sems:
                if not existing_year_sems.filter(yearSem=year_semester).exists():
                    SectionYearSem.objects.create(section=section, yearSem=year_semester, programSection=program_section)

            return redirect('section_list')
    else:
        initial_data = {
            'program': program_section.program if program_section else None,
            'year_semesters': [year_sem.yearSem for year_sem in existing_year_sems]
        }
        form = SectionForm(instance=section, initial=initial_data)

    return render(request, 'section-management/edit_section.html', {
        'form': form,
        'section': section,
        'year_sems': existing_year_sems,
        'program': program_section.program if program_section else None
    })


@login_required
@role_required('scheduler')
def delete_section(request, section_id):
    section = get_object_or_404(Section, section_id=section_id)
    if request.method == 'POST':
        section.delete()
        return redirect('section_list')
    return render(request, 'section-management/confirm_delete_section.html', {'section': section})


# MANAGE AVAILABILITY
@login_required
@role_required('faculty')
def manage_availability(request):
    if request.method == 'POST':
        selected_availability_ids = request.POST.getlist('checkbox')

        UserAvailability.objects.filter(user=request.user).delete()

        for availability_id in selected_availability_ids:
            try:
                availability = Availability.objects.get(availability_id=availability_id)
                UserAvailability.objects.create(
                    user=request.user,
                    availability=availability
                )
            except Availability.DoesNotExist:
                continue

        messages.success(request, "Availability Saved!")
        return redirect('manage_availability')

    else:
        available_times = Availability.objects.all()
        user_availabilities = UserAvailability.objects.filter(user=request.user)

        user_availability_ids = set(user_availabilities.values_list('availability_id', flat=True))

        availability_by_day = {}
        for availability in available_times:
            day = availability.availabilityDay
            if day not in availability_by_day:
                availability_by_day[day] = []
            availability_by_day[day].append(availability)

        return render(request, 'availability-management/manage_availability.html', {
            'availability_by_day': availability_by_day,
            'user_availability_ids': user_availability_ids
        })


from .forms import CourseModalityForm


# MANAGE MODALITY
@login_required
@role_required('scheduler')
def assign_course_modality(request):
    if request.method == 'POST':
        form = CourseModalityForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data['user']
            course = form.cleaned_data['course']

            if CourseModality.objects.filter(user=user, course=course).exists():
                messages.error(request, f"{user.first_name} {user.last_name} is already assigned to this course!")
            else:
                form.save()
                messages.success(request, f"Course modality assigned to {user.first_name} {user.last_name} successfully!")
            return redirect('assign_course_modality')

    else:
        form = CourseModalityForm()

    context = {
        'form': form
    }
    return render(request, 'modality-management/assign_course_modality.html', context)


@login_required
@role_required('bayanihan leader')
def edit_course_modality(request):
    user = request.user

    course_modalities = CourseModality.objects.filter(user=user)

    if not course_modalities.exists():
        return render(request, 'assigned_modalities.html', {
            'message': 'You have not been assigned any course modalities yet.'
        })

    if request.method == 'POST':
        modality_id = request.POST.get('modality_id')
        modality = get_object_or_404(CourseModality, courseModality_id=modality_id, user=user)

        modality.modality = request.POST.get('modality')
        modality.save()

        return redirect('edit-course-modality')

    return render(request, 'modality-management/assigned_modalities.html', {
        'course_modalities': course_modalities
    })


# VIEW SCHEDULES IN DIFFERENT USER

@login_required
@role_required('dean')
def exam_schedules_dean(request):
    schedules = ExamSchedule.objects.filter(status="Scheduled").select_related(
        'room',
        'courseProgram__course',
        'sectionYearSem__section',
        'proctor'
    )

    schedules_by_day = defaultdict(list)
    for schedule in schedules:
        schedules_by_day[schedule.day].append(schedule)

    sorted_days = sorted(schedules_by_day.keys())

    building_data = {}
    for schedule in schedules:
        building = schedule.room.building if schedule.room else "No Building"
        if building not in building_data:
            building_data[building] = {}

        if schedule.room and schedule.room not in building_data[building]:
            building_data[building][schedule.room] = []

        if schedule.room:
            building_data[building][schedule.room].append(schedule)

    time_slots = [(hour, minute) for hour in range(7, 21) for minute in [0, 30]]
    for schedule in schedules:
        schedule.duration = (schedule.end_time.hour * 60 + schedule.end_time.minute) - (schedule.start_time.hour * 60 + schedule.start_time.minute)

    return render(request, 'schedules-views/view_schedule_dean.html', {
        'schedules_by_day': schedules_by_day,
        'sorted_days': sorted_days,
        'building_data': building_data,
        'time_slots': time_slots,
    })

@login_required
@role_required('scheduler')
def exam_schedules_scheduler(request):
    schedules = ExamSchedule.objects.filter(status="Approved").select_related(
        'room',
        'courseProgram__course',
        'sectionYearSem__section',
        'proctor'
    ).all()

    schedules_by_day = defaultdict(list)
    for schedule in schedules:
        schedules_by_day[schedule.day].append(schedule)

    sorted_days = sorted(schedules_by_day.keys())

    building_data = {}
    for schedule in schedules:
        building = schedule.room.building if schedule.room else "No Building"
        if building not in building_data:
            building_data[building] = {}

        if schedule.room and schedule.room not in building_data[building]:
            building_data[building][schedule.room] = []

        if schedule.room:
            building_data[building][schedule.room].append(schedule)

    time_slots = [(hour, minute) for hour in range(7, 21) for minute in [0, 30]]
    for schedule in schedules:
        schedule.duration = (schedule.end_time.hour * 60 + schedule.end_time.minute) - (schedule.start_time.hour * 60 + schedule.start_time.minute)

    return render(request, 'schedules-views/view_schedule_scheduler.html', {
        'schedules_by_day': schedules_by_day,
        'sorted_days': sorted_days,
        'building_data': building_data,
        'time_slots': time_slots,
    })

@login_required
@role_required('faculty')
def exam_schedules_faculty(request):
    schedules = ExamSchedule.objects.filter(status="Approved").select_related(
        'room',
        'courseProgram__course',
        'sectionYearSem__section',
        'proctor'
    ).all()

    schedules_by_day = defaultdict(list)
    for schedule in schedules:
        schedules_by_day[schedule.day].append(schedule)

    sorted_days = sorted(schedules_by_day.keys())

    building_data = {}
    for schedule in schedules:
        building = schedule.room.building if schedule.room else "No Building"
        if building not in building_data:
            building_data[building] = {}

        if schedule.room and schedule.room not in building_data[building]:
            building_data[building][schedule.room] = []

        if schedule.room:
            building_data[building][schedule.room].append(schedule)

    time_slots = [(hour, minute) for hour in range(7, 21) for minute in [0, 30]]
    for schedule in schedules:
        schedule.duration = (schedule.end_time.hour * 60 + schedule.end_time.minute) - (schedule.start_time.hour * 60 + schedule.start_time.minute)

    return render(request, 'schedules-views/view_schedule_faculty.html', {
        'schedules_by_day': schedules_by_day,
        'sorted_days': sorted_days,
        'building_data': building_data,
        'time_slots': time_slots,
    })


@login_required
def exam_schedules_outside(request):
    schedules = ExamSchedule.objects.select_related(
        'room',
        'courseProgram__course',
        'sectionYearSem__section',
        'proctor'
    ).all()

    schedules_by_day = defaultdict(list)
    for schedule in schedules:
        schedules_by_day[schedule.day].append(schedule)

    sorted_days = sorted(schedules_by_day.keys())

    building_data = {}
    for schedule in schedules:
        building = schedule.room.building if schedule.room else "No Building"
        if building not in building_data:
            building_data[building] = {}

        if schedule.room and schedule.room not in building_data[building]:
            building_data[building][schedule.room] = []

        if schedule.room:
            building_data[building][schedule.room].append(schedule)

    time_slots = [(hour, minute) for hour in range(7, 21) for minute in [0, 30]]
    for schedule in schedules:
        schedule.duration = (schedule.end_time.hour * 60 + schedule.end_time.minute) - (schedule.start_time.hour * 60 + schedule.start_time.minute)

    return render(request, 'schedules-views/view_schedule_outside.html', {
        'schedules_by_day': schedules_by_day,
        'sorted_days': sorted_days,
        'building_data': building_data,
        'time_slots': time_slots,
    })

# MANAGE SCHEDULES
@login_required
@role_required('scheduler')
def exam_schedule_list(request):
    exam_schedules = ExamSchedule.objects.filter(
        Q(status="Declined")
    ).select_related(
        'room',
        'courseProgram__course',
        'sectionYearSem__section',
        'proctor'
    )
    
    return render(request, 'exam-schedule-management/exam_schedule_list.html', {'exam_schedules': exam_schedules})


@login_required
@role_required('scheduler')
def exam_schedules(request):
    schedules = ExamSchedule.objects.filter(
        Q(status="Declined") | Q(status="Scheduled")
    ).select_related(
        'room',
        'courseProgram__course',
        'sectionYearSem__section',
        'proctor'
    )

    schedules_by_day = defaultdict(list)
    for schedule in schedules:
        schedules_by_day[schedule.day].append(schedule)

    declined_days = {day: any(schedule.status == "Declined" for schedule in schedules)
                     for day, schedules in schedules_by_day.items()}

    sorted_days = sorted(schedules_by_day.keys())

    building_data = {}
    for schedule in schedules:
        building = schedule.room.building if schedule.room else "No Building"
        if building not in building_data:
            building_data[building] = {}

        if schedule.room and schedule.room not in building_data[building]:
            building_data[building][schedule.room] = []

        if schedule.room:
            building_data[building][schedule.room].append(schedule)

    for building in building_data:
        sorted_rooms = sorted(building_data[building].keys(), key=lambda room: room.room_id)
        sorted_building_data = {room: building_data[building][room] for room in sorted_rooms}
        building_data[building] = sorted_building_data

    time_slots = [(hour, minute) for hour in range(7, 21) for minute in [0, 30]]
    for schedule in schedules:
        schedule.duration = (schedule.end_time.hour * 60 + schedule.end_time.minute) - (schedule.start_time.hour * 60 + schedule.start_time.minute)

    return render(request, 'exam-schedule-management/exam_schedules.html', {
        'schedules_by_day': schedules_by_day,
        'sorted_days': sorted_days,
        'building_data': building_data,
        'time_slots': time_slots,
        'declined_days': declined_days,
    })


@login_required
@role_required('scheduler')
def fetch_courses(request):
    if request.method == 'POST':
        import json
        data = json.loads(request.body)
        semester = data.get('semester')

        year_sem_ids = []
        if semester == 'first':
            year_sem_ids = [1, 3, 5, 7]
        elif semester == 'second':
            year_sem_ids = [2, 4, 6, 8]

        course_year_sems = CourseYearSem.objects.filter(yearSem_id__in=year_sem_ids).select_related('course')
        courses = [
            {"id": c.course.course_id, "course_code": c.course.course_code, "course_name": c.course.course_name}
            for c in course_year_sems
        ]
        seen = set()
        unique_courses = []
        for course in courses:
            if course['course_code'] not in seen:
                unique_courses.append(course)
                seen.add(course['course_code'])

        return JsonResponse({"courses": unique_courses})
    
@login_required
@role_required('scheduler')
def fetch_rooms(request):
    rooms = Room.objects.all()
    room_data = [{"id": room.id, "room_name": room.room_name} for room in rooms]
    return JsonResponse({"rooms": room_data})


from django.db import connection

@login_required
@role_required('scheduler')
def delete_schedule_for_day(request, day):
    if request.method == 'POST':
        with connection.cursor() as cursor:
            cursor.execute("SET foreign_key_checks = 0;")
            ExamSchedule.objects.filter(day=day).delete()
            cursor.execute("SET foreign_key_checks = 1;")
        
        messages.success(request, f"All schedules for Day {day} have been deleted.")
        return HttpResponseRedirect(reverse('exam_schedules'))
    
    return HttpResponseRedirect(reverse('exam_schedules'))


@login_required
@csrf_exempt
@role_required('scheduler')
def update_schedule_status(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            action = data.get("action")
            day = data.get("day")
            custom_message = data.get("custom_message", "") 

            if not action or action not in ["approve", "reschedule", "scheduled"]:
                return JsonResponse({"error": "Invalid action provided."}, status=400)

            day_date = parse_date(day)
            if not day_date:
                return JsonResponse({"error": "Day must be in YYYY-MM-DD format."}, status=400)

            if action == "approve":
                status = "Approved"
            elif action == "reschedule":
                status = "Declined"
            elif action == "scheduled":
                status = "Scheduled"

            updated_count = ExamSchedule.objects.filter(day=day_date).update(status=status)

            if status == "Scheduled":
                with connection.cursor() as cursor:
                    cursor.execute("""
                        SELECT u.email_address 
                        FROM tbl_users u
                        JOIN tbl_userRole ur ON u.user_id = ur.user_id
                        JOIN tbl_roles r ON ur.role_id = r.role_id
                        WHERE r.role_name = 'Dean'
                    """)
                    dean_emails = [row[0] for row in cursor.fetchall()]

                if dean_emails:
                    subject = f"ExamSync: Exam Schedules Pending Approval"
                    message = f"The exam schedule for {day} has been scheduled and is pending approval. Please check the system for details."
                    from_email = settings.DEFAULT_FROM_EMAIL
                    
                    send_mail(
                        subject,
                        message,
                        from_email,
                        dean_emails,
                        fail_silently=False,
                    )
                    messages.success(request, f"Schedules for {day} have been updated to 'Scheduled' and emails have been sent to Deans.")
                else:
                    messages.warning(request, "No Deans found to send the email.")

            if status == "Declined":
                with connection.cursor() as cursor:
                    cursor.execute("""
                        SELECT u.email_address 
                        FROM tbl_users u
                        JOIN tbl_userRole ur ON u.user_id = ur.user_id
                        JOIN tbl_roles r ON ur.role_id = r.role_id
                        WHERE r.role_name = 'Scheduler'
                    """)
                    scheduler_emails = [row[0] for row in cursor.fetchall()]

                if scheduler_emails:
                    subject = f"ExamSync: Exam Schedule was Declined by Dean"
                    message = f"The exam schedule for {day} has been declined. /br{custom_message}" if custom_message else f"The exam schedule for {day} has been declined."
                    from_email = settings.DEFAULT_FROM_EMAIL
                    
                    send_mail(
                        subject,
                        message,
                        from_email,
                        scheduler_emails,
                        fail_silently=False,
                    )
                    messages.success(request, f"Schedules for {day} have been updated to 'Declined' and emails have been sent to Schedulers.")
                else:
                    messages.warning(request, "No Schedulers found to send the email.")

            if status == "Approved":
                with connection.cursor() as cursor:
                    cursor.execute("""
                        SELECT u.email_address 
                        FROM tbl_users u
                        JOIN tbl_userRole ur ON u.user_id = ur.user_id
                        JOIN tbl_roles r ON ur.role_id = r.role_id
                        WHERE r.role_name = 'Scheduler'
                    """)
                    scheduler_emails = [row[0] for row in cursor.fetchall()]

                if scheduler_emails:
                    subject = f"ExamSync: Exam Schedules Approved"
                    message = f"The exam schedule for {day} has been approved."
                    from_email = settings.DEFAULT_FROM_EMAIL
                    
                    send_mail(
                        subject,
                        message,
                        from_email,
                        scheduler_emails,
                        fail_silently=False,
                    )
                    messages.success(request, f"Schedules for {day} have been updated to 'Approved' and emails have been sent to Schedulers.")
                else:
                    messages.warning(request, "No Schedulers found to send the email.")

            return JsonResponse({"success": True, "status": status, "updated_count": updated_count})

        except Exception as e:
            print(f"Error: {e}")
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request method."}, status=405)

@login_required
@role_required('scheduler')
def update_exam_schedule(request, exam_schedule_id):
    exam_schedule = get_object_or_404(
        ExamSchedule.objects.filter(Q(examSchedule_id=exam_schedule_id) & Q(status="Declined"))
    )

    if request.method == "POST":
        form = ExamScheduleUpdateForm(request.POST, instance=exam_schedule)
        if form.is_valid():
            form.save()
            return redirect('exam_schedule_detail', exam_schedule_id=exam_schedule.examSchedule_id)
    else:
        form = ExamScheduleUpdateForm(instance=exam_schedule)

    return render(request, 'exam-schedule-management/exam_schedule_update.html', {'form': form})


def initialize_population(size, courses, days, rooms, proctors, time_slots, exam_duration):
    """
    Initialize the population for the Genetic Algorithm with a deterministic room allocation strategy.
    This ensures rooms are consistently assigned to the exams while respecting time slot usage and avoiding conflicts
    for courses with the same courseYearSem_id and courseProgram_id.
    """
    population = []

    room_availability = {room.room_id: {day: set() for day in days} for room in rooms}
    course_section_counts = {
        course.course_id: SectionYearSem.objects.filter(
            programSection__program=course.courseProgram.program,
            yearSem=course.yearSem
        ).count()
        for course in courses
    }

    # Sort courses based on section count and course program id
    courses_sorted = sorted(courses, key=lambda c: (-course_section_counts[c.course_id], c.courseProgram.program.program_id))

    course_groups = defaultdict(list)
    for course in courses_sorted:  # Use the sorted courses
        key = (course.courseProgram_id, course.yearSem_id)
        course_groups[key].append(course)

    for _ in range(size):
        schedule = []
        day_index = 0 

        course_schedule_conflicts = {
            key: {day: set() for day in days} for key in course_groups
        }

        for course_group, course_list in course_groups.items():
            available_time_slots = set(time_slots) 

            time_slot_counter = 0 
            for course in course_list:
                course_id = course.course_id
                course_key = (course.courseProgram_id, course.yearSem_id)

                day = days[day_index]
                day_index = (day_index + 1) % len(days)

                available_time_slot = None
                for time_slot in available_time_slots:
                    time_slot_str = time_slot.time()

                    if time_slot_str not in course_schedule_conflicts[course_key][day]:
                        available_rooms = [
                            room.room_id for room in rooms
                            if time_slot_str not in room_availability[room.room_id][day]
                        ]

                        if available_rooms:
                            available_time_slot = time_slot_str
                            room_id = available_rooms[0]
                            room_availability[room_id][day].add(available_time_slot)
                            break
                if not available_time_slot:
                    for time_slot in time_slots:
                        time_slot_str = time_slot.time()

                        if time_slot_str not in course_schedule_conflicts[course_key][day]:
                            available_rooms = [
                                room.room_id for room in rooms
                                if time_slot_str not in room_availability[room.room_id][day]
                            ]
                            if available_rooms:
                                available_time_slot = time_slot_str
                                room_id = available_rooms[0]
                                room_availability[room_id][day].add(available_time_slot)
                                break

                if not available_time_slot:
                    available_time_slot = time_slots[0].time()
                course_schedule_conflicts[course_key][day].add(available_time_slot)
                proctor_id = random.choice(proctors).user_id

                schedule.append([course_id, day, available_time_slot, room_id, proctor_id])
                time_slot_counter += 1

        population.append(schedule)

    return population


def generate_time_slots(start_time, end_time, exam_duration):
    current_time = start_time
    time_slots = []
    while current_time + timedelta(minutes=exam_duration) <= end_time:
        time_slots.append(current_time)
        current_time += timedelta(minutes=exam_duration)
    return time_slots

def fitness_function(schedule, courses_by_yearsem_program, exam_duration):
    """
    Fitness function that evaluates a schedule based on given constraints.
    """
    score = 0
    used_rooms = {}
    used_proctors = defaultdict(set)
    conflicting_courses = defaultdict(list)
    program_day_count = defaultdict(int)
    program_timeslot_usage = defaultdict(set)

    for exam in schedule:
        course_id, day, start_time, room_id, proctor_id = exam

        if (day, start_time, room_id) in used_rooms:
            score -= 10
        else:
            used_rooms[(day, start_time, room_id)] = True

        if (day, start_time) in used_proctors[proctor_id]:
            score -= 50
        else:
            used_proctors[proctor_id].add((day, start_time))

        course = courses_by_yearsem_program[course_id]
        program_id = course.courseProgram.program.program_id
        yearSem_id = course.yearSem.yearSem_id

        if (day, start_time) in program_timeslot_usage[(program_id, yearSem_id)]:
            score -= 200
        else:
            program_timeslot_usage[(program_id, yearSem_id)].add((day, start_time))

        program_day_count[(program_id, yearSem_id, day)] += 1
        if program_day_count[(program_id, yearSem_id, day)] > 3:
            score -= 100

        conflicting_courses[(program_id, yearSem_id)].append((day, start_time))

    for key, exams in conflicting_courses.items():
        seen_timeslots = set()
        for exam in exams:
            if exam in seen_timeslots:
                score -= 200
            seen_timeslots.add(exam)

    return score



def selection(population, fitness_scores):
    sorted_population = sorted(zip(population, fitness_scores), key=lambda x: x[1], reverse=True)
    return [schedule for schedule, _ in sorted_population[:len(population) // 2]]

def crossover(parent1, parent2):
    cut = len(parent1) // 2
    child1 = parent1[:cut] + parent2[cut:]
    child2 = parent2[:cut] + parent1[cut:]
    return child1, child2

def mutate(schedule, mutation_rate, days, rooms, proctors, time_slots, courses_by_yearsem_program, exam_duration):
    """
    Introduce mutations in the schedule while respecting room availability and no back-to-back constraints.
    """
    used_rooms_by_timeslot = defaultdict(set)
    used_proctors_by_timeslot = defaultdict(set)

    for exam in schedule:
        used_rooms_by_timeslot[(exam[1], exam[2])].add(exam[3])
        used_proctors_by_timeslot[(exam[1], exam[2])].add(exam[4])

    day_time_slots = {day: [] for day in days}
    for time_slot in time_slots:
        for day in days:
            day_time_slots[day].append(time_slot.time())

    for exam in schedule:
        if random.random() < mutation_rate:
            exam[1] = random.choice(days)

            available_time_slots = [
                time_slot for time_slot in day_time_slots[exam[1]]
                if (exam[1], time_slot) not in used_rooms_by_timeslot
            ]

            if available_time_slots:
                exam[2] = random.choice(available_time_slots)

            available_rooms = [
                room.room_id for room in rooms 
                if exam[2] not in used_rooms_by_timeslot[(exam[1], exam[2])]
            ]

            if available_rooms:
                exam[3] = available_rooms[0] 
                used_rooms_by_timeslot[(exam[1], exam[2])].add(exam[3])

            booked_proctors = used_proctors_by_timeslot[(exam[1], exam[2])]
            available_proctors = [
                proctor.user_id for proctor in proctors 
                if proctor.user_id not in booked_proctors
            ]

            if available_proctors:
                exam[4] = random.choice(available_proctors)

            course = courses_by_yearsem_program[exam[0]]
            program_id = course.courseProgram.program.program_id
            yearSem_id = course.yearSem.yearSem_id

            conflicting = False
            for other_exam in schedule:
                other_course = courses_by_yearsem_program[other_exam[0]]
                if other_course.courseProgram.program.program_id == program_id and other_course.yearSem.yearSem_id == yearSem_id:
                    if other_exam[1] == exam[1] and other_exam[2] == exam[2]:
                        conflicting = True
                        break

            if conflicting:
                continue

    used_rooms_by_timeslot.clear()
    for exam in schedule:
        used_rooms_by_timeslot[(exam[1], exam[2])].add(exam[3])

def genetic_algorithm(courses, days, rooms, proctors, time_slots, generations=100, population_size=50, mutation_rate=0.1, courses_by_yearsem_program=None, exam_duration=None):
    """
    Genetic Algorithm for exam scheduling.
    """
    if courses_by_yearsem_program is None:
        courses_by_yearsem_program = {course.course_id: course for course in courses}

    population = initialize_population(population_size, courses, days, rooms, proctors, time_slots, exam_duration)

    for _ in range(generations):
        fitness_scores = [fitness_function(schedule, courses_by_yearsem_program, exam_duration) for schedule in population]

        population = selection(population, fitness_scores)

        next_generation = []
        while len(next_generation) < population_size:
            parent1, parent2 = random.sample(population, 2)
            child1, child2 = crossover(parent1, parent2)

            mutate(child1, mutation_rate, days, rooms, proctors, time_slots, courses_by_yearsem_program, exam_duration)
            mutate(child2, mutation_rate, days, rooms, proctors, time_slots, courses_by_yearsem_program, exam_duration)

            next_generation.extend([child1, child2])

        population = next_generation

    best_schedule = max(population, key=lambda schedule: fitness_function(schedule, courses_by_yearsem_program, exam_duration))
    return best_schedule


@login_required
@role_required('scheduler')
def generate_schedule(request):
    if request.method == 'POST':
        form = ExamScheduleForm(request.POST)
        if form.is_valid():
            courses = list(form.cleaned_data['courses'])
            rooms = list(form.cleaned_data['rooms'])
            exam_days = [datetime.strptime(day, "%Y-%m-%d").date() for day in form.cleaned_data['exam_days']]
            exam_duration = form.cleaned_data['exam_duration']
            proctors = User.objects.filter(user_roles__role__role_name="Faculty")
            start_time = datetime.strptime("07:00", "%H:%M")
            end_time = datetime.strptime("21:00", "%H:%M")
            time_slots = generate_time_slots(start_time, end_time, exam_duration)

            if len(exam_days) > len(time_slots):
                messages.error(request, "The number of selected exam days exceeds the available time slots.")
                return redirect('exam_schedules')

            courses_by_yearsem_program = {course.course_id: course for course in courses}

            best_schedule = genetic_algorithm(
                courses,
                exam_days,
                rooms,
                proctors,
                time_slots,
                generations=100,
                population_size=50,
                mutation_rate=0.1,
                courses_by_yearsem_program=courses_by_yearsem_program,
                exam_duration=exam_duration
            )

            exam_schedules = []
            skipped_schedules = []
            section_end_times = {}
            yearsem_assignments = defaultdict(set)
            used_rooms_by_timeslot = defaultdict(lambda: defaultdict(int))
            proctor_assignments = defaultdict(lambda: defaultdict(set))

            room_availability = {room.room_id: {day: set() for day in exam_days} for room in rooms}

            availability_mapping = {
                "Monday": {range(7, 12): 1, range(12, 18): 2, range(18, 21): 3},
                "Tuesday": {range(7, 12): 4, range(12, 18): 5, range(18, 21): 6},
                "Wednesday": {range(7, 12): 7, range(12, 18): 8, range(18, 21): 9},
                "Thursday": {range(7, 12): 10, range(12, 18): 11, range(18, 21): 12},
                "Friday": {range(7, 12): 13, range(12, 18): 14, range(18, 21): 15},
                "Saturday": {range(7, 12): 16, range(12, 18): 17, range(18, 21): 18},
            }

            # Collect all proctors for the email
            all_proctors_emails = set()

            for exam in best_schedule:
                course_id, exam_day, start_time, room_id, proctor_id = exam
                course = CourseYearSem.objects.get(course_id=course_id)
                room = Room.objects.get(room_id=room_id)
                proctor = User.objects.get(user_id=proctor_id)

                if ExamSchedule.objects.filter(day=exam_day, start_time=start_time, room=room).exists():
                    messages.error(request, f"Room {room.room_id} is already booked on {exam_day} at {start_time}.")
                    skipped_schedules.append(exam)
                    continue

                if proctor in proctor_assignments[exam_day][start_time]:
                    messages.error(request, f"Proctor {proctor.username} is already assigned to another exam at {start_time} on {exam_day}.")
                    skipped_schedules.append(exam)
                    continue

                proctor_assignments[exam_day][start_time].add(proctor)

                section_year_sems = SectionYearSem.objects.filter(
                    programSection__program=course.courseProgram.program,
                    yearSem=course.yearSem
                )

                assigned_room = None
                for section in section_year_sems:
                    for room in rooms:
                        room_capacity = room.capacity
                        room_key = (room.room_id, exam_day, start_time)
                        current_usage = used_rooms_by_timeslot[exam_day][room_key]

                        if current_usage < room_capacity and room not in room_availability[room.room_id][exam_day]:
                            assigned_room = room
                            used_rooms_by_timeslot[exam_day][room_key] += 1
                            break

                    if not assigned_room:
                        messages.error(request, f"No available rooms for section {section.section.section_name} of course {course.course.course_code} on {exam_day} at {start_time}")
                        skipped_schedules.append(exam)
                        continue

                    room_availability[assigned_room.room_id][exam_day].add(start_time)

                    day_name = exam_day.strftime("%A")
                    hour = start_time.hour
                    availability_id = None
                    if day_name in availability_mapping:
                        for time_range, avail_id in availability_mapping[day_name].items():
                            if hour in time_range:
                                availability_id = avail_id
                                break

                    if availability_id:
                        available_proctors = User.objects.filter(
                            user_roles__role__role_name='Faculty',
                            useravailability__availability__availability_id=availability_id
                        ).distinct()
                    else:
                        messages.error(request, f"Invalid time slot for {day_name} at {start_time}.")
                        skipped_schedules.append(exam)
                        continue

                    available_proctors = [proctor for proctor in available_proctors if proctor not in proctor_assignments[exam_day][start_time]]

                    if available_proctors:
                        proctor = random.choice(available_proctors)
                    else:
                        messages.error(request, f"No available proctors for this time slot at {start_time} on {exam_day}.")
                        skipped_schedules.append(exam)
                        continue

                    if course.course_id in section_end_times:
                        last_end_time = section_end_times[course.course_id]
                        next_start_time = last_end_time + timedelta(minutes=exam_duration)

                        if next_start_time > (datetime.combine(exam_day, start_time) + timedelta(minutes=exam_duration)):
                            start_time = next_start_time.time()

                    end_time = (datetime.combine(exam_day, start_time) + timedelta(minutes=exam_duration)).time()
                    section_end_times[course.course_id] = datetime.combine(exam_day, start_time)
                    yearsem_assignments[course.yearSem_id].add(start_time)

                    exam_schedule = ExamSchedule(
                        examSemester=form.cleaned_data['exam_semester'],
                        examTerm=form.cleaned_data['exam_term'],
                        day=exam_day,
                        start_time=start_time,
                        end_time=end_time,
                        exam_duration=exam_duration,
                        proctor=proctor,
                        sectionYearSem=section,
                        courseYearSem=course,
                        courseProgram=course.courseProgram,
                        room=assigned_room,
                        status="Scheduled"
                    )
                    exam_schedules.append(exam_schedule)

                    # Collect proctor's email
                    if proctor.email_address:
                        all_proctors_emails.add(proctor.email_address)

            # Send bulk email to all proctors after the schedules are generated
            if all_proctors_emails:
                subject = "Exam Schedule Generated"
                message = "A schedule has been generated. Please check ExamSync to see your schedules."
                from_email = settings.DEFAULT_FROM_EMAIL
                send_mail(
                    subject,
                    message,
                    from_email,
                    list(all_proctors_emails),
                    fail_silently=False
                )

            for exam in skipped_schedules:
                course_id, exam_day, start_time, room_id, proctor_id = exam
                course = CourseYearSem.objects.get(course_id=course_id)
                room = Room.objects.get(room_id=room_id)
                proctor = User.objects.get(user_id=proctor_id)

                valid_sections = SectionYearSem.objects.filter(
                    programSection__program=course.courseProgram.program,
                    yearSem=course.yearSem
                )

                if not valid_sections.exists():
                    messages.error(
                        request, 
                        f"No valid sections found for course {course.course.course_code} in program {course.courseProgram.program.program_name}."
                    )
                    continue

                available_rooms = [
                    room for room in rooms 
                    if (room.room_id, exam_day, start_time) not in room_availability[room.room_id]
                ]

                if available_rooms:
                    assigned_room = random.choice(available_rooms)
                else:
                    assigned_room = room


                assigned_section = valid_sections.first()

                exam_schedule = ExamSchedule(
                    examSemester=form.cleaned_data['exam_semester'],
                    examTerm=form.cleaned_data['exam_term'],
                    day=exam_day,
                    start_time=start_time,
                    end_time=(datetime.combine(exam_day, start_time) + timedelta(minutes=exam_duration)).time(),
                    exam_duration=exam_duration,
                    proctor=proctor,
                    sectionYearSem=assigned_section,
                    courseYearSem=course,
                    courseProgram=course.courseProgram,
                    room=assigned_room,
                    status="Scheduled"
                )
                exam_schedules.append(exam_schedule)

            ExamSchedule.objects.bulk_create(exam_schedules)
            messages.success(request, "Schedules successfully generated!")
            return redirect('exam_schedules')
    else:
        form = ExamScheduleForm()

    return render(request, 'exam-schedule-management/generate_schedule.html', {'form': form})

# EXAM REMARKS

@login_required
@role_required('faculty')
def add_remark(request, examSchedule_id):
    schedule = get_object_or_404(ExamSchedule, pk=examSchedule_id, proctor=request.user)

    if request.method == 'POST':
        remark = request.POST.get('remarksDescription')
        if remark:
            exam_remark = ExamRemarks(
                remarksDescription=remark,
                examSchedule=schedule,
                status='Pending',
            )
            exam_remark.save()
            return redirect('dashboard_faculty', role='faculty')

    return render(request, 'exam-remarks/add_remark.html', {'schedule': schedule})


@login_required
@role_required('dean')
def update_remark_status(request, examRemarks_id):
    exam_remark = get_object_or_404(ExamRemarks, pk=examRemarks_id)

    if exam_remark.status != 'Pending':
        messages.error(request, "This remark has already been approved or declined.")
        return redirect('dashboard_dean')
    
    if request.method == 'POST':
        status = request.POST.get('status')

        if status not in ['Approved', 'Declined']:
            messages.error(request, "Invalid status.")
            return redirect('dashboard_dean')

        exam_remark.status = status
        exam_remark.save()

        messages.success(request, f'Remark status updated to {status}.')
        
        exam_schedule = ExamSchedule.objects.get(examSchedule_id=exam_remark.examSchedule_id)
        
        original_proctor = User.objects.get(user_id=exam_schedule.proctor_id)
        
        if status == "Approved":
            availability_mapping = {
                "Monday": {range(7, 12): 1, range(12, 18): 2, range(18, 21): 3},
                "Tuesday": {range(7, 12): 4, range(12, 18): 5, range(18, 21): 6},
                "Wednesday": {range(7, 12): 7, range(12, 18): 8, range(18, 21): 9},
                "Thursday": {range(7, 12): 10, range(12, 18): 11, range(18, 21): 12},
                "Friday": {range(7, 12): 13, range(12, 18): 14, range(18, 21): 15},
                "Saturday": {range(7, 12): 16, range(12, 18): 17, range(18, 21): 18},
            }

            exam_day_name = exam_schedule.day.strftime("%A")
            exam_hour = exam_schedule.start_time.hour

            availability_id = None
            for time_range, avail_id in availability_mapping.get(exam_day_name, {}).items():
                if exam_hour in time_range:
                    availability_id = avail_id
                    break

            if availability_id:
                available_proctors = User.objects.filter(
                    user_roles__role__role_name='Faculty',
                    useravailability__availability__availability_id=availability_id
                ).distinct()

                available_proctors = available_proctors.exclude(user_id=exam_schedule.proctor_id)

                available_proctors = [
                    proctor for proctor in available_proctors
                    if not ExamSchedule.objects.filter(proctor=proctor, day=exam_schedule.day, start_time=exam_schedule.start_time).exists()
                ]

                if available_proctors:
                    new_proctor = available_proctors[0]

                    exam_schedule.proctor = new_proctor
                    exam_schedule.save()

                    # Notify the new proctor
                    if new_proctor.email_address:
                        subject = f"You have been re-assigned to an exam as a Proctor"
                        message = f"Dear {new_proctor.first_name},\n\nYou have been assigned as the proctor for the exam scheduled on {exam_schedule.day}, {exam_schedule.room}, {exam_schedule.start_time}.\n\nThank you."
                        from_email = settings.DEFAULT_FROM_EMAIL
                        
                        send_mail(
                            subject,
                            message,
                            from_email,
                            [new_proctor.email_address],
                            fail_silently=False,
                        )

                    schedulers = User.objects.filter(user_roles__role__role_name='Scheduler')
                    scheduler_emails = [scheduler.email_address for scheduler in schedulers if scheduler.email_address]

                    if scheduler_emails:
                        subject = "Proctor Replacement Notification"
                        message = f"A proctor has been replaced:\n\nOld proctor: {original_proctor.first_name} {original_proctor.last_name}\nNew proctor: {new_proctor.first_name} {new_proctor.last_name}\nExam Date: {exam_schedule.day}, Room: {exam_schedule.room}, Time: {exam_schedule.start_time}.\n\nThank you."
                        send_mail(
                            subject,
                            message,
                            from_email,
                            scheduler_emails,
                            fail_silently=False,
                        )
                else:
                    messages.error(request, "No available proctors found for this exam.")
                    return redirect('dashboard_dean')

        if original_proctor.email_address:
            subject = f"Your exam remark has been {status}"
            message = f"Dear {original_proctor.first_name},\n\nThe remark for the exam scheduled on {exam_schedule.day} has been {status}.\n\nThank you."
            from_email = settings.DEFAULT_FROM_EMAIL

            send_mail(
                subject,
                message,
                from_email,
                [original_proctor.email_address],
                fail_silently=False,
            )

        return redirect('dashboard_dean')
    return redirect('dashboard_dean')
