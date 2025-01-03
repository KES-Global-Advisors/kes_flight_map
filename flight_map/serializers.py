from rest_framework import serializers
from .models import Program, Workstream, Milestone, Task
from django.contrib.auth import get_user_model

# Dynamically retrieve the user model based on AUTH_USER_MODEL setting
User = get_user_model()
class ProgramSerializer(serializers.ModelSerializer):
    """
    This field represents the many-to-many relationship between Program and User.
    StringRelatedField returns the string representation of the related objects (usernames in this case).
    """
    stakeholders = serializers.PrimaryKeyRelatedField(many=True, queryset=User.objects.all())

    class Meta:
        model = Program
        fields = '__all__'


    def to_representation(self, instance):
        """
        Overrides the representation to include detailed stakeholder information.
        """
        representation = super().to_representation(instance)
        representation['stakeholders'] = [
            {"id": user.id, "username": user.username} for user in instance.stakeholders.all()
        ]
        return representation

class WorkstreamSerializer(serializers.ModelSerializer):
    """
    Handles program as a writable field for creation while maintaining a nested
    representation for read operations.
    """
    program = serializers.PrimaryKeyRelatedField(queryset=Program.objects.all())

    class Meta:
        model = Workstream
        fields = '__all__'


    def to_representation(self, instance):
        """
        Overrides the representation to include detailed program information.
        """
        representation = super().to_representation(instance)
        representation['program'] = ProgramSerializer(instance.program).data
        return representation

class MilestoneSerializer(serializers.ModelSerializer):
    """
    Handles the many-to-many relationship between Milestone objects.
    Includes primary keys for dependencies during creation and nested data during read operations.
    """
    dependencies = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Milestone.objects.all()
    )

    class Meta:
        model = Milestone
        fields = '__all__'

    def to_representation(self, instance):
        """
        Overrides the representation to include nested milestone dependency details.
        """
        representation = super().to_representation(instance)
        representation['dependencies'] = MilestoneSerializer(instance.dependencies.all(), many=True).data
        return representation


class TaskSerializer(serializers.ModelSerializer):
    """
    Handles milestone as a writable field for creation while maintaining a nested
    representation for read operations.
    """
    milestone = serializers.PrimaryKeyRelatedField(queryset=Milestone.objects.all())
    key_stakeholders = serializers.PrimaryKeyRelatedField(many=True, queryset=User.objects.all())
    class Meta:
        model = Task
        fields = '__all__'


    def to_representation(self, instance):
        """
        Overrides the representation to include detailed milestone information.
        """
        representation = super().to_representation(instance)
        representation['milestone'] = MilestoneSerializer(instance.milestone).data
        representation['key_stakeholders'] = [
            {"id": user.id, "username": user.username} for user in instance.key_stakeholders.all()
        ]
        return representation
