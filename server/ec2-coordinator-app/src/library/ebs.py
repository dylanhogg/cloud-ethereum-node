from loguru import logger


def find_volumes_by_name(ec2_resource, name):
    volumes = ec2_resource.volumes.filter(
        Filters=[{"Name": "tag:Name", "Values": [name]}]
    )
    return volumes


def create_and_attach_volume(ec2_client, az, attach_instance_id, device, size_gb, tags):
    # TODO: Validate device? An error occurred (InvalidParameterValue) when calling the AttachVolume operation:
    #       Invalid value "/dev/xvdf" for unixDevice. Attachment point /dev/xvdf is already in use

    # Nice ref: https://hands-on.cloud/working-with-ebs-volumes-in-python/

    try:
        response = ec2_client.create_volume(
            AvailabilityZone=az,
            Encrypted=False,
            Size=size_gb,
            VolumeType="gp2",
            TagSpecifications=[
                {
                    "ResourceType": "volume",
                    "Tags": tags
                },
            ]
        )

        create_http_code = response["ResponseMetadata"]["HTTPStatusCode"]
        if create_http_code == 200:
            volume_id = response["VolumeId"]
            logger.info(f"Requested create {volume_id}, size {size_gb}GiB...")
            logger.info(f"Waiting for volume to become available...")

            ec2_client.get_waiter("volume_available").wait(
                VolumeIds=[volume_id]
            )
            logger.info(f"Successfully created volume {volume_id}")
        else:
            logger.error(f"create_volume HTTPStatusCode was {create_http_code}, expected 200")
            return False, None

    except Exception as e:
        logger.error(f"Failed to create the volume {e}")
        return False, None

    assert volume_id is not None, "volume_id is None"

    try:
        logger.info(f"Attaching volume {volume_id} to instance {attach_instance_id}")
        response = ec2_client.attach_volume(
            Device=device,
            InstanceId=attach_instance_id,
            VolumeId=volume_id
        )
        # logger.info(response)

        attach_http_code = response["ResponseMetadata"]["HTTPStatusCode"]
        if attach_http_code == 200:
            ec2_client.get_waiter("volume_in_use").wait(
                VolumeIds=[volume_id]
            )
            logger.info(f"Successfully attached volume {volume_id} to instance {attach_instance_id}")
        else:
            logger.error(f"attach_volume HTTPStatusCode was {attach_http_code}, expected 200")
            return False, volume_id

    except Exception as e:
        logger.error(f"Failed to attach volume {volume_id} to {attach_instance_id}: {e}")
        return False, volume_id

    return True, volume_id
