from rest_framework import serializers
from .models import Strategy, StrategicGoal, Program, Workstream, Milestone, Activity
from django.contrib.auth import get_user_model

# Dynamically retrieve the user model based on AUTH_USER_MODEL setting
User = get_user_model()
class StrategySerializer(serializers.ModelSerializer):
    executive_sponsors = serializers.PrimaryKeyRelatedField(many=True, queryset=User.objects.all())
    strategy_leads = serializers.PrimaryKeyRelatedField(many=True, queryset=User.objects.all())
    communication_leads = serializers.PrimaryKeyRelatedField(many=True, queryset=User.objects.all())

    class Meta:
        model = Strategy
        fields = '__all__'


class StrategicGoalSerializer(serializers.ModelSerializer):
    class Meta:
        model = StrategicGoal
        fields = '__all__'


class ProgramSerializer(serializers.ModelSerializer):
    executive_sponsors = serializers.PrimaryKeyRelatedField(many=True, queryset=User.objects.all())
    program_leads = serializers.PrimaryKeyRelatedField(many=True, queryset=User.objects.all())
    workforce_sponsors = serializers.PrimaryKeyRelatedField(many=True, queryset=User.objects.all())
    key_improvement_targets = serializers.PrimaryKeyRelatedField(many=True, queryset=StrategicGoal.objects.filter(category="business"))
    key_organizational_goals = serializers.PrimaryKeyRelatedField(many=True, queryset=StrategicGoal.objects.filter(category="organizational"))

    class Meta:
        model = Program
        fields = '__all__'


class WorkstreamSerializer(serializers.ModelSerializer):
    workstream_leads = serializers.PrimaryKeyRelatedField(many=True, queryset=User.objects.all())
    team_members = serializers.PrimaryKeyRelatedField(many=True, queryset=User.objects.all())

    class Meta:
        model = Workstream
        fields = '__all__'


class MilestoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Milestone
        fields = '__all__'


class ActivitySerializer(serializers.ModelSerializer):
    prerequisite_activities = serializers.PrimaryKeyRelatedField(many=True, queryset=Activity.objects.all())
    parallel_activities = serializers.PrimaryKeyRelatedField(many=True, queryset=Activity.objects.all())
    successive_activities = serializers.PrimaryKeyRelatedField(many=True, queryset=Activity.objects.all())

    class Meta:
        model = Activity
        fields = '__all__'

