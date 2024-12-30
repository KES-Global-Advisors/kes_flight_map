from django.db import models
from django.contrib.auth.models import User 

# Create your models here.
class Program(models.Model):
    """Create a program"""
    name = models.CharField(max_length=255)
    vision = models.TextField()
    time_horizon = models.CharField(max_length=100)
    stakeholders = models.ManyToManyField(User, related_name="programs")

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Program"
        verbose_name_plural = "Programs"
        ordering = ["name"]


class Workstream(models.Model):
    """Create A Work stream"""
    name = models.CharField(max_length=255)
    lead = models.CharField(max_length=255)
    sponsor = models.CharField(max_length=255)
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name="workstreams")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Workstream"
        verbose_name_plural = "Workstreams"
        ordering = ["name"]


class Milestone(models.Model):
    """Create a milestone"""
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    deadline = models.DateField()
    dependencies = models.ManyToManyField('self', blank=True, symmetrical=False, related_name="dependent_milestones")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Milestone"
        verbose_name_plural = "Milestones"
        ordering = ["deadline"]


class Task(models.Model):
    """Create a task"""
    name = models.TextField()
    key_stakeholders = models.TextField(blank=True, null=True)
    time_required = models.CharField(max_length=100)
    milestone = models.ForeignKey(Milestone, on_delete=models.CASCADE, related_name="tasks")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Task"
        verbose_name_plural = "Tasks"
        ordering = ["name"]