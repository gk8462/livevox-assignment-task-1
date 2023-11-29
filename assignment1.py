import os
import sys
import boto3
from datetime import datetime, timezone

# AWS credentials and region
aws_access_key_id=os.environ['aws_access_key_id']
aws_secret_access_key=os.environ['aws_secret_access_key']
region_name = 'ap-south-1'

# AutoScalingGroup name
asg_name = 'lv-test-cpu'

# Initialize AWS clients
autoscaling_client = boto3.client('autoscaling', aws_access_key_id=aws_access_key_id,
                                  aws_secret_access_key=aws_secret_access_key, region_name=region_name)
ec2_client = boto3.client('ec2', aws_access_key_id=aws_access_key_id,
                          aws_secret_access_key=aws_secret_access_key, region_name=region_name)


def test_case_a():
    response = autoscaling_client.describe_auto_scaling_groups(AutoScalingGroupNames=[asg_name])
    asg_details = response['AutoScalingGroups'][0]

    # Test Case 1
    if asg_details['DesiredCapacity'] == len(asg_details['Instances']):
        print("Test Case 1 Passed: Desired Capacity matches the number of running instances.")
    else:
        print("Test Case 1 Failed: Desired Capacity does not match the number of running instances.")

    # Test Case 2
    instances = asg_details['Instances']
    availability_zones = set(instance['AvailabilityZone'] for instance in instances)

    if len(availability_zones) == len(instances):
        print("Test Case 2 Passed: Instances are evenly distributed across availability zones.")
    else:
        print("Test Case 2 Failed: Instances are not distributed across availability zones.")

    # Test Case 3
    security_group = instances[0]['SecurityGroups'][0]['GroupId']
    image_id = instances[0]['ImageId']
    vpc_id = instances[0]['VpcId']

    for instance in instances:
        if instance['SecurityGroups'][0]['GroupId'] != security_group or \
                instance['ImageId'] != image_id or \
                instance['VpcId'] != vpc_id:
            print("Test Case 3 Failed: Security Group, Image ID, or VPC ID mismatch found.")
            return

    print("Test Case 3 Passed: Security Group, Image ID, and VPC ID are consistent across instances.")

    # Test Case 4
    find_longest_running_instance(instances)


def test_case_b():
    response = autoscaling_client.describe_scheduled_actions(AutoScalingGroupName=asg_name)

    # Test Case 1
    if response['ScheduledUpdateGroupActions']:
        next_action = min(response['ScheduledUpdateGroupActions'], key=lambda x: x['StartTime'])
        current_time = datetime.now(timezone.utc)
        elapsed_time = next_action['StartTime'] - current_time
        print(f"Test Case 1 Passed: Time elapsed for the next scheduled action: {elapsed_time}")
    else:
        print("Test Case 1 Failed: No scheduled actions found.")

    # Test Case 2
    launch_terminate_stats = get_launch_terminate_stats(asg_name)
    print(f"Test Case 2: Total instances launched today: {launch_terminate_stats['launched']}, "
          f"Total instances terminated today: {launch_terminate_stats['terminated']}")


def find_longest_running_instance(instances):
    longest_running_instance = max(instances, key=lambda x: x['LaunchTime'])
    launch_time = longest_running_instance['LaunchTime']
    uptime = datetime.now(timezone.utc) - launch_time
    print(f"Test Case 4 Passed: The longest running instance has been up for: {uptime}")


def get_launch_terminate_stats(asg_name):
    response = autoscaling_client.describe_scaling_activities(AutoScalingGroupName=asg_name)
    today = datetime.now().date()

    launch_stats = {'launched': 0, 'terminated': 0}

    for activity in response['Activities']:
        activity_date = activity['StartTime'].date()

        if activity_date == today:
            if activity['Description'].startswith('Launching a new EC2 instance'):
                launch_stats['launched'] += 1
            elif activity['Description'].startswith('Terminating EC2 instance'):
                launch_stats['terminated'] += 1

    return launch_stats


# Main script
test_case_a()
test_case_b()