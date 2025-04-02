from django.urls import path
from . import views

urlpatterns = [
    path('users/', views.manage_users, name='manage_users'),
    path('create-user/', views.create_user, name='create_user'),
    path('edit-user/<int:user_id>/', views.edit_user, name='edit_user'),
    path('delete-user/<int:user_id>/', views.delete_user, name='delete_user'),

    path('', views.login_view, {'role': 'administrator'}, name='login_page'),
    path('login/<str:role>/', views.login_view, name='login_with_role'),

    path('logout/', views.logout_view, name='logout'),

    path('dashboard-administrator/', views.dashboard_view, {'role': 'administrator'}, name='dashboard_administrator'),
    path('dashboard-scheduler/', views.dashboard_view, {'role': 'scheduler'}, name='dashboard_scheduler'),
    path('dashboard-dean/', views.dashboard_view, {'role': 'dean'}, name='dashboard_dean'),
    path('dashboard-faculty/', views.dashboard_view, {'role': 'faculty'}, name='dashboard_faculty'),

    path('manage-courses/', views.manage_courses, name='manage_courses'),
    path('courses/', views.course_list, name='course_list'),
    path('create-course/', views.create_course, name='create_course'),
    path('edit-course/<int:course_id>/', views.edit_course, name='edit_course'),
    path('delete-course/<int:course_id>/', views.delete_course, name='delete_course'),
    
    path('buildings/', views.building_list, name='building_list'),
    path('edit-building/<int:building_id>/', views.edit_building, name='edit_building'),
    path('delete-building/<int:building_id>/', views.delete_building, name='delete_building'),

    path('rooms/', views.room_list, name='room_list'),
    path('edit-room/<int:room_id>/', views.edit_room, name='edit_room'),
    path('delete-room/<int:room_id>/', views.delete_room, name='delete_room'),

    path('programs/', views.program_list, name='program_list'),
    path('edit-program/<int:program_id>/', views.edit_program, name='edit_program'),
    path('delete-program/<int:program_id>/', views.delete_program, name='delete_program'),

    path('colleges/', views.college_list, name='college_list'),
    path('edit-college/<int:college_id>/', views.edit_college, name='edit_college'),
    path('delete-college/<int:college_id>/', views.delete_college, name='delete_college'),

    path('manage-sections/', views.manage_sections, name='manage_sections'),
    path('sections/', views.section_list, name='section_list'),
    path('create-section/', views.create_section, name='create_section'),
    path('edit-section/<int:section_id>/', views.edit_section, name='edit_section'),
    path('add_role_to_user/<int:user_id>/', views.add_role_to_user, name='add_role_to_user'),
    path('delete-section/<int:section_id>/', views.delete_section, name='delete_section'),

    path('manage-availability/', views.manage_availability, name='manage_availability'),

    path('assign-course-modality/', views.assign_course_modality, name='assign_course_modality'),
    path('edit-course-modality/', views.edit_course_modality, name='edit-course-modality'),

    path('generate-schedule/', views.generate_schedule, name='generate_schedule'),
    path('fetch-courses/', views.fetch_courses, name='fetch_courses'),
    path('exam-schedules/', views.exam_schedules, name='exam_schedules'),
    path('exam-schedules-update/', views.exam_schedule_list, name='exam_schedule_list'),
    path('exam-schedule/<int:exam_schedule_id>/', views.update_exam_schedule, name='update_exam_schedule'),
    path('delete-schedule/<str:day>/', views.delete_schedule_for_day, name='delete_schedule_for_day'),
    path('update-schedule-status/', views.update_schedule_status, name='update_schedule_status'),


    path('dean/view-schedules/', views.exam_schedules_dean, name='view_schedules_dean'),
    path('scheduler/view-schedules/', views.exam_schedules_scheduler, name='view_schedules_scheduler'),
    path('faculty/view-schedules/', views.exam_schedules_faculty, name='view_schedules_faculty'),
    path('outside/view-schedules/', views.exam_schedules_outside, name='view_schedules_outside'),

    path('faculty/schedule/<int:examSchedule_id>/add-remark/', views.add_remark, name='add_remark'),
    path('dean/remarks/<int:examRemarks_id>/update-status/', views.update_remark_status, name='update_remark_status'),
    path('dashboard-<str:role>/', views.dashboard_view, name='dashboard_view'),
]

handler404 = 'UserManagement.views.custom_404_view'