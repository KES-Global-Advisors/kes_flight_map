from rest_framework import serializers
from .models import Roadmap, Strategy, StrategicGoal, Program, Workstream, Milestone, Activity
from django.contrib.auth import get_user_model

# Dynamically retrieve the user model based on AUTH_USER_MODEL setting
User = get_user_model()

# ---- New Roadmap Serializer ----

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
    


class MilestoneSerializer(serializers.ModelSerializer):
    activities = ActivitySerializer(many=True, read_only=True)
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


class WorkstreamSerializer(serializers.ModelSerializer):
        # Add nested milestones and activities
    milestones = MilestoneSerializer(many=True, read_only=True)
    activities = ActivitySerializer(many=True, read_only=True)
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
            {'id': lead.id, 'username': lead.username}
            for lead in instance.workstream_leads.all()
        ]
        representation['team_members'] = [
            {'id': member.id, 'username': member.username}
            for member in instance.team_members.all()
        ]
        return representation


class ProgramSerializer(serializers.ModelSerializer):
        # Add nested workstreams and goals
    workstreams = WorkstreamSerializer(many=True, read_only=True)
    executive_sponsors = serializers.PrimaryKeyRelatedField(many=True, queryset=User.objects.all())
    program_leads = serializers.PrimaryKeyRelatedField(many=True, queryset=User.objects.all())
    workforce_sponsors = serializers.PrimaryKeyRelatedField(many=True, queryset=User.objects.all())
    # Allow writing via IDs while nesting read data
    key_improvement_targets = StrategicGoalSerializer(many=True, read_only=True)
    key_organizational_goals = StrategicGoalSerializer(many=True, read_only=True)
    key_improvement_targets_ids = serializers.PrimaryKeyRelatedField(
        many=True, 
        queryset=StrategicGoal.objects.filter(category="business"), 
        source='key_improvement_targets',
        write_only=True,
        required=False
    )
    key_organizational_goals_ids = serializers.PrimaryKeyRelatedField(
        many=True, 
        queryset=StrategicGoal.objects.filter(category="organizational"), 
        source='key_organizational_goals',
        write_only=True,
        required=False
    )

    class Meta:
        model = Program
        fields = (
            'id', 'strategy', 'name', 'vision', 'time_horizon', 
            'executive_sponsors', 'program_leads', 'workforce_sponsors',
            'key_improvement_targets', 'key_organizational_goals',
            'workstreams', 'key_improvement_targets_ids', 'key_organizational_goals_ids'
        )

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['strategy'] = {
            'id': instance.strategy.id,
            'name': instance.strategy.name,
        }
        representation['executive_sponsors'] = [
            {'id': sponsor.id, 'username': sponsor.username}
            for sponsor in instance.executive_sponsors.all()
        ]
        representation['program_leads'] = [
            {'id': lead.id, 'username': lead.username}
            for lead in instance.program_leads.all()
        ]
        representation['workforce_sponsors'] = [
            {'id': sponsor.id, 'username': sponsor.username}
            for sponsor in instance.workforce_sponsors.all()
        ]
        return representation
    

class StrategySerializer(serializers.ModelSerializer):
    programs = ProgramSerializer(many=True, read_only=True)
    executive_sponsors = serializers.PrimaryKeyRelatedField(many=True, queryset=User.objects.all())
    strategy_leads = serializers.PrimaryKeyRelatedField(many=True, queryset=User.objects.all())
    communication_leads = serializers.PrimaryKeyRelatedField(many=True, queryset=User.objects.all())

    class Meta:
        model = Strategy
        fields = '__all__'

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['executive_sponsors'] = [
            {'id': sponsor.id, 'username': sponsor.username}
            for sponsor in instance.executive_sponsors.all()
        ]
        representation['strategy_leads'] = [
            {'id': lead.id, 'username': lead.username}
            for lead in instance.strategy_leads.all()
        ]
        representation['communication_leads'] = [
            {'id': lead.id, 'username': lead.username}
            for lead in instance.communication_leads.all()
        ]
        return representation
    

class RoadmapSerializer(serializers.ModelSerializer):
    # strategies = serializers.SerializerMethodField()
    strategies = StrategySerializer(many=True, read_only=True)

    class Meta:
        model = Roadmap
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')

    def get_strategies(self, obj):
        strategies = obj.strategies.all()
        return StrategySerializer(strategies, many=True, context=self.context).data