import boto3

from typing import List


class AvailabilityZoneFactory:
    def __init__(self, region: str, expected_az_count: int):
        self.region = region
        self.expected_az_count = expected_az_count

    def create(self) -> List[str]:
        ec2 = boto3.client('ec2')

        # Retrieves all regions/endpoints that work with EC2
        zones = ec2.describe_availability_zones()['AvailabilityZones']
        zones = [zone['ZoneName'] for zone in zones if zone['RegionName'] == self.region]

        # Ensure consistency
        zones = sorted(zones)

        # Ensure that the amount of availability zones does not change (because of a global disaster for e.g.)
        # Otherwise manual actions will be required
        assert len(zones) == self.expected_az_count

        return zones
