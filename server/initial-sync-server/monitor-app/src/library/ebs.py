from loguru import logger


def create_and_attach_volume(ec2_client, az, instance_id, device, size_gb):
    # TODO: Validate device? An error occurred (InvalidParameterValue) when calling the AttachVolume operation:
    #       Invalid value '/dev/xvdf' for unixDevice. Attachment point /dev/xvdf is already in use

    try:
        response = ec2_client.create_volume(
            AvailabilityZone=az,
            Encrypted=False,
            Size=size_gb,
            VolumeType='gp2',    # standard'|'io1'|'gp2'|'sc1'|'st1'
            # TagSpecifications=[
            #     {
            #         'ResourceType': 'capacity-reservation'|'client-vpn-endpoint'|'customer-gateway'|'carrier-gateway'|'dedicated-host'|'dhcp-options'|'egress-only-internet-gateway'|'elastic-ip'|'elastic-gpu'|'export-image-task'|'export-instance-task'|'fleet'|'fpga-image'|'host-reservation'|'image'|'import-image-task'|'import-snapshot-task'|'instance'|'instance-event-window'|'internet-gateway'|'ipv4pool-ec2'|'ipv6pool-ec2'|'key-pair'|'launch-template'|'local-gateway'|'local-gateway-route-table'|'local-gateway-virtual-interface'|'local-gateway-virtual-interface-group'|'local-gateway-route-table-vpc-association'|'local-gateway-route-table-virtual-interface-group-association'|'natgateway'|'network-acl'|'network-interface'|'network-insights-analysis'|'network-insights-path'|'placement-group'|'prefix-list'|'replace-root-volume-task'|'reserved-instances'|'route-table'|'security-group'|'security-group-rule'|'snapshot'|'spot-fleet-request'|'spot-instances-request'|'subnet'|'traffic-mirror-filter'|'traffic-mirror-session'|'traffic-mirror-target'|'transit-gateway'|'transit-gateway-attachment'|'transit-gateway-connect-peer'|'transit-gateway-multicast-domain'|'transit-gateway-route-table'|'volume'|'vpc'|'vpc-endpoint'|'vpc-endpoint-service'|'vpc-peering-connection'|'vpn-connection'|'vpn-gateway'|'vpc-flow-log',
            #         'Tags': [
            #             {
            #                 'Key': 'string',
            #                 'Value': 'string'
            #             },
            #         ]
            #     },
            # ]
        )
        # logger.info(response)

        volume_id = None
        create_http_code = response['ResponseMetadata']['HTTPStatusCode']
        if create_http_code == 200:
            volume_id = response['VolumeId']
            logger.info(f'Requested create {volume_id}, size {size_gb}GiB...')
            logger.info(f'Waiting for volume to become available...')

            ec2_client.get_waiter('volume_available').wait(
                VolumeIds=[volume_id]
            )
            logger.info(f'Successfully created volume {volume_id}')
        else:
            logger.error(f"create_volume status was {create_http_code}")
            return False

    except Exception as e:
        logger.error(f"Failed to create the volume {e}")
        return False

    assert volume_id is not None, "volume_id is None"

    try:
        logger.info(f"Attaching volume {volume_id} to instance {instance_id}")
        response = ec2_client.attach_volume(
            Device=device,
            InstanceId=instance_id,
            VolumeId=volume_id
        )
        # logger.info(response)

        attach_http_code = response['ResponseMetadata']['HTTPStatusCode']
        if attach_http_code == 200:
            ec2_client.get_waiter('volume_in_use').wait(
                VolumeIds=[volume_id]
            )
            logger.info(f"Successfully attached volume {volume_id} to instance {instance_id}")
        else:
            logger.error(f"attach_volume status was {attach_http_code}")
            return False

    except Exception as e:
        logger.error(f"Failed to attach volume {volume_id} to {instance_id}: {e}")
        return False

    return True
