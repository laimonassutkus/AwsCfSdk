import re
import subprocess

from typing import Optional


class GitVersionResolver:
    """
    Git tags as versions resolver class.
    """
    def __init__(self, repository_url: str):
        """
        Constructor.

        :param repository_url: Repository url formatted for ssh use: e.g. git@bitbucket.org:person/repository.git
        """
        self.git_repository = repository_url

    def resolve(self, version_to_resolve: str, dev: bool = True) -> Optional[str]:
        """
        Resolves a git tagged version. E.g. If version to resolve is 2.*.*, function fetches all
        tags from a provided git repository and assigns latest tags to wildcards in version to resolve string.

        :return: Resolved version string or None if resolve failed.
        """
        # Split version to resolve string into major, minor and patch versions
        major, minor, patch = version_to_resolve.split('.')

        # Regex to match only those versions that contain only numbers, digits and a string 'dev-'
        regex = re.compile(r'^[dev\-0-9.]*$')

        # Fetch all tags from a git repository
        output = subprocess.check_output(
            ['git', 'ls-remote', '--tags', 'ssh://{}'.format(self.git_repository)])
        # Split and filter out standard git api output and leave only tag strings
        output = [line.split('\t')[1].split('/')[2] for line in output.decode().splitlines()]
        # Filter our tags that do not match version structure (e.g. dev-2.0.0 or 1.5.0)
        output = list(filter(regex.search, output))

        # Separate development versions
        dev_versions = [version.replace('dev-', '') for version in output if version.__contains__('dev')]
        # Separate production versions
        prod_versions = [version for version in output if not version.__contains__('dev')]

        # Set versions list to work with depending on environment (dev or prod)
        versions = dev_versions if dev else prod_versions

        # Split version strings  into a list of 3 integers: major, minor and patch versions
        versions = [[int(version) for version in version_string.split('.')] for version_string in versions]
        # Sort in reverse versions so the latest version would be at index 0
        versions.sort(key=lambda version: (version[0], version[1], version[2]), reverse=True)

        # Create a function that resolves each subversion independently
        def resolve_subversion(versions, index, subversion):
            if subversion != '*':
                versions = [vrs for vrs in versions if vrs[index] == int(subversion)]
            return versions, versions[0][index]

        try:
            # Resolve major version first
            versions, resolved_major = resolve_subversion(versions, 0, major)
            # Resolve minor version second
            versions, resolved_minor = resolve_subversion(versions, 1, minor)
            # Resolve patch version last
            versions, resolved_patch = resolve_subversion(versions, 2, patch)
        except IndexError:
            print('Failed to resolve version for: {}'.format(version_to_resolve))
            return None

        # Return a resolved version string which corresponds to input version to resolve
        return str(resolved_major) + '.' + str(resolved_minor) + '.' + str(resolved_patch)
