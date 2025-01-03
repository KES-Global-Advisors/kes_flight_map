import pytest
from flight_map.models import Program, Workstream, Milestone, Task

@pytest.mark.django_db
def test_program_creation():
    """Test that a program is created successfully"""
    program = Program.objects.create(
        name="Climate Change Initiative",
        vision="Reduce carbon emissions by 50% by 2030",
        time_horizon="2023-2030"
    )

    assert program.name == "Climate Change Initiative"
    assert program.vision == "Reduce carbon emissions by 50% by 2030"
    assert program.time_horizon == "2023-2030"


@pytest.mark.django_db
def test_workstream_creation():
    """Test that a work stream is created successfully"""
    program = Program.objects.create(name="Digital Transformation")
    workstream = Workstream.objects.create(
        name="Cloud Migration",
        lead="Alice Johnson",
        sponsor="John Smith",
        program=program
    )
    assert workstream.name == "Cloud Migration"
    assert workstream.lead == "Alice Johnson"
    assert workstream.program == program


@pytest.mark.django_db
def test_milestone_creation_with_dependencies():
    """Test that a milstone is created successfully with dependencies"""
    milestone1 = Milestone.objects.create(name="Phase 1 Completion", deadline="2024-01-01")
    milestone2 = Milestone.objects.create(name="Phase 2 Kickoff", deadline="2024-03-01")
    milestone2.dependencies.add(milestone1)

    assert milestone2.name == "Phase 2 Kickoff"
    assert milestone1 in milestone2.dependencies.all()


@pytest.mark.django_db
def test_task_creation():
    """Test that a task is created successfully with key stakeholders as users"""
    from django.contrib.auth import get_user_model
    User = get_user_model()

    # Create a milestone
    milestone = Milestone.objects.create(name="Initial Planning", deadline="2024-02-01")
    
    # Create users for key stakeholders
    user1 = User.objects.create_user(username="manager", password="password123")
    user2 = User.objects.create_user(username="assistant", password="password123")
    
    # Create the task
    task = Task.objects.create(
        name="Create Gantt Chart",
        time_required="2 days",
        milestone=milestone
    )
    # Add key stakeholders
    task.key_stakeholders.set([user1, user2])
    
    # Assertions
    assert task.name == "Create Gantt Chart"
    assert list(task.key_stakeholders.all()) == [user1, user2]
    assert task.milestone == milestone
