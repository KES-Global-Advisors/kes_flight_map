from rest_framework import serializers
from .models import (
    Flightmap, Strategy, StrategicGoal, Program,
    Workstream, Milestone, Activity,
    MilestoneContributor, ActivityContributor,
    NodePosition, FlightmapDraft,
)
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

User = get_user_model()
    
class StrategicGoalSerializer(serializers.ModelSerializer):

    class Meta:
        model = StrategicGoal
        fields = ['id', 'category', 'goal_text', 'strategy']

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        # Represent the strategy as an object with id and name
        rep['strategy'] = {
            'id': instance.strategy.id,
            'name': instance.strategy.name
        }
        return rep

class ContributorSerializer(serializers.ModelSerializer):
    # user = serializers.PrimaryKeyRelatedField(read_only=True)
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        fields = ['user', 'username', 'email']

class MilestoneContributorSerializer(ContributorSerializer):
    class Meta(ContributorSerializer.Meta):
        model = MilestoneContributor
        fields = ['milestone', 'user']
        extra_kwargs = {
            'user': {'read_only': True},
        }

    def create(self, validated_data):
        request = self.context.get("request")
        if request and request.user and request.user.is_authenticated:
            validated_data["user"] = request.user
        milestone = validated_data.get("milestone")
        user = validated_data.get("user")
        contributor, _ = MilestoneContributor.objects.get_or_create(
            milestone=milestone,
            user=user
        )
        return contributor

class ActivityContributorSerializer(ContributorSerializer):
    class Meta(ContributorSerializer.Meta):
        model = ActivityContributor
        fields = ['activity', 'user']
        extra_kwargs = {
            'user': {'read_only': True},
        }

    def create(self, validated_data):
        request = self.context.get("request")
        if request and request.user and request.user.is_authenticated:
            validated_data["user"] = request.user
        activity = validated_data.get("activity")
        user = validated_data.get("user")
        contributor, _ = ActivityContributor.objects.get_or_create(
            activity=activity,
            user=user
        )
        return contributor

class ActivitySerializer(serializers.ModelSerializer):
    status = serializers.ChoiceField(choices=Activity.STATUS_CHOICES)
    contributors = ActivityContributorSerializer(many=True, read_only=True)
    strategic_goals = serializers.SerializerMethodField()
    delay_days = serializers.SerializerMethodField()
    actual_duration = serializers.SerializerMethodField()
    is_overdue = serializers.SerializerMethodField()

        # New fields to return additional links
    supported_milestones = serializers.PrimaryKeyRelatedField(
        queryset=Milestone.objects.all(),
        many=True,
        required=False
    )
    additional_milestones = serializers.PrimaryKeyRelatedField(
        queryset=Milestone.objects.all(),
        many=True,
        required=False
    )

    class Meta:
        model = Activity
        fields = '__all__'
        extra_kwargs = {
            'completed_date': {'read_only': True},
            'actual_start_date': {'required': False}
        }

    def get_delay_days(self, obj):
        if obj.completed_date and obj.completed_date > obj.target_end_date:
            return (obj.completed_date - obj.target_end_date).days
        return 0

    def get_actual_duration(self, obj):
        if obj.actual_start_date and obj.completed_date:
            return (obj.completed_date - obj.actual_start_date).days
        return None

    def get_is_overdue(self, obj):
        if obj.status != 'completed' and timezone.now().date() > obj.target_end_date:
            return True
        return False

    def get_strategic_goals(self, obj):
        if obj.milestone:
            return StrategicGoalSerializer(
                obj.milestone.strategic_goals.all(),
                many=True,
                context=self.context
            ).data
        return []

    def validate(self, data):
        if data.get('status') == 'completed' and not data.get('completed_date'):
            data['completed_date'] = timezone.now().date()
        
        if data.get('actual_start_date') and data.get('target_start_date'):
            if data['actual_start_date'] < data['target_start_date']:
                raise serializers.ValidationError(
                    "Actual start date cannot precede target start date"
                )

        if data.get('completed_date'):
            # When updating, if target_start_date isn't provided in data, use instance's value.
            target_start = data.get('target_start_date')
            if not target_start and self.instance:
                target_start = self.instance.target_start_date
            if target_start and data['completed_date'] < target_start:
                raise serializers.ValidationError(
                    "Completion date cannot be before target start date"
                )

        return data

    def create(self, validated_data):
        # If this is a standalone activity (no workstream and no milestone),
        # mark it by setting updated_by to the current user.
        request = self.context.get("request")
        if request and request.user and request.user.is_authenticated:
            if validated_data.get('workstream') is None and validated_data.get('milestone') is None:
                validated_data['updated_by'] = request.user
        return super().create(validated_data)

    
    def update(self, instance, validated_data):
        # Always update the updated_by field to the current user from the request context
        request = self.context.get('request')
        if request and request.user and request.user.is_authenticated:
            instance.updated_by = request.user
        return super().update(instance, validated_data)

