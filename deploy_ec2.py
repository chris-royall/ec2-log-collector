import boto3
import uuid
import json
import time
import urllib.request

REGION = "eu-west-2"
BUCKET_NAME = f"ec2-log-collector-{uuid.uuid4()}"

s3 = boto3.client("s3", region_name=REGION)
ec2 = boto3.resource("ec2", region_name=REGION)
ec2_client = boto3.client("ec2", region_name=REGION)
iam = boto3.client("iam", region_name=REGION)

try:
    print("Getting current IP address...")
    # Get current public IP
    with urllib.request.urlopen("https://ipinfo.io/ip") as response:
        my_ip = response.read().decode().strip()
    print(f"✓ Current IP: {my_ip}")

    print("Getting default VPC...")
    # Get default VPC
    vpcs = ec2_client.describe_vpcs(Filters=[{"Name": "is-default", "Values": ["true"]}])
    vpc_id = vpcs["Vpcs"][0]["VpcId"]
    print(f"✓ Default VPC: {vpc_id}")

    print("Creating security group...")
    # Create security group
    sg_response = ec2_client.create_security_group(
        GroupName=f"ec2-log-collector-sg-{uuid.uuid4()}",
        Description="SSH access for EC2 log collector",
        VpcId=vpc_id
    )
    security_group_id = sg_response["GroupId"]
    print(f"✓ Security group created: {security_group_id}")

    print("Adding SSH access rule...")
    # Add SSH rule for current IP
    ec2_client.authorize_security_group_ingress(
        GroupId=security_group_id,
        IpPermissions=[
            {
                "IpProtocol": "tcp",
                "FromPort": 22,
                "ToPort": 22,
                "IpRanges": [{"CidrIp": f"{my_ip}/32"}]
            }
        ]
    )
    print(f"✓ SSH access added")

    print("Creating IAM role...")
    # Create IAM role for EC2
    role_document = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"Service": "ec2.amazonaws.com"},
                "Action": "sts:AssumeRole"
            }
        ]
    }

    policy_document = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": ["s3:PutObject"],
                "Resource": f"arn:aws:s3:::{BUCKET_NAME}/*"
            }
        ]
    }

    iam.create_role(
        RoleName="ec2-log-collector-role",
        AssumeRolePolicyDocument=json.dumps(role_document)
    )
    print("✓ IAM role created")

    print("Attaching policy to role...")
    iam.put_role_policy(
        RoleName="ec2-log-collector-role",
        PolicyName="S3LogUploadPolicy",
        PolicyDocument=json.dumps(policy_document)
    )
    print("✓ Policy attached")

    print("Creating instance profile...")
    iam.create_instance_profile(InstanceProfileName="EC2LogCollectorProfile")
    print("✓ Instance profile created")

    print("Adding role to instance profile...")
    iam.add_role_to_instance_profile(
        InstanceProfileName="EC2LogCollectorProfile",
        RoleName="ec2-log-collector-role"
    )
    print("✓ Role added to instance profile")

    # Wait for IAM resources to propagate
    print("Waiting for IAM resources to propagate...")
    time.sleep(10)
    print("✓ IAM propagation complete")

    print("Creating S3 bucket...")
    # Create S3 bucket
    s3.create_bucket(
        Bucket=BUCKET_NAME,
        CreateBucketConfiguration={"LocationConstraint": REGION}
    )
    print(f"✓ S3 bucket created: {BUCKET_NAME}")

    print("Preparing user data...")
    # Read user data
    with open("user_data.sh") as f:
        user_data = f.read().replace("REPLACE", BUCKET_NAME)
    print("✓ User data prepared")

    print("Launching EC2 instance...")
    # Launch EC2
    instance = ec2.create_instances(
        ImageId="ami-0a0ff88d0f3f85a14",
        InstanceType="t3.micro",
        KeyName="ec2-log-collector",
        SecurityGroupIds=[security_group_id],
        IamInstanceProfile={"Name": "EC2LogCollectorProfile"},
        MinCount=1,
        MaxCount=1,
        UserData=user_data
    )
    print(f"✓ EC2 instance launched: {instance[0].id}")

    print("\n=== DEPLOYMENT COMPLETE ===")
    print("S3 bucket:", BUCKET_NAME)
    print("EC2 instance ID:", instance[0].id)

except Exception as e:
    print(f"Error: {e}")
