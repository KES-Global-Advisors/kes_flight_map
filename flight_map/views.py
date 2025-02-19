from rest_framework import generics, viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from django.db.models import Prefetch, Count, Q, F, Case, When, Value, IntegerField, FloatField, CharField, Avg
from django.db.models.functions import TruncDate
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


# New views for data analysis
class TrendAnalysisView(APIView):
    """
    Returns trend data showing daily counts of completed vs. in-progress activities
    for a given time range (default: last 30 days). You can pass an optional query
    parameter 'time_range' (in days) to adjust the range.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Default time range is 30 days unless specified in query params
        try:
            time_range = int(request.query_params.get('time_range', 30))
        except ValueError:
            time_range = 30

        today = timezone.now().date()
        start_date = today - timedelta(days=time_range)

        # Get completed activities by their completion date within the range.
        completed_qs = Activity.objects.filter(
            status='completed',
            completed_date__range=(start_date, today)
        ).annotate(day=TruncDate('completed_date')).values('day').annotate(count=Count('id'))

        # Get in-progress activities by their target end date within the range.
        in_progress_qs = Activity.objects.filter(
            status='in_progress',
            target_end_date__range=(start_date, today)
        ).annotate(day=TruncDate('target_end_date')).values('day').annotate(count=Count('id'))

        # Convert queryset results into dictionaries keyed by date.
        completed_dict = {entry['day']: entry['count'] for entry in completed_qs}
        in_progress_dict = {entry['day']: entry['count'] for entry in in_progress_qs}

        # Build trend data for each day in the range.
        trend_data = []
        current_day = start_date
        while current_day <= today:
            trend_data.append({
                'date': current_day.isoformat(),
                'completed': completed_dict.get(current_day, 0),
                'in_progress': in_progress_dict.get(current_day, 0)
            })
            current_day += timedelta(days=1)

        return Response(trend_data)


class RiskAssessmentView(APIView):
    """
    Analyzes milestones (that are not yet completed) and returns a risk metric for each.
    Risk is determined based on the milestone's deadline, current progress, and activity delays.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        today = timezone.now().date()
        # Select milestones for roadmaps owned by the current user that are not completed.
        milestones = Milestone.objects.filter(
            workstream__program__strategy__roadmap__owner=request.user,
            status__in=['not_started', 'in_progress']
        )

        risks = []
        for milestone in milestones:
            # Use the milestone property (or annotation) for current progress.
            progress = milestone.current_progress
            total_activities = milestone.activities.count()
            overdue_activities = milestone.activities.filter(
                status__in=['not_started', 'in_progress'],
                target_end_date__lt=today
            ).count()
            delay_probability = (overdue_activities / total_activities * 100) if total_activities > 0 else 0

            # Determine risk level
            if milestone.deadline < today:
                risk_level = 'high'
            elif (milestone.deadline - today).days <= 7 and progress < 50:
                risk_level = 'medium'
            elif progress < 75:
                risk_level = 'low'
            else:
                risk_level = 'low'

            # Identify contributing factors.
            factors = []
            if milestone.deadline < today:
                factors.append("Deadline passed")
            if progress < 50:
                factors.append("Low progress")
            if delay_probability > 50:
                factors.append("Many overdue tasks")

            risks.append({
                'milestone_id': milestone.id,
                'name': milestone.name,
                'risk_level': risk_level,
                'factors': factors,
                'delay_probability': round(delay_probability, 2)
            })

        return Response(risks)


class ResourceAllocationView(APIView):
    """
    Returns workload distribution for team members involved in roadmaps owned by the
    current user. For each user, it provides counts of current, upcoming, and overdue tasks.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        today = timezone.now().date()
        # Filter users associated with activities in roadmaps owned by the current user.
        users = User.objects.filter(
            Q(activitycontributor__activity__workstream__program__strategy__roadmap__owner=request.user)
        ).distinct().annotate(
            current_tasks=Count(
                'activitycontributor',
                filter=Q(activitycontributor__activity__status='in_progress')
            ),
            upcoming_tasks=Count(
                'activitycontributor',
                filter=Q(
                    activitycontributor__activity__status='not_started',
                    activitycontributor__activity__target_start_date__gt=today
                )
            ),
            overdue_tasks=Count(
                'activitycontributor',
                filter=Q(
                    activitycontributor__activity__status__in=['not_started', 'in_progress'],
                    activitycontributor__activity__target_end_date__lt=today
                )
            )
        )

        workload_data = []
        for user in users:
            workload_data.append({
                'user': user.username,
                'current_tasks': user.current_tasks,
                'upcoming_tasks': user.upcoming_tasks,
                'overdue_tasks': user.overdue_tasks
            })

        return Response(workload_data)
