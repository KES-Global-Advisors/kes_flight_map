from django.urls import path
from .views import (
    StrategyListCreateView, StrategyRetrieveUpdateDestroyView,
    StrategicGoalListCreateView, StrategicGoalRetrieveUpdateDestroyView,
    ProgramListCreateView, ProgramRetrieveUpdateDestroyView,
    WorkstreamListCreateView, WorkstreamRetrieveUpdateDestroyView,
    MilestoneListCreateView, MilestoneRetrieveUpdateDestroyView,
    ActivityListCreateView, ActivityRetrieveUpdateDestroyView
)

urlpatterns = [
    # Strategy endpoints
    path('strategies/', StrategyListCreateView.as_view(), name='strategy-list-create'),
    path('strategies/<int:pk>/', StrategyRetrieveUpdateDestroyView.as_view(), name='strategy-detail'),

    # Strategic Goals
    path('strategic-goals/', StrategicGoalListCreateView.as_view(), name='strategic-goal-list-create'),
    path('strategic-goals/<int:pk>/', StrategicGoalRetrieveUpdateDestroyView.as_view(), name='strategic-goal-detail'),

    # Program endpoints
    path('programs/', ProgramListCreateView.as_view(), name='program-list-create'),
    path('programs/<int:pk>/', ProgramRetrieveUpdateDestroyView.as_view(), name='program-detail'),

    # Workstream endpoints
    path('workstreams/', WorkstreamListCreateView.as_view(), name='workstream-list-create'),
    path('workstreams/<int:pk>/', WorkstreamRetrieveUpdateDestroyView.as_view(), name='workstream-detail'),

    # Milestone endpoints
    path('milestones/', MilestoneListCreateView.as_view(), name='milestone-list-create'),
    path('milestones/<int:pk>/', MilestoneRetrieveUpdateDestroyView.as_view(), name='milestone-detail'),

    # Activity endpoints
    path('activities/', ActivityListCreateView.as_view(), name='activity-list-create'),
    path('activities/<int:pk>/', ActivityRetrieveUpdateDestroyView.as_view(), name='activity-detail'),
]
