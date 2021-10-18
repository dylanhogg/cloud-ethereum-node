from loguru import logger


def create_and_attach_volume(ec2_client, az, dry_run, device, instance_id, size_gb):
    # TODO: Validate device? An error occurred (InvalidParameterValue) when calling the AttachVolume operation:
    #       Invalid value '/dev/xvdf' for unixDevice. Attachment point /dev/xvdf is already in use

    try:
        response = ec2_client.create_volume(
            AvailabilityZone=az,
            Encrypted=False,
            Size=size_gb,
            VolumeType='gp2',    # standard'|'io1'|'gp2'|'sc1'|'st1',
            DryRun=dry_run
        )
        # plogger.info(response)

        volume_id = None
        create_http_code = response['ResponseMetadata']['HTTPStatusCode']
        if create_http_code == 200:
            volume_id = response['VolumeId']
            logger.info(f'volume_id: {volume_id}')
            logger.info(f'Waiting for volumne to become available...')

            ec2_client.get_waiter('volume_available').wait(
                VolumeIds=[volume_id],
                DryRun=dry_run
            )
            logger.info(f'Success!! volume: {volume_id} created...')
        else:
            logger.error(f"create_http_code was not 200 but was: {create_http_code}")

    except Exception as e:
        logger.error('Failed to create the volume...')
        logger.info(type(e), ':', e)
        return False

    if volume_id is not None:
        try:
            logger.info('Attaching volume:', volume_id, 'to:', instance_id)
            response = ec2_client.attach_volume(
                Device=device,
                InstanceId=instance_id,
                VolumeId=volume_id,
                DryRun=dry_run
            )
            # plogger.info(response)

            attach_http_code = response['ResponseMetadata']['HTTPStatusCode']
            if attach_http_code == 200:
                ec2_client.get_waiter('volume_in_use').wait(
                    VolumeIds=[volume_id],
                    DryRun=False
                )
                logger.info('Success!! volume:', volume_id, 'is attached to instance:', instance_id)
            else:
                logger.error(f"attach_http_code was not 200 but was: {attach_http_code}")

        except Exception as e:
            logger.error('Error - Failed to attach volume:', volume_id, 'to the instance:', instance_id)
            logger.info(type(e), ':', e)
            return False

    return True
