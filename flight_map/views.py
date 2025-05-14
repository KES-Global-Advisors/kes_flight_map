from rest_framework import generics, viewsets, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from django.db.models import Prefetch, Count, Q, F, Case, When, Value, IntegerField, FloatField, CharField, Avg, DurationField, ExpressionWrapper
from django.db.models.functions import TruncDate
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.core.cache import cache
from datetime import timedelta
from .models import (
    Roadmap, Strategy, Program, Workstream,
    Milestone, Activity, StrategicGoal,
    MilestoneContributor, ActivityContributor,
    NodePosition,
)
from .serializers import (
    RoadmapSerializer, StrategySerializer,
    ProgramSerializer, WorkstreamSerializer,
    MilestoneSerializer, ActivitySerializer,
    DashboardMilestoneSerializer, EmployeeContributionSerializer,
    MilestoneStatusSerializer, ActivityStatusSerializer,
    StrategicGoalSerializer, MilestoneContributorSerializer,
    ActivityContributorSerializer, NodePositionSerializer,
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
                     queryset=Milestone.objects.annotate_progress().distinct()),
            Prefetch('strategies__programs__workstreams__activities',
                     queryset=Activity.objects.annotate_delay().distinct())
        ).filter(
            Q(owner=self.request.user) |
            Q(strategies__executive_sponsors=self.request.user) |
            Q(strategies__strategy_leads=self.request.user) |
            Q(strategies__communication_leads=self.request.user) |
            Q(strategies__programs__executive_sponsors=self.request.user) |
            Q(strategies__programs__program_leads=self.request.user) |
            Q(strategies__programs__workforce_sponsors=self.request.user) |
            Q(strategies__programs__workstreams__workstream_leads=self.request.user) |
            Q(strategies__programs__workstreams__team_members=self.request.user)
        ).distinct()


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
        base_qs = Milestone.objects.annotate_progress()
        user = self.request.user
        # Related milestones: those that have a workstream and meet the user association criteria.
        related_qs = base_qs.filter(
            workstream__isnull=False
        ).filter(
            Q(workstream__program__strategy__roadmap__owner=user) |
            Q(workstream__program__strategy__executive_sponsors=user) |
            Q(workstream__program__strategy__strategy_leads=user) |
            Q(workstream__program__strategy__communication_leads=user) |
            Q(workstream__program__executive_sponsors=user) |
            Q(workstream__program__program_leads=user) |
            Q(workstream__program__workforce_sponsors=user) |
            Q(workstream__workstream_leads=user) |
            Q(workstream__team_members=user)
        )
        # Standalone milestones: those without a workstream but with updated_by set.
        standalone_qs = base_qs.filter(
            workstream__isnull=True,
            updated_by__isnull=False
        )
        return (related_qs | standalone_qs).distinct()

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

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        return Response(queryset.values('id', 'name', 'calculated_progress'))

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
        base_qs = Activity.objects.annotate_delay()

        # Activities attached to a workstream or milestone.
        related_qs = base_qs.filter(
            Q(workstream__isnull=False) | Q(milestone__isnull=False)
        ).filter(
            Q(workstream__program__strategy__roadmap__owner=self.request.user) |
            Q(workstream__program__strategy__roadmap__strategies__executive_sponsors=self.request.user) |
            Q(workstream__program__strategy__roadmap__strategies__strategy_leads=self.request.user) |
            Q(workstream__program__strategy__roadmap__strategies__communication_leads=self.request.user) |
            Q(workstream__program__executive_sponsors=self.request.user) |
            Q(workstream__program__program_leads=self.request.user) |
            Q(workstream__program__workforce_sponsors=self.request.user) |
            Q(workstream__workstream_leads=self.request.user) |
            Q(workstream__team_members=self.request.user) |
            Q(milestone__workstream__program__strategy__roadmap__owner=self.request.user) |
            Q(milestone__workstream__program__strategy__roadmap__strategies__executive_sponsors=self.request.user) |
            Q(milestone__workstream__program__strategy__roadmap__strategies__strategy_leads=self.request.user) |
            Q(milestone__workstream__program__strategy__roadmap__strategies__communication_leads=self.request.user) |
            Q(milestone__workstream__program__executive_sponsors=self.request.user) |
            Q(milestone__workstream__program__program_leads=self.request.user) |
            Q(milestone__workstream__program__workforce_sponsors=self.request.user) |
            Q(milestone__workstream__workstream_leads=self.request.user) |
            Q(milestone__workstream__team_members=self.request.user) |
            Q(workstream__program__strategy__roadmap__strategies__programs__executive_sponsors=self.request.user) |
            Q(workstream__program__strategy__roadmap__strategies__programs__program_leads=self.request.user) |
            Q(workstream__program__strategy__roadmap__strategies__programs__workstreams__workstream_leads=self.request.user) |
            Q(workstream__program__strategy__roadmap__strategies__programs__workstreams__team_members=self.request.user)
        )

        # Standalone activities: no workstream or milestone, but with updated_by set.
        standalone_qs = base_qs.filter(
            workstream__isnull=True,
            milestone__isnull=True,
            updated_by__isnull=False
        )

        return (related_qs | standalone_qs).distinct()


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
        try:
            time_range = int(request.query_params.get('time_range', 30))
        except ValueError:
            time_range = 30
    
        today = timezone.now().date()
        start_date = today - timedelta(days=time_range)
    
        completed_qs = Activity.objects.filter(
            status='completed',
            completed_date__range=(start_date, today)
        ).annotate(day=TruncDate('completed_date')).values('day').annotate(count=Count('id'))
    
        in_progress_qs = Activity.objects.filter(
            status='in_progress',
            target_end_date__range=(start_date, today)
        ).annotate(day=TruncDate('target_end_date')).values('day').annotate(count=Count('id'))
    
        failed_qs = Activity.objects.filter(
            status='completed',
            completed_date__gt=F('target_end_date'),
            completed_date__range=(start_date, today)
        ).annotate(day=TruncDate('completed_date')).values('day').annotate(count=Count('id'))
    
        completed_dict = {entry['day']: entry['count'] for entry in completed_qs}
        in_progress_dict = {entry['day']: entry['count'] for entry in in_progress_qs}
        failed_dict = {entry['day']: entry['count'] for entry in failed_qs}
    
        trend_data = []
        current_day = start_date
        while current_day <= today:
            trend_data.append({
                'date': current_day.isoformat(),
                'completed': completed_dict.get(current_day, 0),
                'in_progress': in_progress_dict.get(current_day, 0),
                'failed': failed_dict.get(current_day, 0)
            })
            current_day += timedelta(days=1)
    
        return Response(trend_data)

