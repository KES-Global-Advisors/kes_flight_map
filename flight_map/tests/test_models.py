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
    """Test that a task is created successfully"""
    milestone = Milestone.objects.create(name="Initial Planning", deadline="2024-02-01")
    task = Task.objects.create(
        name="Create Gantt Chart",
        key_stakeholders="Project Manager",
        time_required="2 days",
        milestone=milestone
    )
    assert task.name == "Create Gantt Chart"
    assert task.key_stakeholders == "Project Manager"
    assert task.milestone == milestone