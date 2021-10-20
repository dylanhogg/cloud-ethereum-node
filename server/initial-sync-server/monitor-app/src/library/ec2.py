from loguru import logger
from pprint import pprint


def _get_attribute(instance, key):
    try:
        return instance[key]
    except KeyError as e:
        error = f"{key} not found in response: {instance}"
        logger.error(error)
        raise RuntimeError(error)


def find_ec2_instance(ec2_client, tag_name):
    ec2_filters = [{'Name': 'tag:Name', 'Values': [tag_name]}, {'Name': 'instance-state-name', 'Values': ['running']}]
    response = ec2_client.describe_instances(Filters=ec2_filters)
    # pprint(response)

    reservation_count = len(response['Reservations'])
    if reservation_count == 0:
        logger.warning(f"No matching instances found with tag:Name '{tag_name}'")
        return False, None, None, None

    if reservation_count != 1:
        error = f"Expected 'Reservations' response to only have 1 value, but was {reservation_count}"
        logger.error(error)
        raise RuntimeError(error)

    if len(response['Reservations'][0]['Instances']) != 1:
        error = f"Expected single matching instance with tag:Name '{tag_name}'"
        logger.error(error)
        raise RuntimeError(error)

    try:
        instance = response['Reservations'][0]['Instances'][0]
    except KeyError as e:
        error = f"Instance not found in response: {response}"
        logger.error(error)
        raise RuntimeError(error)

    # TODO: dataclass this
    instance_id = _get_attribute(instance, "InstanceId")
    instance_ip = _get_attribute(instance, "PublicIpAddress")
    instance_dns = _get_attribute(instance, "PublicDnsName")
    instance_type = _get_attribute(instance, "InstanceType")

    assert instance_id is not None
    assert instance_id.startswith("i-")
    assert instance_ip is not None
    assert len(instance_ip) > 6
    assert instance_dns is not None
    assert instance_dns.startswith("ec2-")
    assert instance_type is not None
    assert len(instance_type) > 0

    return True, instance_id, instance_ip, instance_dns, instance_type
