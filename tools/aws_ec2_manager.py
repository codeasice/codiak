import streamlit as st
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
import pandas as pd
from datetime import datetime
import time

def get_ec2_client():
    """Get EC2 client with error handling for credentials."""
    try:
        # Use the 'codiak' profile specifically
        session = boto3.Session(profile_name='codiak')
        return session.client('ec2')
    except NoCredentialsError:
        st.error("AWS credentials not found for 'codiak' profile. Please configure your AWS credentials using 'aws configure --profile codiak'.")
        return None
    except Exception as e:
        st.error(f"Error creating EC2 client with 'codiak' profile: {str(e)}")
        return None

def list_instances(ec2_client):
    """List all EC2 instances with their status."""
    try:
        response = ec2_client.describe_instances()
        instances = []

        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                instances.append({
                    'Instance ID': instance['InstanceId'],
                    'Name': next((tag['Value'] for tag in instance.get('Tags', []) if tag['Key'] == 'Name'), 'N/A'),
                    'State': instance['State']['Name'],
                    'Instance Type': instance['InstanceType'],
                    'Launch Time': instance['LaunchTime'].strftime('%Y-%m-%d %H:%M:%S'),
                    'Public IP': instance.get('PublicIpAddress', 'N/A'),
                    'Private IP': instance.get('PrivateIpAddress', 'N/A'),
                    'Zone': instance['Placement']['AvailabilityZone']
                })

        return instances
    except ClientError as e:
        st.error(f"Error listing instances: {str(e)}")
        return []
    except Exception as e:
        st.error(f"Unexpected error: {str(e)}")
        return []

def start_instance(ec2_client, instance_id):
    """Start an EC2 instance."""
    try:
        response = ec2_client.start_instances(InstanceIds=[instance_id])
        return True, f"Starting instance {instance_id}..."
    except ClientError as e:
        return False, f"Error starting instance {instance_id}: {str(e)}"
    except Exception as e:
        return False, f"Unexpected error starting instance {instance_id}: {str(e)}"

def stop_instance(ec2_client, instance_id):
    """Stop an EC2 instance."""
    try:
        response = ec2_client.stop_instances(InstanceIds=[instance_id])
        return True, f"Stopping instance {instance_id}..."
    except ClientError as e:
        return False, f"Error stopping instance {instance_id}: {str(e)}"
    except Exception as e:
        return False, f"Unexpected error stopping instance {instance_id}: {str(e)}"

def render():
    st.write("Manage your AWS EC2 instances. List instances and toggle their power state.")

    # Initialize session state for messages
    if 'ec2_message' not in st.session_state:
        st.session_state.ec2_message = None
    if 'ec2_message_type' not in st.session_state:
        st.session_state.ec2_message_type = None

    # Get EC2 client
    ec2_client = get_ec2_client()
    if not ec2_client:
        st.stop()

    # Refresh button
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()

    with col2:
        st.write("Click refresh to update the instance list")

    # Get instances
    instances = list_instances(ec2_client)

    if not instances:
        st.info("No EC2 instances found or no access to EC2 instances.")
        return

    # Convert to DataFrame for better display
    df = pd.DataFrame(instances)

    # Display instances in a table with action buttons
    st.subheader("EC2 Instances")

    # Create a more interactive display
    for idx, instance in enumerate(instances):
        with st.container():
            col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 2])

            with col1:
                st.write(f"**{instance['Name']}**")
                st.caption(f"ID: {instance['Instance ID']}")
                st.caption(f"Type: {instance['Instance Type']}")

            with col2:
                # Color code the state
                state = instance['State']
                if state == 'running':
                    st.success("🟢 Running")
                elif state == 'stopped':
                    st.error("🔴 Stopped")
                elif state == 'pending':
                    st.warning("🟡 Pending")
                elif state == 'stopping':
                    st.warning("🟡 Stopping")
                elif state == 'starting':
                    st.warning("🟡 Starting")
                else:
                    st.info(f"⚪ {state}")

            with col3:
                st.write(f"**Zone:** {instance['Zone']}")

            with col4:
                if instance['Public IP'] != 'N/A':
                    st.write(f"**Public IP:** {instance['Public IP']}")
                else:
                    st.write("**Public IP:** N/A")

            with col5:
                # Action buttons
                if state == 'running':
                    if st.button(f"🛑 Stop", key=f"stop_{instance['Instance ID']}", use_container_width=True):
                        success, message = stop_instance(ec2_client, instance['Instance ID'])
                        st.session_state.ec2_message = message
                        st.session_state.ec2_message_type = 'success' if success else 'error'
                        st.rerun()
                elif state == 'stopped':
                    if st.button(f"▶️ Start", key=f"start_{instance['Instance ID']}", use_container_width=True):
                        success, message = start_instance(ec2_client, instance['Instance ID'])
                        st.session_state.ec2_message = message
                        st.session_state.ec2_message_type = 'success' if success else 'error'
                        st.rerun()
                else:
                    st.write("⏳ Processing...")

            st.divider()

    # Show messages
    if st.session_state.ec2_message:
        if st.session_state.ec2_message_type == 'success':
            st.success(st.session_state.ec2_message)
        else:
            st.error(st.session_state.ec2_message)

        # Clear message after showing
        if st.button("Clear Message"):
            st.session_state.ec2_message = None
            st.session_state.ec2_message_type = None
            st.rerun()

    # Summary statistics
    st.subheader("Summary")
    running_count = len([i for i in instances if i['State'] == 'running'])
    stopped_count = len([i for i in instances if i['State'] == 'stopped'])
    other_count = len(instances) - running_count - stopped_count

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Instances", len(instances))
    with col2:
        st.metric("Running", running_count)
    with col3:
        st.metric("Stopped", stopped_count)