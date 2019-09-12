from typing import NewType, Union
from troposphere import GetAtt, Ref, Join


AwsRef = NewType('AwsRef', Union[str, GetAtt, Ref, Join])