class MilestoneSerializer(serializers.ModelSerializer):
    status = serializers.ChoiceField(choices=Milestone.STATUS_CHOICES)
    activities = ActivitySerializer(many=True, read_only=True)
    contributors = MilestoneContributorSerializer(many=True, read_only=True)
    strategic_goals = StrategicGoalSerializer(many=True, read_only=True)
    strategic_goal_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=StrategicGoal.objects.all(),
        source='strategic_goals',
        write_only=True,
        required=False
    )
    current_progress = serializers.IntegerField(read_only=True)
    timeframe_category = serializers.CharField(read_only=True)

    class Meta:
        model = Milestone
        fields = '__all__'
        extra_kwargs = {
            'completed_date': {'read_only': True},
            'workstream': {'required': False, 'allow_null': True},
            'parent_milestone': {'required': False, 'allow_null': True},
        }

    def validate(self, data):
        if data.get('status') == 'completed' and not data.get('completed_date'):
            data['completed_date'] = timezone.now().date()
        return data

    def create(self, validated_data):
        request = self.context.get("request")
        if request and request.user and request.user.is_authenticated:
            # If no workstream is provided, assume the milestone is standalone.
            if validated_data.get('workstream') is None:
                validated_data['updated_by'] = request.user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        request = self.context.get('request')
        if request and request.user and request.user.is_authenticated:
            instance.updated_by = request.user
        return super().update(instance, validated_data)

class WorkstreamSerializer(serializers.ModelSerializer):
    milestones = serializers.SerializerMethodField()
    activities = serializers.SerializerMethodField()
    workstream_leads = serializers.SlugRelatedField(
         many=True, read_only=True, slug_field='username'
    )
    team_members = serializers.SlugRelatedField(
         many=True, read_only=True, slug_field='username'
    )
    progress_summary = serializers.SerializerMethodField()

    class Meta:
         model = Workstream
         fields = '__all__'


    def get_milestones(self, obj):
        # Fetch all related milestones, then collapse duplicates by ID
        unique = {m.id: m for m in obj.milestones.all()}.values()
        return MilestoneSerializer(unique, many=True, context=self.context).data

    def get_activities(self, obj):
        qs = obj.activities.filter(milestone__isnull=True)
        unique = {a.id: a for a in qs}.values()
        return ActivitySerializer(unique, many=True, context=self.context).data
    
    def get_contributors(self, obj):
        contributors = obj.get_contributors().distinct()
        return [{
            'id': user.id,
            'username': user.username
        } for user in contributors]

    def get_progress_summary(self, obj):
        return {
            'total_milestones': obj.milestones.count(),
            'completed_milestones': obj.milestones.filter(status='completed').count(),
            'in_progress_milestones': obj.milestones.filter(status='in_progress').count()
        }

class ProgramSerializer(serializers.ModelSerializer):
    workstreams = WorkstreamSerializer(many=True, read_only=True)
    progress = serializers.SerializerMethodField()
    executive_sponsors = serializers.SlugRelatedField(
         many=True, read_only=True, slug_field='username'
    )
    program_leads = serializers.SlugRelatedField(
         many=True, read_only=True, slug_field='username'
    )
    workforce_sponsors = serializers.SlugRelatedField(
         many=True, read_only=True, slug_field='username'
    )

    class Meta:
         model = Program
         fields = '__all__'

    def get_progress(self, obj):
        milestones = Milestone.objects.filter(workstream__program=obj)
        total = milestones.count()
        completed = milestones.filter(status='completed').count()
        if total == 0:
            return {'percentage': 0, 'total': 0, 'completed': 0}
        return {
            'total': total,
            'completed': completed,
            'percentage': int((completed / total) * 100) if total > 0 else 0
        }

