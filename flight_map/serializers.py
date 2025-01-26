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

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['executive_sponsors'] = [
            {'id': sponsor.id, 'username': sponsor.username, 'email': sponsor.email}
            for sponsor in instance.executive_sponsors.all()
        ]
        representation['strategy_leads'] = [
            {'id': lead.id, 'username': lead.username, 'email': lead.email}
            for lead in instance.strategy_leads.all()
        ]
        representation['communication_leads'] = [
            {'id': lead.id, 'username': lead.username, 'email': lead.email}
            for lead in instance.communication_leads.all()
        ]
        return representation


class StrategicGoalSerializer(serializers.ModelSerializer):
    class Meta:
        model = StrategicGoal
        fields = '__all__'

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['strategy'] = {
            'id': instance.strategy.id,
            'name': instance.strategy.name,
        }
        return representation


class ProgramSerializer(serializers.ModelSerializer):
    executive_sponsors = serializers.PrimaryKeyRelatedField(many=True, queryset=User.objects.all())
    program_leads = serializers.PrimaryKeyRelatedField(many=True, queryset=User.objects.all())
    workforce_sponsors = serializers.PrimaryKeyRelatedField(many=True, queryset=User.objects.all())
    key_improvement_targets = serializers.PrimaryKeyRelatedField(many=True, queryset=StrategicGoal.objects.filter(category="business"))
    key_organizational_goals = serializers.PrimaryKeyRelatedField(many=True, queryset=StrategicGoal.objects.filter(category="organizational"))

    class Meta:
        model = Program
        fields = '__all__'

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['strategy'] = {
            'id': instance.strategy.id,
            'name': instance.strategy.name,
        }
        representation['executive_sponsors'] = [
            {'id': sponsor.id, 'username': sponsor.username, 'email': sponsor.email}
            for sponsor in instance.executive_sponsors.all()
        ]
        representation['program_leads'] = [
            {'id': lead.id, 'username': lead.username, 'email': lead.email}
            for lead in instance.program_leads.all()
        ]
        representation['workforce_sponsors'] = [
            {'id': sponsor.id, 'username': sponsor.username, 'email': sponsor.email}
            for sponsor in instance.workforce_sponsors.all()
        ]
        return representation


class WorkstreamSerializer(serializers.ModelSerializer):
    workstream_leads = serializers.PrimaryKeyRelatedField(many=True, queryset=User.objects.all())
    team_members = serializers.PrimaryKeyRelatedField(many=True, queryset=User.objects.all())

    class Meta:
        model = Workstream
        fields = '__all__'

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['program'] = {
            'id': instance.program.id,
            'name': instance.program.name,
        }
        representation['workstream_leads'] = [
            {'id': lead.id, 'username': lead.username, 'email': lead.email}
            for lead in instance.workstream_leads.all()
        ]
        representation['team_members'] = [
            {'id': member.id, 'username': member.username, 'email': member.email}
            for member in instance.team_members.all()
        ]
        return representation

class MilestoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Milestone
        fields = '__all__'

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['workstream'] = {
            'id': instance.workstream.id,
            'name': instance.workstream.name,
        }
        return representation

class ActivitySerializer(serializers.ModelSerializer):
    prerequisite_activities = serializers.PrimaryKeyRelatedField(many=True, queryset=Activity.objects.all())
    parallel_activities = serializers.PrimaryKeyRelatedField(many=True, queryset=Activity.objects.all())
    successive_activities = serializers.PrimaryKeyRelatedField(many=True, queryset=Activity.objects.all())

    class Meta:
        model = Activity
        fields = '__all__'

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['workstream'] = {
            'id': instance.workstream.id,
            'name': instance.workstream.name,
        }
        if instance.milestone:
            representation['milestone'] = {
                'id': instance.milestone.id,
                'name': instance.milestone.name,
            }
        representation['prerequisite_activities'] = [
            {'id': activity.id, 'name': activity.name}
            for activity in instance.prerequisite_activities.all()
        ]
        representation['parallel_activities'] = [
            {'id': activity.id, 'name': activity.name}
            for activity in instance.parallel_activities.all()
        ]
        representation['successive_activities'] = [
            {'id': activity.id, 'name': activity.name}
            for activity in instance.successive_activities.all()
        ]
        return representation