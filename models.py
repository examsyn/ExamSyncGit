from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin, Group, Permission
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save
from django.dispatch import receiver

# USER MANAGEMENT
class UserManager(BaseUserManager):
    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError('The Username field must be set')
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        return self.create_user(username, password, **extra_fields)

# USER
class User(AbstractBaseUser, PermissionsMixin):
    STATUS_CHOICES = (
        ('Active', 'Active'),
        ('Inactive', 'Inactive'),
    )

    user_id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=55, unique=True)
    password = models.CharField(max_length=255)
    first_name = models.CharField(max_length=55)
    middle_name = models.CharField(max_length=55, null=True, blank=True)
    last_name = models.CharField(max_length=55)
    email_address = models.EmailField(max_length=255, blank=True)
    contact_number = models.CharField(max_length=55, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'username'

    objects = UserManager()

    groups = models.ManyToManyField(
        Group,
        related_name='custom_user_set',
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups'
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name='custom_user_set',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions'
    )

    class Meta:
        db_table = 'tbl_users'

    def __str__(self):
        return f"{self.last_name}, {self.first_name}"

# ROLE
class Role(models.Model):
    role_id = models.AutoField(primary_key=True)
    role_name = models.CharField(max_length=55, unique=True)

    class Meta:
        db_table = 'tbl_roles'

    def __str__(self):
        return self.role_name

# USERROLE
class UserRole(models.Model):
    userRole_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_roles')
    role = models.ForeignKey(Role, on_delete=models.CASCADE)

    class Meta:
        db_table = 'tbl_userRole'

    def __str__(self):
        return f"{self.user.user_id} - {self.role.role_name}"

# BUILDING
class Building(models.Model):
    building_id = models.AutoField(primary_key=True)
    building_code = models.CharField(max_length=55)
    building_name = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.building_code}: {self.building_name}"

    class Meta:
        db_table = 'tbl_buildings'

# ROOM
class Room(models.Model):
    TYPE_CHOICES = (
        ('Single', 'Single'),
        ('Multiple', 'Multiple'),
    )

    MODALITY_CHOICES = [
        ('Written', 'Written'),
        ('Laboratory', 'Laboratory'),
        ('Online', 'Online'),
        ('None', 'None'),
    ]
    modality = models.CharField(max_length=55, choices=MODALITY_CHOICES)
    room_id = models.AutoField(primary_key=True)
    room_name = models.CharField(max_length=255)
    capacity = models.IntegerField()
    building = models.ForeignKey(Building, on_delete=models.CASCADE)
    roomType = models.CharField(max_length=10, choices=TYPE_CHOICES, default='Single')


    def __str__(self):
        return self.room_name

    class Meta:
        db_table = 'tbl_rooms'

# COLLEGE
class College(models.Model):
    college_id = models.AutoField(primary_key=True)
    college_name = models.CharField(max_length=255)

    def __str__(self):
        return self.college_name
    
    class Meta:
        db_table = 'tbl_colleges'

# PROGRAM
class Program(models.Model):
    program_id = models.AutoField(primary_key=True)
    program_name = models.CharField(max_length=255)
    college = models.ForeignKey(College, on_delete=models.CASCADE)

    def __str__(self):
        return self.program_name

    @property
    def get_college_id(self):
        return self.college.college_id

    class Meta:
        db_table = 'tbl_programs'

# YEARSEM
class YearSem(models.Model):
    yearSem_id = models.AutoField(primary_key=True)
    yearLevel = models.CharField(max_length=55)
    semester = models.CharField(max_length=55)

    def __str__(self):
        return f"{self.yearLevel}, {self.semester}"
    
    class Meta:
        db_table = 'tbl_yearSem'

# COURSE
class Course(models.Model):
    course_id = models.AutoField(primary_key=True)
    course_code = models.CharField(max_length=55)
    course_name = models.CharField(max_length=255)
    
    def __str__(self):
        return f"{self.course_code} - {self.course_name} "

    class Meta:
        db_table = 'tbl_courses'

# COURSE PROGRAM
class CourseProgram(models.Model):
    courseProgram_id = models.AutoField(primary_key=True)
    course = models.ForeignKey('Course', on_delete=models.CASCADE)
    program = models.ForeignKey('Program', on_delete=models.CASCADE)

    class Meta:
        db_table = 'tbl_courseProgram'

# SECTION
class Section(models.Model):
    section_id = models.AutoField(primary_key=True)
    section_name = models.CharField(max_length=255)

    def __str__(self):
        return self.section_name

    class Meta:
        db_table = 'tbl_sections'

# PROGRAMSECTION
class ProgramSection(models.Model):
    programSection_id = models.AutoField(primary_key=True)
    section = models.ForeignKey('Section', on_delete=models.CASCADE)  # Links to Section
    program = models.ForeignKey('Program', on_delete=models.CASCADE)  # Links to Program

    def __str__(self):
        return f"{self.program} - {self.section}"


    class Meta:
        db_table = 'tbl_programSection'

# SECTIONYEARSEM
class SectionYearSem(models.Model):
    sectionYearSem_id = models.AutoField(primary_key=True)
    section = models.ForeignKey('Section', on_delete=models.CASCADE)
    yearSem = models.ForeignKey('YearSem', on_delete=models.CASCADE)
    programSection = models.ForeignKey('ProgramSection', on_delete=models.CASCADE)
    
      # Updated reference

    class Meta:
        db_table = 'tbl_sectionYearSem'

