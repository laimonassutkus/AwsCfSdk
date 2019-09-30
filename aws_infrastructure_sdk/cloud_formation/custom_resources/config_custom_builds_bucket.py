class ConfigCustomBuildsBucket:
    __SUFFIX = None
    __CF_CUSTOM_BUILDS_BUCKET = 'aws.infrastructure.sdk.cf.custom.resources.{}'

    @staticmethod
    def set_suffix(suffix: str):
        ConfigCustomBuildsBucket.__SUFFIX = suffix

    @staticmethod
    def get_builds_bucket_name() -> str:
        assert ConfigCustomBuildsBucket.__SUFFIX, 'You must first set suffix in order to continue...'
        return ConfigCustomBuildsBucket.__CF_CUSTOM_BUILDS_BUCKET.format(ConfigCustomBuildsBucket.__SUFFIX)