class PerformanceDashboardView(APIView): 
    """ 
    Returns aggregated performance metrics including: 
        • Average completion times for completed activities (based on target start dates) and milestones (using deadlines). 
        • Counts of overdue tasks versus completed tasks. 
        • Percentage of tasks that failed to meet target start/end dates and on-time completions.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        today = timezone.now().date()
        from django.db.models import Avg, Count, ExpressionWrapper, F, DurationField, Q, Value, Case, When
    
        # Average completion time for completed activities (difference between completed_date and target_start_date)
        activity_completion = Activity.objects.filter(status='completed').annotate(
            completion_time=ExpressionWrapper(F('completed_date') - F('target_start_date'), output_field=DurationField())
        ).aggregate(avg_completion_time=Avg('completion_time'))
    
        # For milestones, using the difference between completed_date and deadline
        milestone_completion = Milestone.objects.filter(status='completed').annotate(
            completion_time=ExpressionWrapper(F('completed_date') - F('deadline'), output_field=DurationField())
        ).aggregate(avg_completion_time=Avg('completion_time'))
    
        overdue_tasks = Activity.objects.filter(
            status__in=['not_started', 'in_progress'],
            target_end_date__lt=today
        ).count()
    
        completed_tasks = Activity.objects.filter(status='completed').count()
        # completed_tasks=Count('activities', filter=Q(activities__status='completed')),
    
        # Calculate tasks that completed late (failing to meet target end dates)
        failing_tasks = Activity.objects.filter(
            status='completed',
            completed_date__gt=F('target_end_date')
        ).count()
        total_completed = Activity.objects.filter(status='completed').count()
        failing_percentage = (failing_tasks / total_completed * 100) if total_completed > 0 else 0
    
        # Calculate percentage of tasks completed on time
        on_time_tasks = Activity.objects.filter(
            status='completed',
            completed_date__lte=F('target_end_date')
        ).count()
        on_time_percentage = (on_time_tasks / total_completed * 100) if total_completed > 0 else 0
    
        data = {
            'average_completion_time_activities': str(activity_completion['avg_completion_time']),
            'average_completion_time_milestones': str(milestone_completion['avg_completion_time']),
            'overdue_tasks': overdue_tasks,
            'completed_tasks': completed_tasks,
            'failing_tasks_percentage': failing_percentage,
            'on_time_percentage': on_time_percentage,
        }
        return Response(data)

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

class MilestoneContributorCreateView(generics.CreateAPIView):
    """
    API endpoint to create a MilestoneContributor.
    Expects JSON payload with 'milestone' and 'user' fields.
    """
    queryset = MilestoneContributor.objects.all()
    serializer_class = MilestoneContributorSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context

class ActivityContributorCreateView(generics.CreateAPIView):
    """
    API endpoint to create an ActivityContributor.
    Expects JSON payload with 'activity' and 'user' fields.
    """
    queryset = ActivityContributor.objects.all()
    serializer_class = ActivityContributorSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context

class NodePositionViewSet(viewsets.ModelViewSet):
    queryset = NodePosition.objects.all()
    serializer_class = NodePositionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # only positions for this flightmap (and optionally filter by group/user perms)
        fmap = self.request.query_params.get('flightmap')
        return NodePosition.objects.filter(flightmap_id=fmap)
    
    def perform_create(self, serializer):
        serializer.save(updated_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    @action(detail=False, methods=['DELETE'])
    def reset(self, request):
        flightmap_id = request.query_params.get('flightmap')
        if not flightmap_id:
            return Response({"error": "flightmap parameter is required"}, status=400)

        # Delete all positions for this flightmap
        NodePosition.objects.filter(flightmap_id=flightmap_id).delete()

        # Create default positions with appropriate spacing
        self.create_default_positions(flightmap_id, request.user)

        return Response({"message": "Reset positions with default spacing"}, status=200)

    def create_default_positions(self, flightmap_id, user):
        # Get the flightmap
        try:
            flightmap = Roadmap.objects.get(id=flightmap_id)
        except Roadmap.DoesNotExist:
            return

        # Get all workstreams related to this flightmap
        workstreams = Workstream.objects.filter(
            program__strategy__roadmap=flightmap
        ).distinct()

        # Calculate default positions for workstreams
        workstream_count = workstreams.count()
        workstream_positions = {}

        for index, workstream in enumerate(workstreams):
            # Distribute workstreams evenly in vertical space with margins
            # Using 0.1-0.9 range to leave margin at top and bottom
            rel_y = 0.1 + (0.8 * index / max(1, workstream_count - 1)) if workstream_count > 1 else 0.5

            # Store for milestone positioning
            workstream_positions[workstream.id] = rel_y

            # Create workstream position
            NodePosition.objects.create(
                flightmap=flightmap,
                node_type='workstream',
                node_id=workstream.id,
                rel_y=rel_y,
                updated_by=user
            )

        # Now position all milestones based on their workstreams
        for workstream_id, base_y in workstream_positions.items():
            # Get milestones for this workstream
            milestones = Milestone.objects.filter(workstream_id=workstream_id)

            # Group milestones by deadline to prevent overlaps
            deadline_groups = {}
            for milestone in milestones:
                deadline_str = milestone.deadline.isoformat() if milestone.deadline else "none"
                if deadline_str not in deadline_groups:
                    deadline_groups[deadline_str] = []
                deadline_groups[deadline_str].append(milestone)

            # Process each deadline group
            for group in deadline_groups.values():
                group_size = len(group)

                for i, milestone in enumerate(group):
                    # Calculate offset based on group size
                    # For a single milestone, no offset
                    # For multiple, spread them with offsets (larger groups = larger spread)
                    offset = 0
                    if group_size > 1:
                        # Create a vertical spread based on number of milestones in this group
                        # Use progressive offsets: -0.05, -0.03, 0, 0.03, 0.05 for 5 items
                        max_offset = min(0.05 * group_size, 0.15)  # Cap maximum offset
                        offset = -max_offset + (2 * max_offset * i / (group_size - 1)) if group_size > 1 else 0

                    # Create milestone position with base + offset
                    NodePosition.objects.create(
                        flightmap=flightmap,
                        node_type='milestone',
                        node_id=milestone.id,
                        rel_y=base_y + offset,
                        updated_by=user
                    )