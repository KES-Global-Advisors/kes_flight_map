from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db.models import (
    Case, When, Value, FloatField, IntegerField, F, ExpressionWrapper,
    DurationField, Count, Q
)
from django.db.models.functions import ExtractDay, Greatest
from .current_user_middleware import get_current_user

User = get_user_model()


class MilestoneQuerySet(models.QuerySet):
    def annotate_progress(self):
        return self.annotate(
            calculated_progress=Case(
                When(activities__isnull=True, then=Value(0.0)),
                default=100.0 * Count(
                    'activities',
                    filter=Q(activities__status='completed')
                ) / Greatest(Count('activities'), 1),
                output_field=FloatField()
            )
        )
    
class ActivityQuerySet(models.QuerySet):
    def annotate_delay(self):
        return self.annotate(
            delay_days=Case(
                When(
                    completed_date__isnull=False,
                    completed_date__gt=F('target_end_date'),
                    then=ExtractDay(
                        ExpressionWrapper(
                            F('completed_date') - F('target_end_date'),
                            output_field=DurationField()
                        )
                    )
                ),
                default=Value(0),
                output_field=IntegerField()
            )
        )
    
class Roadmap(models.Model):
    """Central roadmap container for all components"""
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="owned_roadmaps")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-created_at']

class Strategy(models.Model):
    """Strategic initiative container"""
    roadmap = models.ForeignKey(Roadmap, on_delete=models.CASCADE, related_name="strategies")
    name = models.CharField(max_length=255)
    tagline = models.CharField(max_length=255, blank=True, null=True)
    vision = models.TextField()
    time_horizon = models.DateField()

    # Governance
    executive_sponsors = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="strategy_executive_sponsors")
    strategy_leads = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="strategy_leads")
    communication_leads = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="strategy_communication_leads")

    def __str__(self):
        return self.name

    def clean(self):
        if self.roadmap:
            latest_program_date = self.programs.aggregate(models.Max('time_horizon'))['time_horizon__max']
            if latest_program_date and self.time_horizon < latest_program_date:
                raise ValidationError("Strategy time horizon cannot be earlier than its latest program's horizon.")

    class Meta:
        verbose_name = "Strategy"
        verbose_name_plural = "Strategies"
        ordering = ["-time_horizon"]

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
        unique_together = ('strategy', 'goal_text')
        ordering = ['category']

class Program(models.Model):
    """Program implementation of strategy"""
    strategy = models.ForeignKey(Strategy, on_delete=models.CASCADE, related_name="programs")
    name = models.CharField(max_length=255)
    vision = models.TextField(blank=True, null=True)
    time_horizon = models.DateField(db_index=True)

    # Governance
    executive_sponsors = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="program_executive_sponsors")
    program_leads = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="program_leads")
    workforce_sponsors = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="program_workforce_sponsors")

    # Goals
    key_improvement_targets = models.ManyToManyField(StrategicGoal, related_name="program_improvement_targets", blank=True)
    key_organizational_goals = models.ManyToManyField(StrategicGoal, related_name="program_organizational_goals", blank=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.name.strip():
            self.name = self.strategy.name
        super().save(*args, **kwargs)

    def clean(self):
        if self.strategy and self.time_horizon > self.strategy.time_horizon:
            raise ValidationError("Program time horizon cannot exceed its parent strategy's horizon.")

    class Meta:
        verbose_name = "Program"
        verbose_name_plural = "Programs"
        ordering = ["-time_horizon"]

class Workstream(models.Model):
    """Workstream within a program"""
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name="workstreams")
    name = models.CharField(max_length=255)
    vision = models.TextField(blank=True, null=True)
    time_horizon = models.DateField()

    # Governance
    workstream_leads = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="workstream_leads")
    team_members = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="workstream_team_members")
    improvement_targets = models.JSONField(default=list)
    organizational_goals = models.JSONField(default=list)

    # New field to capture the color of the workstream
    color = models.CharField(max_length=7, default='#22d3ee')

    def __str__(self):
        return self.name

    def get_contributors(self):
         return self.workstream_leads.all() | self.team_members.all()

    
    class Meta:
        verbose_name = "Workstream"
        verbose_name_plural = "Workstreams"
        ordering = ["name"]

class Milestone(models.Model):
    """Progress tracking milestone"""
    STATUS_CHOICES = [
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    ]

    workstream = models.ForeignKey('Workstream', on_delete=models.CASCADE, null=True, blank=True, related_name="milestones")
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    deadline = models.DateField(db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not_started', db_index=True)
    completed_date = models.DateField(null=True, blank=True)
    strategic_goals = models.ManyToManyField('StrategicGoal', related_name="associated_milestones", blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # NEW: Allow a milestone to depend on other milestones.
    dependencies = models.ManyToManyField(
        "self",
        symmetrical=False,
        related_name="dependent_milestones",
        blank=True,
        help_text="Milestones that must be completed before this milestone can be achieved."
    )

    # Add a parent milestone field:
    parent_milestone = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        related_name='child_milestones',
        on_delete=models.SET_NULL,
        help_text="The direct parent milestone that this milestone depends on."
    )

    # capture who updated this milestone
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="updated_milestones"
    )

    objects = MilestoneQuerySet.as_manager()

    def __str__(self):
        return f"{self.workstream.name} - {self.name}"

    def save(self, *args, **kwargs):
        # Automatically set completed_date if status is completed and not already set        
        if self.status == 'completed' and not self.completed_date:
            self.completed_date = timezone.now().date()
        elif self.status != 'completed' and self.completed_date:
            self.completed_date = None
        super().save(*args, **kwargs)

    @property
    def current_progress(self):
        """
        Returns the progress of the milestone.
        Uses annotated value if available, otherwise calculates it.
        """
        if hasattr(self, 'calculated_progress'):
            return self.calculated_progress
            
        activities = self.activities.all()
        if not activities.exists():
            return 0
        completed = activities.filter(status='completed').count()
        return int((completed / activities.count()) * 100)

    def timeframe_category(self):
        today = timezone.now().date()
        delta = (self.deadline - today).days
        
        if delta < 0:
            return 'overdue'
        elif delta <= 30:
            return 'next_30_days'
        elif delta <= 90:
            return 'next_quarter'
        elif delta <= 365:
            return 'next_year'
        return 'future'

    class Meta:
        verbose_name = "Milestone"
        verbose_name_plural = "Milestones"
        ordering = ["deadline"]
        unique_together = (("workstream", "name"),)

