from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError

# Create your models here.

class Roadmap(models.Model):
    """Central roadmap container for all components"""
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="owned_roadmaps")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Strategy(models.Model):
    """Create a strategy"""
    roadmap = models.ForeignKey(Roadmap, on_delete=models.CASCADE, related_name="strategies")  # Link to Roadmap
    name = models.CharField(max_length=255)
    tagline = models.CharField(max_length=255, blank=True, null=True)
    vision = models.TextField()
    time_horizon = models.DateField()

    #Governance
    executive_sponsors = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="strategy_executive_sponsors")
    strategy_leads = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="strategy_leads")
    communication_leads = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="strategy_communication_leads")

    # Goals - Using JSONField for better structure and to allow multiple goals
    key_business_goals = models.JSONField(default=list) # Stores list of goals
    key_organizational_goals = models.JSONField(default=list) # Stores list of goals

    def __str__(self):
        return self.name

    def clean(self):
        # Validate against parent Roadmap
        if self.roadmap:
            latest_program_date = self.programs.aggregate(models.Max('time_horizon'))['time_horizon__max']
            if latest_program_date and self.time_horizon < latest_program_date:
                raise ValidationError("Strategy time horizon cannot be earlier than its latest program's horizon.")
    
    class Meta:
        verbose_name = "Strategy"
        verbose_name_plural = "Strategies"
        ordering = ["name"]

class StrategicGoal(models.Model):
    STRATEGIC_GOAL_CATEGORIES = [
        ("business", "Business Goal"),
        ("organizational", "Organizational Goal"),
    ]
    strategy = models.ForeignKey(Strategy, on_delete=models.CASCADE, related_name="goals")
    category = models.CharField(max_length=20, choices=STRATEGIC_GOAL_CATEGORIES)
    goal_text = models.TextField()

    def __str__(self):
        return f"{self.strategy.name} - {self.goal_text[:30]}"

    class Meta:
        unique_together = ('strategy', 'goal_text')  # Prevent duplicate goals per strategy


class Program(models.Model):
    """Create a program"""
    strategy = models.ForeignKey(Strategy, on_delete=models.CASCADE, related_name="programs")
    # Automatically populate name from Strategy
    name = models.CharField(max_length=255)
    vision = models.TextField(blank=True, null=True)
    time_horizon = models.DateField()

    # Governance
    executive_sponsors = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="program_executive_sponsors")
    program_leads = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="program_leads")
    workforce_sponsors = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="program_workforce_sponsors")

    # Goals
    key_improvement_targets = models.ManyToManyField(StrategicGoal, related_name="program_improvement_targets")
    key_organizational_goals = models.ManyToManyField(StrategicGoal, related_name="program_organizational_goals")

    def __str__(self):
        return self.name or self.strategy.name  # Fallback to strategy name if program name not set
    
    def save(self, *args, **kwargs):
        # If name is not set, use strategy name
        if not self.name:
            self.name = self.strategy.name
        super().save(*args, **kwargs)

    def clean(self):
        # Validate against parent Strategy
        if self.strategy and self.time_horizon > self.strategy.time_horizon:
            raise ValidationError("Program time horizon cannot exceed its parent strategy's horizon.")

    class Meta:
        verbose_name = "Program"
        verbose_name_plural = "Programs"
        ordering = ["name"]


class Workstream(models.Model):
    """Create A Work stream"""
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name="workstreams")
    name = models.CharField(max_length=255)
    vision = models.TextField(blank=True, null=True)
    time_horizon = models.DateField()

    # Governance
    workstream_leads = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="workstream_leads")
    team_members = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="workstream_team_members")

    # Goals
    improvement_targets = models.JSONField(default=list)  # JSON Field: Multiple targets
    organizational_goals = models.JSONField(default=list)  # JSON Field: Multiple goals

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Workstream"
        verbose_name_plural = "Workstreams"
        ordering = ["name"]


class Milestone(models.Model):
    """Create a milestone"""
    workstream = models.ForeignKey(Workstream, on_delete=models.CASCADE, related_name="milestones")
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    deadline = models.DateField()

    def __str__(self):
        return f"{self.workstream.name} - {self.name}"
    
    class Meta:
        verbose_name = "Milestone"
        verbose_name_plural = "Milestones"
        ordering = ["deadline"]



class Activity(models.Model):
    workstream = models.ForeignKey(Workstream, on_delete=models.CASCADE, related_name="activities")
    milestone = models.ForeignKey(Milestone, on_delete=models.SET_NULL, null=True, related_name="activities")
    name = models.CharField(max_length=255)
    priority = models.IntegerField(choices=[(1, "1"), (2, "2"), (3, "3")])

    # Activity Relationships
    prerequisite_activities = models.ManyToManyField("self", symmetrical=False, related_name="prerequisite_for", blank=True)
    parallel_activities = models.ManyToManyField("self", symmetrical=False, related_name="parallel_with", blank=True)
    successive_activities = models.ManyToManyField("self", symmetrical=False, related_name="successor_to", blank=True)

    # Governance
    impacted_employee_groups = models.JSONField(default=list)  # JSON: List of positions
    change_leaders = models.JSONField(default=list)  # JSON: List of leaders
    development_support = models.JSONField(default=list)  # JSON: List of development/execution support teams
    external_resources = models.JSONField(default=list)  # JSON: External company names
    corporate_resources = models.JSONField(default=list)  # JSON: Team names

    target_start_date = models.DateField()
    target_end_date = models.DateField()

    def __str__(self):
        return self.name

    def clean(self):
        if self.pk:
            for rel_field in [self.prerequisite_activities, self.parallel_activities, self.successive_activities]:
                if rel_field.filter(pk=self.pk).exists():
                    raise ValidationError("Activity cannot reference itself in any dependency field.")

    class Meta:
        verbose_name = "Activity"
        verbose_name_plural = "Activities"
        ordering = ["target_end_date"]
