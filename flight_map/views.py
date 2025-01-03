from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from .models import Program, Workstream, Milestone, Task
from .serializers import ProgramSerializer, WorkstreamSerializer, MilestoneSerializer, TaskSerializer


# Program Views
class ProgramListCreateView(generics.ListCreateAPIView):
    """
    GET: List all programs
    POST: Create a new program
    """
    queryset = Program.objects.all()
    serializer_class = ProgramSerializer
    permission_classes = [IsAuthenticated]  # Ensure only authenticated users can access


class ProgramRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET: Retrieve a single program
    PUT/PATCH: Update a program
    DELETE: Delete a program
    """
    queryset = Program.objects.all()
    serializer_class = ProgramSerializer
    permission_classes = [IsAuthenticated]


# Workstream Views
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


# Milestone Views
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


# Task Views
class TaskListCreateView(generics.ListCreateAPIView):
    """
    GET: List all tasks
    POST: Create a new task
    """
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]


class TaskRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET: Retrieve a single task
    PUT/PATCH: Update a task
    DELETE: Delete a task
    """
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]
