from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    FlightmapViewSet, MilestoneViewSet, ActivityViewSet,
    ProgressDashboardView, EmployeeContributionsView,
    StrategicAlignmentView,
    StrategyListCreateView, StrategyRetrieveUpdateDestroyView,
    StrategicGoalListCreateView, StrategicGoalRetrieveUpdateDestroyView,
    ProgramListCreateView, ProgramRetrieveUpdateDestroyView,
    WorkstreamListCreateView, WorkstreamRetrieveUpdateDestroyView,
    DashboardMilestoneView, TrendAnalysisView, RiskAssessmentView,
    ResourceAllocationView, MilestoneContributorCreateView,
    ActivityContributorCreateView, PerformanceDashboardView,
    NodePositionViewSet,
)

router = DefaultRouter()
router.register(r'flightmaps', FlightmapViewSet, basename='flightmap')
router.register(r'milestones', MilestoneViewSet, basename='milestone')
router.register(r'activities', ActivityViewSet, basename='activity')
router.register(r'positions', NodePositionViewSet, basename='position')

urlpatterns = [
    # New viewsets
    path('', include(router.urls)),
    
    # Dashboard endpoints
    path('dashboard/', ProgressDashboardView.as_view(), name='progress-dashboard'),
    path('dashboard/milestones/', DashboardMilestoneView.as_view(), name='dashboard-milestones'),
    path('dashboard/performance/', PerformanceDashboardView.as_view(), name='performance-dashboard'),
    path('contributions/', EmployeeContributionsView.as_view(), name='employee-contributions'),
    path('strategic-alignment/', StrategicAlignmentView.as_view(), name='strategic-alignment'),

    # Analysis endpoints
    path('dashboard/trends/', TrendAnalysisView.as_view(), name='trend-analysis'),
    path('dashboard/risks/', RiskAssessmentView.as_view(), name='risk-assessment'),
    path('dashboard/workloads/', ResourceAllocationView.as_view(), name='resource-allocation'),
    
    # Original CBV endpoints
    path('strategies/', StrategyListCreateView.as_view(), name='strategy-list-create'),
    path('strategies/<int:pk>/', StrategyRetrieveUpdateDestroyView.as_view(), name='strategy-detail'),
    
    path('strategic-goals/', StrategicGoalListCreateView.as_view(), name='strategic-goal-list-create'),
    path('strategic-goals/<int:pk>/', StrategicGoalRetrieveUpdateDestroyView.as_view(), name='strategic-goal-detail'),
    
    path('programs/', ProgramListCreateView.as_view(), name='program-list-create'),
    path('programs/<int:pk>/', ProgramRetrieveUpdateDestroyView.as_view(), name='program-detail'),
    
    path('workstreams/', WorkstreamListCreateView.as_view(), name='workstream-list-create'),
    path('workstreams/<int:pk>/', WorkstreamRetrieveUpdateDestroyView.as_view(), name='workstream-detail'),

    # Contributors
    path('milestone-contributors/', MilestoneContributorCreateView.as_view(), name='milestone-contributor-create'),
    path('activity-contributors/', ActivityContributorCreateView.as_view(), name='activity-contributor-create'),
]