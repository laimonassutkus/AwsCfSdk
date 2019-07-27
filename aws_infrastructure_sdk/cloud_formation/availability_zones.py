import boto3

from typing import List, Optional


class AvailabilityZones:
    """
    Class that shows current availability zones.
    More on availability zones:
    https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-regions-availability-zones.html
    """
    def __init__(self, region: str, expected_az_count: Optional[int] = None):
        """
        Constructor.

        :param region: Name of the AWS Region.
        :param expected_az_count: Expected availability zones count.
        """
        self.region = region
        self.expected_az_count = expected_az_count

    def get(self) -> List[str]:
        """
        Returns a list of availability zones.

        :return: List of availability zones
        """
        ec2 = boto3.client('ec2')

        # Retrieves all regions/endpoints that work with EC2
        zones = ec2.describe_availability_zones()['AvailabilityZones']
        zones = [zone['ZoneName'] for zone in zones if zone['RegionName'] == self.region]

        # Ensure consistency
        zones = sorted(zones)

        if self.expected_az_count is not None:
            # Ensure that the amount of availability zones does not change (because of a global disaster for e.g.)
            # Otherwise manual actions will be required
            assert len(zones) == self.expected_az_count

        return zones
