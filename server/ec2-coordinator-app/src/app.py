import os
from library import ec2
from initial_server import coordinator as initial_coordinator


def main():
    region_name = os.environ.get("AWS_REGION")
    az_name = os.environ.get("AWS_AZ")
    assert region_name is not None, "AWS_REGION environ is not set"
    assert az_name is not None, "AWS_AZ environ is not set"

    ec2_client = ec2.get_client(region_name)
    data_dir = "/mnt/sync/ethereum"
    debug_run = True
    terminate_instance = True
    initial_coordinator.start(ec2_client, az_name, data_dir, debug_run, terminate_instance)


if __name__ == "__main__":
    main()