class MilestoneContributor(models.Model):
    milestone = models.ForeignKey(Milestone, on_delete=models.CASCADE, related_name="contributors")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('milestone', 'user')

class Activity(models.Model):
    """Detailed work activity"""
    STATUS_CHOICES = [
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    ]

    workstream = models.ForeignKey(Workstream, on_delete=models.CASCADE, null=True, blank=True, related_name="activities")
    milestone = models.ForeignKey(Milestone, on_delete=models.SET_NULL, null=True, blank=True, related_name="activities")
    name = models.CharField(max_length=255)
    priority = models.IntegerField(choices=[(1, "High"), (2, "Medium"), (3, "Low")])
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not_started', db_index=True)
    completed_date = models.DateField(null=True, blank=True)
    actual_start_date = models.DateField(null=True, blank=True)
    delay_reason = models.TextField(blank=True)
    objects = ActivityQuerySet.as_manager()
    updated_at = models.DateTimeField(auto_now=True)

    # Relationships
    prerequisite_activities = models.ManyToManyField("self", symmetrical=False, related_name="prerequisite_for", blank=True)
    parallel_activities = models.ManyToManyField("self", symmetrical=False, related_name="parallel_with", blank=True)
    successive_activities = models.ManyToManyField("self", symmetrical=False, related_name="successor_to", blank=True)

    # Governance
    impacted_employee_groups = models.JSONField(default=list)
    change_leaders = models.JSONField(default=list)
    development_support = models.JSONField(default=list)
    external_resources = models.JSONField(default=list)
    corporate_resources = models.JSONField(default=list)

    target_start_date = models.DateField()
    target_end_date = models.DateField(db_index=True)

    # New field to capture who updated this activity
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="updated_activities"
    )

    # New field to capture which milestones this activity supports for cross‐workstream support
    supported_milestones = models.ManyToManyField(
        Milestone,
        blank=True,
        related_name="supported_by_activities",
        help_text="Milestones (potentially in other workstreams) that this activity supports."
    )

    # New field to capture additional milestone connections for sequential/parallel or multiple milestone connections
    additional_milestones = models.ManyToManyField(
        Milestone,
        blank=True,
        related_name="additional_activities",
        help_text="Extra milestone connections (for sequential/parallel relationships)."
    )

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # Automatically set completed_date if status is completed and not already set
        if self.status == 'completed' and not self.completed_date:
            self.completed_date = timezone.now().date()
        elif self.status != 'completed' and self.completed_date:
            self.completed_date = None
        super().save(*args, **kwargs)

    def clean(self):
        all_related = (self.prerequisite_activities.all() | 
                      self.parallel_activities.all() |
                      self.successive_activities.all())
        if self in all_related:
            raise ValidationError("Activity cannot reference itself in dependencies")
        if self.actual_start_date and self.target_start_date:
            if self.actual_start_date < self.target_start_date:
                raise ValidationError("Actual start cannot be before target start")
        if self.target_start_date >= self.target_end_date:
            raise ValidationError("Target start date must be before end date")
        if self.completed_date and self.completed_date < self.target_start_date:
            raise ValidationError("Completion date cannot be before target start date")
        if self.workstream is not None and self.milestone is not None:
            raise ValidationError("An activity should not be both under a milestone and directly under a workstream")
    

    class Meta:
        verbose_name = "Activity"
        verbose_name_plural = "Activities"
        ordering = ["target_end_date"]

class ActivityContributor(models.Model):
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, related_name="contributors")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('activity', 'user')

class NodePosition(models.Model):
    FLIGHTMAP = 'flightmap'
    NODE_TYPES = [
        ('workstream', 'Workstream'),
        ('milestone',   'Milestone'),
    ]
    flightmap   = models.ForeignKey(Roadmap, on_delete=models.CASCADE, related_name="positions")
    node_type   = models.CharField(max_length=12, choices=NODE_TYPES)
    node_id     = models.CharField(max_length=100)  # e.g. milestone.id or workstream.id
    rel_y       = models.FloatField()    # 0.0–1.0 relative vertical position
    updated_at  = models.DateTimeField(auto_now=True)
    updated_by  = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    
    # Add these new fields to track duplicates
    is_duplicate = models.BooleanField(default=False)
    duplicate_key = models.CharField(max_length=100, null=True, blank=True)  # To store the generated duplicate ID
    original_node_id = models.IntegerField(null=True, blank=True)  # Reference to the original node
    
    # class Meta:
    #     # Unique constraint needs to include duplicate_key for duplicate nodes
    #     unique_together = ('flightmap', 'node_type', 'node_id', 'duplicate_key')