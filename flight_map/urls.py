from django.urls import path
from .views import (
    ProgramListCreateView,
    ProgramRetrieveUpdateDestroyView,
    WorkstreamListCreateView,
    WorkstreamRetrieveUpdateDestroyView,
    MilestoneListCreateView,
    MilestoneRetrieveUpdateDestroyView,
    TaskListCreateView,
    TaskRetrieveUpdateDestroyView,
)

urlpatterns = [
    # Program URLs
    path('programs/', ProgramListCreateView.as_view(), name='program-list-create'),
    path('programs/<int:pk>/', ProgramRetrieveUpdateDestroyView.as_view(), name='program-detail'),

    # Workstream URLs
    path('workstreams/', WorkstreamListCreateView.as_view(), name='workstream-list-create'),
    path('workstreams/<int:pk>/', WorkstreamRetrieveUpdateDestroyView.as_view(), name='workstream-detail'),

    # Milestone URLs
    path('milestones/', MilestoneListCreateView.as_view(), name='milestone-list-create'),
    path('milestones/<int:pk>/', MilestoneRetrieveUpdateDestroyView.as_view(), name='milestone-detail'),

    # Task URLs
    path('tasks/', TaskListCreateView.as_view(), name='task-list-create'),
    path('tasks/<int:pk>/', TaskRetrieveUpdateDestroyView.as_view(), name='task-detail'),
]
