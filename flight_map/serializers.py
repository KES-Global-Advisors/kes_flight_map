from rest_framework import serializers
from .models import Program, Workstream, Milestone, Task

class ProgramSerializer(serializers.ModelSerializer):
    """
    * This field represents the many-to-many relationship between Program and User.
    * StringRelatedField returns the string representation of the related objects (usernames in this case).
    """
    stakeholders = serializers.StringRelatedField(many=True)

    class Meta:
        model = Program
        fields = '__all__'

class WorkstreamSerializer(serializers.ModelSerializer):
    """
    * This nested serializer provides a serialized representation of the Program associated with each Workstream.
    * read_only=True ensures that the program data is included in the output but cannot be modified through the serializer.
    """
    Program = ProgramSerializer(read_only=True)

    class Meta:
        model = Workstream
        fields = '__all__'

class MilestoneSerializer(serializers.ModelSerializer):
    """
    * This handles the many-to-many relationship between Milestone objects.
    * It only includes the primary keys of the dependent milestones, making the output more concise.
    """
    dependencies = serializers.PrimaryKeyRelatedField(many=True, read_only=True) 

    class Meta:
        model = Milestone
        fields = '__all__'

class TaskSerializer(serializers.ModelSerializer):
    """
    *  Similar to WorkstreamSerializer, this includes a nested serializer for the Milestone associated with each Task.
    """
    milestone = MilestoneSerializer(read_only=True) 

    class Meta:
        model = Task
        fields = '__all__'
