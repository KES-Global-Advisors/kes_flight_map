from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from .models import Strategy, StrategicGoal, Program, Workstream, Milestone, Activity
from .serializers import StrategySerializer, StrategicGoalSerializer, ProgramSerializer, WorkstreamSerializer, MilestoneSerializer, ActivitySerializer


class StrategyListCreateView(generics.ListCreateAPIView):
    """
    GET: List all strategies
    POST: Create a new strategy
    """
    queryset = Strategy.objects.all()
    serializer_class = StrategySerializer

class StrategyRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET: Retrieve a single strategy
    PUT/PATCH: Update a strategy
    DELETE: Delete a strategy
    """
    queryset = Strategy.objects.all()
    serializer_class = StrategySerializer

class StrategicGoalListCreateView(generics.ListCreateAPIView):
    """
    GET: List all strategic goals
    POST: Create a new strategic goal
    """
    queryset = StrategicGoal.objects.all()
    serializer_class = StrategicGoalSerializer

class StrategicGoalRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET: Retrieve a single strategic goal
    PUT/PATCH: Update a strategic goal
    DELETE: Delete a strategic goal
    """
    queryset = StrategicGoal.objects.all()
    serializer_class = StrategicGoalSerializer


class ProgramListCreateView(generics.ListCreateAPIView):
    """
    GET: List all programs
    POST: Create a new program
    """
    queryset = Program.objects.all()
    serializer_class = ProgramSerializer

class ProgramRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET: Retrieve a single program
    PUT/PATCH: Update a program
    DELETE: Delete a program
    """
    queryset = Program.objects.all()
    serializer_class = ProgramSerializer


class WorkstreamListCreateView(generics.ListCreateAPIView):
    """
    GET: List all workstreams
    POST: Create a new workstream
    """
    queryset = Workstream.objects.all()
    serializer_class = WorkstreamSerializer

class WorkstreamRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET: Retrieve a single workstream
    PUT/PATCH: Update a workstream
    DELETE: Delete a workstream
    """
    queryset = Workstream.objects.all()
    serializer_class = WorkstreamSerializer


class MilestoneListCreateView(generics.ListCreateAPIView):
    """
    GET: List all milestones
    POST: Create a new milestone
    """
    queryset = Milestone.objects.all()
    serializer_class = MilestoneSerializer

class MilestoneRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET: Retrieve a single milestone
    PUT/PATCH: Update a milestone
    DELETE: Delete a milestone
    """
    queryset = Milestone.objects.all()
    serializer_class = MilestoneSerializer


class ActivityListCreateView(generics.ListCreateAPIView):
    """
    GET: List all activities
    POST: Create a new activity
    """
    queryset = Activity.objects.all()
    serializer_class = ActivitySerializer

class ActivityRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET: Retrieve a single activity
    PUT/PATCH: Update a activity
    DELETE: Delete a activity
    """
    queryset = Activity.objects.all()
    serializer_class = ActivitySerializer