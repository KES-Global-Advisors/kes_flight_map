from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from .models import Roadmap, Strategy, StrategicGoal, Program, Workstream, Milestone, Activity
from .serializers import RoadmapSerializer, StrategySerializer, StrategicGoalSerializer, ProgramSerializer, WorkstreamSerializer, MilestoneSerializer, ActivitySerializer


# ---- New Roadmap API View ----
class RoadmapListCreateView(generics.ListCreateAPIView):
    """
    GET: List all roadmaps
    POST: Create a new roadmap
    """
    queryset = Roadmap.objects.prefetch_related('strategies__programs__workstreams')
    serializer_class = RoadmapSerializer
    permission_classes = [IsAuthenticated]


class RoadmapRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET: Retrieve a roadmap
    PUT/PATCH: Update a roadmap
    DELETE: Delete a roadmap (cascades to strategies, programs, etc.)
    """
    queryset = Roadmap.objects.prefetch_related(
        'strategies__programs__workstreams__milestones',
        'strategies__programs__workstreams__activities',
        'strategies__executive_sponsors',  # Optimize user relationships
        'strategies__programs__executive_sponsors'
    )
    serializer_class = RoadmapSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Optional: Filter by roadmap ID or owner
        return super().get_queryset().filter(id=self.kwargs['pk'])

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


class MilestoneListCreateView(generics.ListCreateAPIView):
    """
    GET: List all milestones
    POST: Create a new milestone
    """
    queryset = Milestone.objects.all()
    serializer_class = MilestoneSerializer
    permission_classes = [IsAuthenticated]

class MilestoneRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET: Retrieve a single milestone
    PUT/PATCH: Update a milestone
    DELETE: Delete a milestone
    """
    queryset = Milestone.objects.all()
    serializer_class = MilestoneSerializer
    permission_classes = [IsAuthenticated]


class ActivityListCreateView(generics.ListCreateAPIView):
    """
    GET: List all activities
    POST: Create a new activity
    """
    queryset = Activity.objects.all()
    serializer_class = ActivitySerializer
    permission_classes = [IsAuthenticated]

class ActivityRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET: Retrieve a single activity
    PUT/PATCH: Update a activity
    DELETE: Delete a activity
    """
    queryset = Activity.objects.all()
    serializer_class = ActivitySerializer
    permission_classes = [IsAuthenticated]