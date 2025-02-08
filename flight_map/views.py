from rest_framework import generics, viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from django.db.models import Prefetch, Count, Q, F, Case, When, Value, IntegerField, FloatField, CharField, Avg
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.core.cache import cache
from datetime import timedelta
from .models import (
    Roadmap, Strategy, Program, Workstream,
    Milestone, Activity, StrategicGoal
)
from .serializers import (
    RoadmapSerializer, StrategySerializer,
    ProgramSerializer, WorkstreamSerializer,
    MilestoneSerializer, ActivitySerializer,
    DashboardMilestoneSerializer, EmployeeContributionSerializer,
    MilestoneStatusSerializer, ActivityStatusSerializer,
    StrategicGoalSerializer
)
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.exceptions import ValidationError
from django.contrib.auth import get_user_model

User = get_user_model()

# Maintained original CBV pattern for these models
class StrategyListCreateView(generics.ListCreateAPIView):
    """
    GET: List all strategies
    POST: Create a new strategy
    """
    queryset = Strategy.objects.all()
    serializer_class = StrategySerializer
    permission_classes = [IsAuthenticated]

class StrategyRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET: Retrieve a single strategy
    PUT/PATCH: Update a strategy
    DELETE: Delete a strategy
    """
    queryset = Strategy.objects.all()
    serializer_class = StrategySerializer
    permission_classes = [IsAuthenticated]

class StrategicGoalListCreateView(generics.ListCreateAPIView):
    """
    GET: List all strategic goals
    POST: Create a new strategic goal
    """
    queryset = StrategicGoal.objects.all()
    serializer_class = StrategicGoalSerializer
    permission_classes = [IsAuthenticated]

class StrategicGoalRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET: Retrieve a single strategic goal
    PUT/PATCH: Update a strategic goal
    DELETE: Delete a strategic goal
    """
    queryset = StrategicGoal.objects.all()
    serializer_class = StrategicGoalSerializer
    permission_classes = [IsAuthenticated]


class ProgramListCreateView(generics.ListCreateAPIView):
    """
    GET: List all programs
    POST: Create a new program
    """
    queryset = Program.objects.all()
    serializer_class = ProgramSerializer
    permission_classes = [IsAuthenticated]

class ProgramRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET: Retrieve a single program
    PUT/PATCH: Update a program
    DELETE: Delete a program
    """
    queryset = Program.objects.all()
    serializer_class = ProgramSerializer
    permission_classes = [IsAuthenticated]


class WorkstreamListCreateView(generics.ListCreateAPIView):
    """
    GET: List all workstreams
    POST: Create a new workstream
    """
    queryset = Workstream.objects.all()
    serializer_class = WorkstreamSerializer
    permission_classes = [IsAuthenticated]

class WorkstreamRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET: Retrieve a single workstream
    PUT/PATCH: Update a workstream
    DELETE: Delete a workstream
    """
    queryset = Workstream.objects.all()
    serializer_class = WorkstreamSerializer
    permission_classes = [IsAuthenticated]



# Viewsets for models with extended functionality
class RoadmapViewSet(viewsets.ModelViewSet):
    serializer_class = RoadmapSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['owner']

    def get_queryset(self):
        return Roadmap.objects.prefetch_related(
            Prefetch('strategies__programs__workstreams__milestones',
                    queryset=Milestone.objects.annotate_progress()),
            Prefetch('strategies__programs__workstreams__activities',
                    queryset=Activity.objects.annotate_delay())
        ).filter(owner=self.request.user)

    @action(detail=True, methods=['get'])
    def timeline(self, request, pk=None):
        roadmap = self.get_object()
        timeline_events = []

        for strategy in roadmap.strategies.all():
            for program in strategy.programs.all():
                for workstream in program.workstreams.all():
                    # Milestones
                    for milestone in workstream.milestones.all():
                        timeline_events.append({
                            'type': 'milestone',
                            'id': milestone.id,
                            'name': milestone.name,
                            'date': milestone.deadline,
                            'status': milestone.status,
                            'progress': milestone.current_progress
                        })
                    # Activities
                    for activity in workstream.activities.all():
                        timeline_events.append({
                            'type': 'activity',
                            'id': activity.id,
                            'name': activity.name,
                            'date': activity.target_end_date,
                            'status': activity.status,
                            'milestone': activity.milestone.id if activity.milestone else None
                        })
        
        return Response(sorted(timeline_events, key=lambda x: x['date']))

class ProgressDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        cache_key = f'dashboard_{request.user.id}'
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return Response(cached_data)

        roadmaps = Roadmap.objects.filter(
            Q(owner=request.user) |
            Q(strategies__executive_sponsors=request.user) |
            Q(strategies__strategy_leads=request.user)
        ).prefetch_related(
            Prefetch('strategies__programs__workstreams__milestones',
                    queryset=Milestone.objects.annotate(
                        timeframe_category=Case(
                            When(deadline__lte=timezone.now().date(), then=Value('overdue')),
                            When(deadline__lte=timezone.now().date() + timedelta(days=30), 
                                then=Value('next_30_days')),
                            When(deadline__lte=timezone.now().date() + timedelta(days=90), 
                                then=Value('next_90_days')),
                            default=Value('future'),
                            output_field=CharField()
                        )
                    )),
            Prefetch('strategies__programs__workstreams__activities',
                    queryset=Activity.objects.select_related('milestone'))
        ).distinct()

        response_data = {
            'summary': self.get_summary(roadmaps),
            'employee_contributions': self.get_contributions(roadmaps),
            'strategic_alignment': self.get_strategic_alignment(roadmaps)
        }

        cache.set(cache_key, response_data, 300)  # Cache for 5 minutes
        return Response(response_data)

    def get_summary(self, roadmaps):
        milestones = Milestone.objects.filter(
            workstream__program__strategy__roadmap__in=roadmaps
        )
        today = timezone.now().date()

        return {
            'total': milestones.count(),
            'completed': milestones.filter(status='completed').count(),
            'in_progress': milestones.filter(status='in_progress').count(),
            'upcoming': {
                'next_30_days': milestones.filter(
                    deadline__range=(today, today + timedelta(days=30))
                ).exclude(status='completed').count(),
                'next_90_days': milestones.filter(
                    deadline__range=(today + timedelta(days=31), today + timedelta(days=90))
                ).exclude(status='completed').count()
            }
        }

    def get_contributions(self, roadmaps):
        contributors = User.objects.filter(
            Q(milestonecontributor__milestone__workstream__program__strategy__roadmap__in=roadmaps) |
            Q(activitycontributor__activity__workstream__program__strategy__roadmap__in=roadmaps)
        ).distinct().annotate(
            total_contributions=Count(
                'milestonecontributor',
                filter=Q(milestonecontributor__milestone__status='completed'),
                distinct=True
            ) + Count(
                'activitycontributor',
                filter=Q(activitycontributor__activity__status='completed'),
                distinct=True
            )
        ).order_by('-total_contributions')

        return EmployeeContributionSerializer(contributors, many=True).data

    def get_strategic_alignment(self, roadmaps):
        return StrategicGoal.objects.filter(
            strategy__roadmap__in=roadmaps
        ).annotate(
            milestone_count=Count('associated_milestones')
        ).values('category', 'milestone_count')

class MilestoneViewSet(viewsets.ModelViewSet):
    serializer_class = MilestoneSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = {
        'status': ['exact', 'in'],
        'deadline': ['gte', 'lte', 'exact'],
        'workstream__program__strategy': ['exact']
    }

    def get_queryset(self):
        return Milestone.objects.annotate_progress().filter(
            workstream__program__strategy__roadmap__owner=self.request.user
        )


    @action(detail=True, methods=['get'])
    def insights(self, request, pk=None):
        milestone = get_object_or_404(Milestone.objects.annotate(
            total_tasks=Count('activities'),
            completed_tasks=Count('activities', filter=Q(activities__status='completed')),
            avg_completion_time=Avg(
                F('activities__completed_date') - F('activities__target_start_date'),
                filter=Q(activities__status='completed')
            ),
            delay_days=Avg(
                F('activities__completed_date') - F('activities__target_end_date'),
                filter=Q(activities__completed_date__gt=F('activities__target_end_date'))
            )
        ), pk=pk)

        return Response({
            'stats': {
                'completion_rate':  (milestone.completed_tasks / milestone.total_tasks) * 100 if milestone.total_tasks else 0,
                'avg_completion_time': milestone.avg_completion_time,
                'average_delay': milestone.delay_days
            },
            'activities': ActivitySerializer(milestone.activities.all(), many=True).data
        })

    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
        try:
            milestone = self.get_object()
            serializer = MilestoneStatusSerializer(milestone, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
        except ValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ActivityViewSet(viewsets.ModelViewSet):
    serializer_class = ActivitySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = {
        'status': ['exact', 'in'],
        'target_start_date': ['gte', 'lte'],
        'target_end_date': ['gte', 'lte'],
        'milestone': ['exact']
    }

    def get_queryset(self):
        return Activity.objects.annotate_delay().filter(
            workstream__program__strategy__roadmap__owner=self.request.user
        ).select_related('milestone', 'workstream')

    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
        activity = self.get_object()
        serializer = ActivityStatusSerializer(activity, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EmployeeContributionsView(generics.ListAPIView):
    serializer_class = EmployeeContributionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return User.objects.filter(
            Q(milestonecontributor__milestone__workstream__program__strategy__roadmap__owner=self.request.user) |
            Q(activitycontributor__activity__workstream__program__strategy__roadmap__owner=self.request.user)
        ).distinct().annotate(
            completed_milestones=Count(
                'milestonecontributor',
                filter=Q(milestonecontributor__milestone__status='completed')
            ),
            in_progress_milestones=Count(
                'milestonecontributor',
                filter=Q(milestonecontributor__milestone__status='in_progress')
            ),
            completed_activities=Count(
                'activitycontributor',
                filter=Q(activitycontributor__activity__status='completed')
            ),
            in_progress_activities=Count(
                'activitycontributor',
                filter=Q(activitycontributor__activity__status='in_progress')
            )
        ).order_by('-completed_milestones', '-completed_activities')

class StrategicAlignmentView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        goals = StrategicGoal.objects.filter(
            strategy__roadmap__owner=request.user
        ).annotate(
            milestone_count=Count('associated_milestones'),
            completed_milestones=Count(
                'associated_milestones',
                filter=Q(associated_milestones__status='completed')
            )
        )

        return Response({
            'goals': [{
                'id': g.id,
                'text': g.goal_text[:50],
                'category': g.category,
                'total_milestones': g.milestone_count,
                'completed_milestones': g.completed_milestones
            } for g in goals]
        })


# views.py
class DashboardMilestoneView(generics.ListAPIView):
    """
    GET: List milestones in dashboard format
    Filters:
    - timeframe: overdue|next_30_days|next_quarter|next_year
    - status: completed|in_progress|not_started
    - program: program_id
    - strategy: strategy_id
    """
    serializer_class = DashboardMilestoneSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = {
        'status': ['exact', 'in'],
        'deadline': ['gte', 'lte'],
        'workstream__program': ['exact'],
        'workstream__program__strategy': ['exact']
    }

    def get_queryset(self):
        return Milestone.objects.annotate_progress().filter(
            workstream__program__strategy__roadmap__owner=self.request.user
        ).select_related('workstream__program__strategy')