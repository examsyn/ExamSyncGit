from django import forms
from .models import User, Role, UserRole, Course, Building, College, Program, Room, Section, SectionYearSem, YearSem,CourseYearSem, CourseProgram, Program, Availability, CourseModality, ExamSchedule, ProgramSection, ExamRemarks
from django.utils import timezone
from django.db.models import Q
import random

from django.contrib.auth.forms import ReadOnlyPasswordHashField

# USER
class UserForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(), required=False)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'middle_name', 'last_name', 'email_address', 'contact_number', 'work_time' ,'status', 'password']
        widgets = {
            'password': forms.PasswordInput(attrs={'placeholder': 'Enter current password to keep the same!'}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get('password')

        if password:
            user.set_password(password)

        if commit:
            user.save()
        return user
    
# USERUPDATE
class UserUpdateForm(forms.ModelForm):
    password = ReadOnlyPasswordHashField(label="Password", help_text="Passwords can't be changed here.")
    
    class Meta:
        model = User
        fields = ['username', 'first_name', 'middle_name', 'last_name', 'email_address', 'contact_number', 'work_time', 'status']

    def clean_password(self):
        return self.initial["password"]

# ROLE
class RoleForm(forms.ModelForm):
    class Meta:
        model = Role
        fields = ['role_name']

# USERROLE
class UserRoleForm(forms.ModelForm):
    class Meta:
        model = UserRole
        fields = ['user', 'role']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['user'].queryset = User.objects.all()
        self.fields['role'].queryset = Role.objects.all()
        self.fields['role'].required = True

    def clean(self):
        cleaned_data = super().clean()
        user = cleaned_data.get("user")
        role = cleaned_data.get("role")

        if user and role and UserRole.objects.filter(user=user, role=role).exists():
            raise forms.ValidationError(f"The user already has the '{role}' role assigned.")
        
        return cleaned_data
    
# COURSE
class CourseForm(forms.ModelForm):
    program = forms.ModelChoiceField(queryset=Program.objects.all(), label="Program")
    semester = forms.ModelChoiceField(queryset=YearSem.objects.all(), label="Year/Semester")

    class Meta:
        model = Course
        fields = ['course_code', 'course_name', 'program', 'semester']

# BUILDING
class BuildingForm(forms.ModelForm):
    class Meta:
        model = Building
        fields = ['building_code','building_name']

# ROOM
class RoomForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = ['room_name', 'building', 'roomType', 'capacity', 'modality']
        widgets = {
            'building': forms.Select(attrs={'class': 'form-control'}),
        }

# PROGRAM
class ProgramForm(forms.ModelForm):
    class Meta:
        model = Program
        fields = ['program_name', 'college']
        widgets = {
            'college': forms.Select(attrs={'class': 'form-control'}),
        }

# COLLEGE
class CollegeForm(forms.ModelForm):
    class Meta:
        model = College
        fields = ['college_name']

# SECTION
class SectionForm(forms.ModelForm):
    # Program field to display the Program related to the Section
    program = forms.ModelChoiceField(queryset=Program.objects.all(), label="Program")

    # Year/Semester field to select multiple YearSem objects
    year_semesters = forms.ModelMultipleChoiceField(queryset=YearSem.objects.all(), widget=forms.CheckboxSelectMultiple, label="Year/Semesters")

    class Meta:
        model = Section
        fields = ['section_name', 'program', 'year_semesters']  # Include 'program' and 'year_semesters'




# USERAVAILABILITY
class UserAvailabilityForm(forms.Form):
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        super().__init__(*args, **kwargs)
        availabilities = Availability.objects.all()
        for availability in availabilities:
            user_availability = user.useravailability_set.filter(availability=availability).exists()
            self.fields[f'availability_{availability.id}'] = forms.BooleanField(
                required=False,
                initial=user_availability,
                label=f"{availability.availabilityDay} - {availability.availabilityDescription} ({availability.availabilityTime})"
            )

# COURSEMODALITY
class CourseModalityForm(forms.ModelForm):
    class Meta:
        model = CourseModality
        fields = ['modality', 'course', 'user']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        bayanihan_leader_role = Role.objects.get(role_name="Bayanihan Leader")
        user_roles = UserRole.objects.filter(role=bayanihan_leader_role)
        user_ids = user_roles.values_list('user', flat=True)
        
        self.fields['user'].queryset = User.objects.filter(user_id__in=user_ids)

# EDITCOURSEMODALITY
class EditCourseModalityForm(forms.ModelForm):
    class Meta:
        model = CourseModality
        fields = ['modality']

    modality = forms.ChoiceField(choices=CourseModality.MODALITY_CHOICES, required=True)

# EXAMSCHEDULE
from datetime import datetime, time, timedelta
from django.utils import timezone
import random

# forms.py
from .models import CourseYearSem, Room, Role, UserRole, ExamSchedule, User

class ExamScheduleForm(forms.Form):
    EXAM_SEMESTER_CHOICES = [
        ('First Semester', 'First Semester'),
        ('Second Semester', 'Second Semester'),
    ]
    EXAM_TERM_CHOICES = [
        ('Midterm Exam', 'Midterm Exam'),
        ('Final Exam', 'Final Exam'),
    ]
    exam_semester = forms.ChoiceField(choices=EXAM_SEMESTER_CHOICES, label="Exam Semester")
    exam_term = forms.ChoiceField(choices=EXAM_TERM_CHOICES, label="Exam Term")
    exam_duration = forms.IntegerField(min_value=1, required=False, label="Exam Duration (minutes)")
    courses = forms.ModelMultipleChoiceField(
        queryset=CourseYearSem.objects.all(),
        widget=forms.CheckboxSelectMultiple(),
        label="Select Courses"
    )
    rooms = forms.ModelMultipleChoiceField(
        queryset=Room.objects.all(),
        widget=forms.CheckboxSelectMultiple(),
        label="Select Rooms"
    )
    start_time = forms.TimeField(widget=forms.TimeInput(attrs={'type': 'time'}), required=False, label="Start Time")
    end_time = forms.TimeField(widget=forms.TimeInput(attrs={'type': 'time'}), required=False, label="End Time")
    exam_days = forms.MultipleChoiceField(
        choices=[],
        widget=forms.CheckboxSelectMultiple,
        label="Available Exam Days"
    )
    
    proctor = forms.CharField(widget=forms.HiddenInput(), required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        faculty_role = Role.objects.get(role_name="Faculty")
        faculty_users = UserRole.objects.filter(role=faculty_role).values_list('user', flat=True)
        self.faculty_users = User.objects.filter(user_id__in=faculty_users)

        if self.faculty_users:
            random_proctor = random.choice(self.faculty_users)
            self.fields['proctor'].initial = random_proctor.user_id

        self.fields['exam_days'].choices = [
            (day.strftime("%Y-%m-%d"), day.strftime("%Y-%m-%d")) for day in [
                timezone.now().date() + timedelta(days=i) for i in range(1, 2000)
            ]
        ]

    def clean_courses(self):
        courses = self.cleaned_data.get('courses')
        if not courses.exists():
            raise forms.ValidationError("At least one course must be selected.")
        return courses

    def clean(self):
        cleaned_data = super().clean()
        exam_duration = cleaned_data.get('exam_duration')
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        exam_days = cleaned_data.get('exam_days')

        if not exam_days:
            raise forms.ValidationError("At least one available exam day must be selected.")

        available_days = []
        for day in exam_days:
            try:
                available_days.append(datetime.strptime(day, "%Y-%m-%d").date())
            except ValueError:
                raise forms.ValidationError(f"Invalid date format for exam day: {day}")

        cleaned_data['exam_day'] = random.choice(available_days)

        if not start_time and not end_time:
            if not exam_duration:
                raise forms.ValidationError("Either start_time and end_time must be provided or exam_duration must be specified.")
            else:
                self._assign_auto_time_slot(cleaned_data)
        elif start_time and end_time:
            if end_time <= start_time:
                raise forms.ValidationError("End time must be after the start time.")

        return cleaned_data


    def _assign_auto_time_slot(self, cleaned_data):
        courses = cleaned_data.get('courses')
        if not courses:
            raise forms.ValidationError("No courses were selected. Please select at least one course.")

        exam_day = cleaned_data.get('exam_day')
        exam_duration = cleaned_data.get('exam_duration')
        rooms = cleaned_data.get('rooms')

        day_start = timezone.datetime.combine(exam_day, time(7, 0))
        day_end = timezone.datetime.combine(exam_day, time(21, 0))

        total_available_time = (day_end - day_start).total_seconds() / 60
        if exam_duration > total_available_time:
            raise forms.ValidationError("The exam duration is too long to fit within the available time window.")

        possible_start_times = []
        current_start_time = day_start
        while current_start_time + timedelta(minutes=exam_duration) <= day_end:
            possible_start_times.append(current_start_time)
            current_start_time += timedelta(minutes=exam_duration)

        available_slots = []
        attempt_count = 0
        max_attempts = 50
        while available_slots == [] and attempt_count < max_attempts:
            attempt_count += 1
            for start in possible_start_times:
                end = start + timedelta(minutes=exam_duration)
                conflict_found = False

                for course in courses:
                    course_program = course.courseProgram
                    course_year_sem = course.yearSem

                    if ExamSchedule.objects.filter(
                        day=exam_day,
                        start_time__lt=end.time(),
                        end_time__gt=start.time(),
                        courseProgram=course_program,
                        courseYearSem__yearSem=course_year_sem,
                        status="Scheduled"
                    ).exists():
                        conflict_found = True
                        break

                if not conflict_found:
                    available_slots.append((start, end))

            if available_slots == []:
                available_slots = []
                for start in possible_start_times:
                    end = start + timedelta(minutes=exam_duration)
                    available_slots.append((start, end))

        if available_slots:
            chosen_slot = random.choice(available_slots)
            cleaned_data['start_time'] = chosen_slot[0].time()
            cleaned_data['end_time'] = chosen_slot[1].time()
        else:
            raise forms.ValidationError("No available time slot found after multiple attempts.")


        
    def clean_exam_duration(self):
        exam_duration = self.cleaned_data['exam_duration']
        if exam_duration % 30 != 0:
            raise forms.ValidationError("Exam duration must be a multiple of 30 minutes.")
        return exam_duration

    def save(self, commit=True):
        proctor_id = self.cleaned_data.get('proctor')
        proctor = User.objects.get(id=proctor_id)

        exam_schedule = ExamSchedule(
            examSemester=self.cleaned_data['exam_semester'],
            examTerm=self.cleaned_data['exam_term'],
            day=self.cleaned_data['exam_day'],
            start_time=self.cleaned_data['start_time'],
            end_time=self.cleaned_data['end_time'],
            exam_duration=self.cleaned_data.get('exam_duration'),
            proctor=proctor,
            courseYearSem=self.cleaned_data['courses'],
        )

        if commit:
            exam_schedule.save()

        rooms = self.cleaned_data['rooms']
        exam_schedule.room.set(rooms)

        return exam_schedule


from django import forms
from .models import Room, ExamSchedule, CourseYearSem
from django.utils import timezone
import random

class ExamScheduleUpdateForm(forms.ModelForm):
    room = forms.ModelChoiceField(
        queryset=Room.objects.all(),
        widget=forms.Select(),
        label="Select Room"
    )
    start_time = forms.TimeField(widget=forms.TimeInput(attrs={'type': 'time'}), required=True, label="Start Time")
    end_time = forms.TimeField(widget=forms.TimeInput(attrs={'type': 'time'}), required=True, label="End Time")
    exam_day = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=True, label="Exam Day")

    class Meta:
        model = ExamSchedule
        fields = ['room', 'start_time', 'end_time', 'exam_day'] 

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        exam_day = cleaned_data.get('exam_day')

        if end_time <= start_time:
            raise forms.ValidationError("End time must be after start time.")

        room = cleaned_data.get('room')

        current_exam_schedule_id = self.instance.examSchedule_id

        if ExamSchedule.objects.filter(
            day=exam_day,
            start_time__lt=end_time,
            end_time__gt=start_time,
            room=room,
            status="Scheduled",
            courseProgram=self.instance.courseProgram,
            courseYearSem=self.instance.courseYearSem,
        ).exclude(examSchedule_id=current_exam_schedule_id).exists():
            raise forms.ValidationError("Another exam with the same courseProgram and courseYearSem is already scheduled in this time slot.")

        return cleaned_data

    def save(self, commit=True):
        exam_schedule = super().save(commit=False)

        selected_room = self.cleaned_data['room']
        exam_schedule.room = selected_room

        if commit:
            exam_schedule.save()

        return exam_schedule


# EXAMREMARKS
from django import forms
from .models import ExamRemarks

class ExamRemarksForm(forms.ModelForm):
    class Meta:
        model = ExamRemarks
        fields = ['remarksDescription', 'examSchedule', 'status']
        widgets = {
            'examSchedule': forms.HiddenInput(),
            'status': forms.Select(choices=[('Pending', 'Pending'), ('Approved', 'Approved'), ('Declined', 'Declined')])
        }