class StrategySerializer(serializers.ModelSerializer):
    programs = ProgramSerializer(many=True, read_only=True)
    goal_summary = serializers.SerializerMethodField()
    executive_sponsors = serializers.SlugRelatedField(
         many=True, read_only=True, slug_field='username'
    )
    strategy_leads = serializers.SlugRelatedField(
         many=True, read_only=True, slug_field='username'
    )
    communication_leads = serializers.SlugRelatedField(
         many=True, read_only=True, slug_field='username'
    )

    class Meta:
        model = Strategy
        fields = '__all__'

    def get_goal_summary(self, obj):
        return {
            'business_goals': list(obj.goals.filter(category='business').values_list('goal_text', flat=True)),
            'organizational_goals': list(obj.goals.filter(category='organizational').values_list('goal_text', flat=True))
        }

class FlightmapSerializer(serializers.ModelSerializer):
    strategies = StrategySerializer(many=True, read_only=True)
    milestone_summary = serializers.SerializerMethodField()

    class Meta:
        model = Flightmap
        fields = '__all__'

    def get_milestone_summary(self, obj):
        milestones = Milestone.objects.filter(workstream__program__strategy__flightmap=obj)
        return {
            'total': milestones.count(),
            'completed': milestones.filter(status='completed').count(),
            'in_progress': milestones.filter(status='in_progress').count(),
            'overdue': milestones.filter(deadline__lt=timezone.now().date(), status__in=['not_started', 'in_progress']).count()
        }
    
class FlightmapDraftSerializer(serializers.ModelSerializer):
    class Meta:
        model = FlightmapDraft
        fields = ['id', 'name', 'current_step', 'form_data', 'completed_steps', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

# Dashboard-specific serializers
class DashboardMilestoneSerializer(serializers.ModelSerializer):
    program = serializers.CharField(source='workstream.program.name', read_only=True)
    strategy = serializers.CharField(source='workstream.program.strategy.name', read_only=True)
    timeframe_category = serializers.CharField()
    contributors = serializers.SerializerMethodField()

    class Meta:
        model = Milestone
        fields = [
            'id', 'name', 'status', 'deadline', 'current_progress',
            'program', 'strategy', 'timeframe_category', 'contributors'
        ]

    def get_contributors(self, obj):
        return obj.contributors.values('user__username')

class EmployeeContributionSerializer(serializers.ModelSerializer):
    milestones = serializers.SerializerMethodField()
    activities = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'milestones', 'activities']

    def get_milestones(self, obj):
        return {
            'completed': obj.milestonecontributor_set.filter(milestone__status='completed').count(),
            'in_progress': obj.milestonecontributor_set.filter(milestone__status='in_progress').count()
        }

    def get_activities(self, obj):
        return {
            'completed': obj.activitycontributor_set.filter(activity__status='completed').count(),
            'in_progress': obj.activitycontributor_set.filter(activity__status='in_progress').count()
        }

# Status update serializers
class MilestoneStatusSerializer(serializers.ModelSerializer):
    
    def validate(self, data):
        if data.get('status') == 'completed' and not data.get('completed_date'):
            data['completed_date'] = timezone.now().date()
        return data

    class Meta:
        model = Milestone
        fields = ['status', 'completed_date']
        extra_kwargs = {
            'completed_date': {'required': False}
        }

class ActivityStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Activity
        fields = ['status', 'completed_date', 'actual_start_date']
        extra_kwargs = {
            'completed_date': {'required': False},
            'actual_start_date': {'required': False}
        }

    def validate(self, data):
        if data.get('status') == 'in_progress' and not data.get('actual_start_date'):
            data['actual_start_date'] = timezone.now().date()
        return data

class NodePositionSerializer(serializers.ModelSerializer):
    class Meta:
        model = NodePosition
        fields = ['id', 'flightmap', 'node_type', 'node_id', 'rel_y', 'updated_at', 
          'is_duplicate', 'duplicate_key', 'original_node_id']