from loguru import logger
from pprint import pprint


def find_ec2_instance(ec2_client, ec2_name):
    response = ec2_client.describe_instances(Filters=[{'Name': 'tag:Name', 'Values': [ec2_name]}])
    # pprint(response)
    assert len(response['Reservations']), "Expected 'Reservations' response to only have 1 value"

    try:
        instance_id = response['Reservations'][0]['Instances'][0]['InstanceId']
    except Exception as e:
        logger.error(f"InstanceId not found in response: {response}")
        return None

    logger.info(f"Found InstanceId: {instance_id}")
    assert instance_id is not None
    assert instance_id.startswith("i-")

    return instance_id