# COURSEPROGRAM
class CourseProgram(models.Model):
    courseProgram_id = models.AutoField(primary_key=True)
    course = models.ForeignKey('Course', on_delete=models.CASCADE)
    program = models.ForeignKey('Program', on_delete=models.CASCADE)

    class Meta:
        db_table = 'tbl_courseProgram'

# COURSEYEARSEM
class CourseYearSem(models.Model):
    courseYearSem_id = models.AutoField(primary_key=True)
    course = models.ForeignKey('Course', on_delete=models.CASCADE)
    yearSem = models.ForeignKey('YearSem', on_delete=models.CASCADE)
    courseProgram = models.ForeignKey('CourseProgram', on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.course.course_code} - {self.course.course_name}"

    class Meta:
        db_table = 'tbl_courseYearSem'

# AVAILABILITY
class Availability(models.Model):
    availability_id = models.AutoField(primary_key=True)
    availabilityDay = models.CharField(max_length=9, choices=[('Monday', 'Monday'), ('Tuesday', 'Tuesday'), ('Wednesday', 'Wednesday'), ('Thursday', 'Thursday'), ('Friday', 'Friday'), ('Saturday', 'Saturday')])
    availabilityDescription = models.CharField(max_length=9, choices=[('Morning', 'Morning'), ('Afternoon', 'Afternoon'), ('Evening', 'Evening')])
    availabilityTime = models.CharField(max_length=15, choices=[('8:00 - 11:00', '8:00 - 11:00'), ('12:00 - 5:00', '12:00 - 5:00'), ('6:00 - 9:00', '6:00 - 9:00')])

    class Meta:
        db_table = 'tbl_availability'

# USERAVAILABILITY
class UserAvailability(models.Model):
    userAvailability_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    availability = models.ForeignKey(Availability, on_delete=models.CASCADE)

    class Meta:
        db_table = 'tbl_userAvailability'

# COURSEMODALITY
class CourseModality(models.Model):
    courseModality_id = models.AutoField(primary_key=True)
    MODALITY_CHOICES = [
        ('Written', 'Written'),
        ('Laboratory', 'Laboratory'),
        ('Online', 'Online'),
        ('None', 'None'),
    ]
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    modality = models.CharField(max_length=255, choices=MODALITY_CHOICES)

    def __str__(self):
        return f"{self.user} - {self.course} - {self.modality}"
    
    class Meta:
        db_table = 'tbl_courseModality'


# EXAM SCHEDULE
class ExamSchedule(models.Model):
    examSchedule_id = models.AutoField(primary_key=True)
    EXAM_SEMESTER_CHOICES = [
        ('First Semester', 'First Semester'),
        ('Second Semester', 'Second Semester'),
    ]

    EXAM_TERM_CHOICES = [
        ('Midterm Exam', 'Midterm Exam'),
        ('Final Exam', 'Final Exam'),
    ]
    
    STATUS_CHOICES = [
        ('Scheduled', 'Scheduled'),
        ('Approved', 'Approved'),
        ('Declined', 'Declined'),
    ]

    examSemester = models.CharField(max_length=55, choices=EXAM_SEMESTER_CHOICES)
    examTerm = models.CharField(max_length=55, choices=EXAM_TERM_CHOICES)
    day = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    exam_duration = models.IntegerField(null=True, blank=True)  # Duration in minutes
    proctor = models.ForeignKey(User, on_delete=models.CASCADE, related_name="proctored_exams")
    sectionYearSem = models.ForeignKey('SectionYearSem', on_delete=models.CASCADE)
    courseYearSem = models.ForeignKey('CourseYearSem', on_delete=models.CASCADE)
    courseProgram = models.ForeignKey('CourseProgram', on_delete=models.CASCADE)
    room = models.ForeignKey('Room', on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Scheduled')


    def clean(self):
        super().clean()
        overlapping_schedules = ExamSchedule.objects.filter(
            day=self.day,
            start_time__lt=self.end_time,
            end_time__gt=self.start_time,
            courseProgram=self.courseProgram,  # Same course program
            courseYearSem=self.courseYearSem,  # Same courseYearSem
            status="Scheduled"
        ).exclude(pk=self.pk)  # Exclude the current object if it's an update

        if overlapping_schedules.exists():
            raise ValidationError(
                "Another exam with the same courseProgram and courseYearSem is already scheduled in this time slot."
            )


    def save(self, *args, **kwargs):
        """Override save to dynamically update the status."""
        from datetime import datetime, time
        now = datetime.now()
        if self.day == now.date():
            if time(self.start_time.hour, self.start_time.minute) <= now.time() <= time(self.end_time.hour, self.end_time.minute):
                self.status = 'Ongoing'
            elif now.time() > time(self.end_time.hour, self.end_time.minute):
                self.status = 'Ended'
        super().save(*args, **kwargs)

    
    def __str__(self):
        return self.examSchedule_id
    
    class Meta:
        db_table = 'tbl_examSchedule'


# EXAM REMARKS

class ExamRemarks(models.Model):
    examRemarks_id = models.AutoField(primary_key=True)
    remarksDescription = models.TextField()
    examSchedule = models.ForeignKey(ExamSchedule, on_delete=models.CASCADE)
    status = models.CharField(
        max_length=20,  # Ensure this matches the length of the values you're using
        choices=[('Pending', 'Pending'), ('Approved', 'Approved'), ('Declined', 'Declined')],
        default='Pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'tbl_examRemarks'

