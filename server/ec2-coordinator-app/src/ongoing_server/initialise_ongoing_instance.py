from loguru import logger
from library import ec2, ssh, ebs


def get_tag_by_key(tags, key):
    matching = [x for x in tags if x["Key"] == key]
    return matching[0]


def get_ebs_volume(ec2_resource):
    volume_name = "ethereum-initial-sync-server-ebs-export"
    volumes = list(ebs.find_volumes_by_name(ec2_resource, volume_name))
    if len(volumes) == 0:
        raise RuntimeError(f"No volumes matching name {volume_name}")

    eligible_volumes = [x for x in volumes if x.state == "available"]
    logger.info(f"Number of eligible_volumes is {len(eligible_volumes)}")
    if len(eligible_volumes) == 0:
        raise RuntimeError(f"No *eligible* volumes matching name {volume_name}")

    # TODO: filter by meta_geth_status, meta_debug_run also

    # TODO: review approach of getting max meta_sync_date if >1 eligible_volumes

    max_sync_date = max([get_tag_by_key(x.tags, "meta_sync_date")["Value"] for x in eligible_volumes])
    logger.info(f"max_sync_date within eligible_volumes is {max_sync_date}")

    max_sync_date_volume = [x for x in eligible_volumes if get_tag_by_key(x.tags, "meta_sync_date")["Value"] == max_sync_date][0]
    return max_sync_date_volume


def start(ec2_client, ec2_resource, az_name, data_dir, debug_run):
    ebs_volume = get_ebs_volume(ec2_resource)
    logger.info(f"ebs_volume id: {ebs_volume.id}")
    logger.info(f"ebs_volume tags: {ebs_volume.tags}")

