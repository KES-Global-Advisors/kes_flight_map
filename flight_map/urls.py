from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    RoadmapViewSet, MilestoneViewSet, ActivityViewSet,
    ProgressDashboardView, EmployeeContributionsView,
    StrategicAlignmentView,
    # Maintain compatibility for other endpoints
    StrategyListCreateView, StrategyRetrieveUpdateDestroyView,
    StrategicGoalListCreateView, StrategicGoalRetrieveUpdateDestroyView,
    ProgramListCreateView, ProgramRetrieveUpdateDestroyView,
    WorkstreamListCreateView, WorkstreamRetrieveUpdateDestroyView,
    DashboardMilestoneView,
)

router = DefaultRouter()
router.register(r'roadmaps', RoadmapViewSet, basename='roadmap')
router.register(r'milestones', MilestoneViewSet, basename='milestone')
router.register(r'activities', ActivityViewSet, basename='activity')

urlpatterns = [
    # New viewsets
    path('', include(router.urls)),
    
    # Dashboard endpoints
    path('dashboard/', ProgressDashboardView.as_view(), name='progress-dashboard'),
    path('dashboard/milestones/', DashboardMilestoneView.as_view(), name='dashboard-milestones'),
    path('contributions/', EmployeeContributionsView.as_view(), name='employee-contributions'),
    path('strategic-alignment/', StrategicAlignmentView.as_view(), name='strategic-alignment'),
    
    # Original CBV endpoints
    path('strategies/', StrategyListCreateView.as_view(), name='strategy-list-create'),
    path('strategies/<int:pk>/', StrategyRetrieveUpdateDestroyView.as_view(), name='strategy-detail'),
    
    path('strategic-goals/', StrategicGoalListCreateView.as_view(), name='strategic-goal-list-create'),
    path('strategic-goals/<int:pk>/', StrategicGoalRetrieveUpdateDestroyView.as_view(), name='strategic-goal-detail'),
    
    path('programs/', ProgramListCreateView.as_view(), name='program-list-create'),
    path('programs/<int:pk>/', ProgramRetrieveUpdateDestroyView.as_view(), name='program-detail'),
    
    path('workstreams/', WorkstreamListCreateView.as_view(), name='workstream-list-create'),
    path('workstreams/<int:pk>/', WorkstreamRetrieveUpdateDestroyView.as_view(), name='workstream-detail'),
]



# from django.urls import path
# from .views import (
#     StrategyListCreateView, StrategyRetrieveUpdateDestroyView,
#     StrategicGoalListCreateView, StrategicGoalRetrieveUpdateDestroyView,
#     ProgramListCreateView, ProgramRetrieveUpdateDestroyView,
#     WorkstreamListCreateView, WorkstreamRetrieveUpdateDestroyView,
#     MilestoneListCreateView, MilestoneRetrieveUpdateDestroyView,
#     ActivityListCreateView, ActivityRetrieveUpdateDestroyView,
#     RoadmapListCreateView, RoadmapRetrieveUpdateDestroyView,
# )

# urlpatterns = [
#     # Strategy endpoints
#     path('strategies/', StrategyListCreateView.as_view(), name='strategy-list-create'),
#     path('strategies/<int:pk>/', StrategyRetrieveUpdateDestroyView.as_view(), name='strategy-detail'),

#     # Strategic Goals
#     path('strategic-goals/', StrategicGoalListCreateView.as_view(), name='strategic-goal-list-create'),
#     path('strategic-goals/<int:pk>/', StrategicGoalRetrieveUpdateDestroyView.as_view(), name='strategic-goal-detail'),

#     # Program endpoints
#     path('programs/', ProgramListCreateView.as_view(), name='program-list-create'),
#     path('programs/<int:pk>/', ProgramRetrieveUpdateDestroyView.as_view(), name='program-detail'),

#     # Workstream endpoints
#     path('workstreams/', WorkstreamListCreateView.as_view(), name='workstream-list-create'),
#     path('workstreams/<int:pk>/', WorkstreamRetrieveUpdateDestroyView.as_view(), name='workstream-detail'),

#     # Milestone endpoints
#     path('milestones/', MilestoneListCreateView.as_view(), name='milestone-list-create'),
#     path('milestones/<int:pk>/', MilestoneRetrieveUpdateDestroyView.as_view(), name='milestone-detail'),

#     # Activity endpoints
#     path('activities/', ActivityListCreateView.as_view(), name='activity-list-create'),
#     path('activities/<int:pk>/', ActivityRetrieveUpdateDestroyView.as_view(), name='activity-detail'),

#     # Roadmap endpoints
#     path('roadmaps/', RoadmapListCreateView.as_view(), name='roadmap-list-create'),
#     path('roadmaps/<int:pk>/', RoadmapRetrieveUpdateDestroyView.as_view(), name='roadmap-detail'),
# ]
