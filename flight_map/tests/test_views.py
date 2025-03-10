from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from flight_map.models import Program, Workstream, Milestone, Task


class ProgramViewTests(APITestCase):
    """Test that program view creates and returns data when requested"""
    def setUp(self):
        """
        Set up initial data for testing Program views.
        """
        # Create a test user and log in
        self.user = get_user_model().objects.create_user(
            username="testuser",
            password="password123"
        )
        self.client.login(username="testuser", password="password123")

        # Create a test program
        self.program_data = {
            "name": "Climate Initiative",
            "vision": "Reduce carbon emissions by 50% by 2030",
            "time_horizon": "2023-2030",
        }

    def test_create_program(self):
        """
        Test creating a program.
        """
        response = self.client.post("/programs/", self.program_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], self.program_data["name"])


    def test_get_program_list(self):
        """
        Test retrieving a list of programs.
        """
        Program.objects.create(**self.program_data)
        response = self.client.get("/programs/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)


    def test_get_program_detail(self):
        """
        Test retrieving a single program.
        """
        program = Program.objects.create(**self.program_data)
        response = self.client.get(f"/programs/{program.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], program.name)


    def test_update_program(self):
        """
        Test creating a milestone with dependencies.
        """
        program = Program.objects.create(**self.program_data)
        updated_data = {"name": "New Initiative"}
        response = self.client.patch(f"/programs/{program.id}/", updated_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], updated_data["name"])

    
    def test_delete_program(self):
        """
        Test creating a milestone with dependencies.
        """
        program = Program.objects.create(**self.program_data)
        response = self.client.delete(f"/programs/{program.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


class WorkstreamViewTests(APITestCase):
    """Test that workstream view creates and returns data when requested"""
    def setUp(self):
        """
        Set up initial data for testing Workstream views.
        """
        # Create a test user and log in
        self.user = get_user_model().objects.create_user(
            username="testuser",
            password="password123"
        )
        self.client.login(username="testuser", password="password123")

        # Create a test program
        self.program = Program.objects.create(
            name="Digital Transformation",
            vision="Digitize operations by 2025",
            time_horizon="2023-2025",
        )

        # Create test workstream data
        self.workstream_data = {
            "name": "Cloud Migration",
            "lead": "Alice Johnson",
            "sponsor": "John Smith",
            "program": self.program.id,
        }

    def test_create_workstream(self):
        """
        Test creating a workstream.
        """
        response = self.client.post("/workstreams/", self.workstream_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], self.workstream_data["name"])

    def test_get_workstream_list(self):
        """
        Test retrieving a list of workstreams.
        """
        workstream = Workstream.objects.create(
            name="Cloud Migration",
            lead="Alice Johnson",
            sponsor="John Smith",
            program=self.program,
        )

        response = self.client.get("/workstreams/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["name"], workstream.name)


class MilestoneViewTests(APITestCase):
    """Test that Milestone view creates and returns data when requested"""
    def setUp(self):
        """
        Set up initial data for testing Milestone views.
        """
        # Create a test user and log in
        self.user = get_user_model().objects.create_user(
            username="testuser",
            password="password123"
        )
        self.client.login(username="testuser", password="password123")

        # Create some test milestones to use as dependencies
        self.milestone1 = Milestone.objects.create(
            name="Phase 1 Completion",
            description="Complete the initial phase",
            deadline="2024-01-15"
        )

        self.milestone2 = Milestone.objects.create(
            name="Phase 2 Kickoff",
            description="Start the second phase",
            deadline="2024-03-01"
        )

        # Add dependencies to milestone2
        self.milestone2.dependencies.add(self.milestone1)

        # Data for creating a new milestone
        self.new_milestone_data = {
            "name": "Final Phase",
            "description": "Wrap up the project",
            "deadline": "2024-12-01",
            "dependencies": [self.milestone1.id, self.milestone2.id],  # IDs of dependent milestones
        }

    def test_create_milestone_with_dependencies(self):
        """
        Test creating a milestone with dependencies.
        """
        response = self.client.post("/milestones/", self.new_milestone_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], self.new_milestone_data["name"])
        self.assertEqual(len(response.data["dependencies"]), 2)

        # Access created milestone objects from response data
        created_milestone1 = None
        created_milestone2 = None
        for dependency in response.data["dependencies"]:
            if dependency["name"] == "Phase 1 Completion":
                created_milestone1 = dependency
            elif dependency["name"] == "Phase 2 Kickoff":
                created_milestone2 = dependency

        # Assert if expected milestones are present in dependencies
        self.assertIsNotNone(created_milestone1)
        self.assertIsNotNone(created_milestone2)

    def test_get_milestone_list(self):
        """
        Test retrieving a list of milestones.
        """
        response = self.client.get("/milestones/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_get_milestone_detail(self):
        """
        Test retrieving a single milestone, including its dependencies.
        """
        response = self.client.get(f"/milestones/{self.milestone2.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], self.milestone2.name)
        self.assertEqual(len(response.data["dependencies"]), 1)
        self.assertIn(response.data["dependencies"][0]["name"], "Phase 1 Completion")

    def test_update_milestone(self):
        """
        Test updating a milestone's name.
        """
        # First, create the milestone to update
        create_response = self.client.post("/milestones/", self.new_milestone_data, format="json")
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)

        created_milestone_id = create_response.data["id"]

        # Prepare updated data
        updated_data = {"name": "Complete Phase"}

        # Update the milestone
        response = self.client.patch(f"/milestones/{created_milestone_id}/", updated_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], updated_data["name"])

    def test_update_milestone_dependencies(self):
        """
        Test updating a milestone's dependencies.
        """
        # First, create the initial milestone and dependencies
        create_response = self.client.post("/milestones/", self.new_milestone_data, format="json")
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)

        created_milestone_id = create_response.data["id"]

        # Create a new milestone to be added as a dependency
        self.milestone3 = Milestone.objects.create(
            name="Phase 3 Planning",
            description="Plan the third phase",
            deadline="2024-06-15"
        )

        # Prepare updated data for dependencies
        updated_data = {
            "dependencies": [self.milestone1.id, self.milestone2.id, self.milestone3.id]
        }

        # Send PATCH request to update the milestone dependencies
        response = self.client.patch(f"/milestones/{created_milestone_id}/", updated_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify the dependencies were updated
        self.assertEqual(len(response.data["dependencies"]), 3)
        dependency_ids = [dependency["id"] for dependency in response.data["dependencies"]]
        self.assertIn(self.milestone1.id, dependency_ids)
        self.assertIn(self.milestone2.id, dependency_ids)
        self.assertIn(self.milestone3.id, dependency_ids)


    def test_delete_milestone(self):
        """
        Test deleting a milestone.
        """
        response = self.client.delete(f"/milestones/{self.milestone1.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Milestone.objects.filter(id=self.milestone1.id).exists())


class TaskViewTests(APITestCase):
    """Test that That view creates and returns data when requested"""

    def setUp(self):
        """
        Set up initial data for testing Milestone views.
        """
        # Create users for key stakeholders
        self.user1 = get_user_model().objects.create_user(username="manager", password="password123")
        self.user2 = get_user_model().objects.create_user(username="assistant", password="password123")
        self.client.login(username="manager", password="password123")
        
        # Create a milestone
        self.milestone = Milestone.objects.create(
            name="Initial Planning",
            description="Plan the project",
            deadline="2024-02-01"
        )

        # Task data for creation
        self.task_data = {
            "name": "Create Gantt Chart",
            "key_stakeholders": [self.user1.id, self.user2.id],
            "time_required": "2 days",
            "milestone": self.milestone.id,
        }

    def test_create_task(self):
        """Test creating a task with key stakeholders"""
        response = self.client.post("/tasks/", self.task_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], self.task_data["name"])
        self.assertEqual(response.data["time_required"], self.task_data["time_required"])
        self.assertEqual(len(response.data["key_stakeholders"]), 2)
        self.assertEqual(response.data["milestone"]["id"], self.milestone.id)

    def test_get_task_list(self):
        """Test retrieving a list of tasks"""
        # Create a task
        task = Task.objects.create(
            name="Design Mockups",
            time_required="3 days",
            milestone=self.milestone,
        )
        task.key_stakeholders.set([self.user1, self.user2])

        # Retrieve task list
        response = self.client.get("/tasks/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_get_task_detail(self):
        """Test retrieving a single task with details"""
        task = Task.objects.create(
            name="Design Mockups",
            time_required="3 days",
            milestone=self.milestone,
        )
        task.key_stakeholders.set([self.user1, self.user2])

        response = self.client.get(f"/tasks/{task.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Design Mockups")
        self.assertEqual(response.data["time_required"], "3 days")
        self.assertEqual(len(response.data["key_stakeholders"]), 2)

    def test_update_task(self):
        """Test updating a task's details"""
        task = Task.objects.create(
            name="Design Mockups",
            time_required="3 days",
            milestone=self.milestone,
        )
        task.key_stakeholders.set([self.user1])

        updated_data = {
            "name": "Updated Task Name",
            "time_required": "4 days",
            "key_stakeholders": [self.user2.id],
        }

        response = self.client.patch(f"/tasks/{task.id}/", updated_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Updated Task Name")
        self.assertEqual(response.data["time_required"], "4 days")
        self.assertEqual(len(response.data["key_stakeholders"]), 1)
        self.assertEqual(response.data["key_stakeholders"][0]["id"], self.user2.id)

    def test_delete_task(self):
        """Test deleting a task"""
        task = Task.objects.create(
            name="Delete Me",
            time_required="1 day",
            milestone=self.milestone,
        )
        task.key_stakeholders.set([self.user1])

        response = self.client.delete(f"/tasks/{task.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Task.objects.filter(id=task.id).exists())