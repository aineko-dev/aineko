"""Entrypoint for invoking provisioner to return terraform usable response."""
import json
import sys
from typing import List, Optional

from aineko.config import AINEKO_CONFIG
from aineko.core.provisioner import Provisioner
from aineko.utils.io import load_yamls


def get_active_projects(
    env: Optional[str] = None,
    config_file: Optional[str] = None,
    conf_source: Optional[str] = None,
) -> List[str]:
    """Gets list of active projects defined in conf/main.yaml.

    Args:
        env: environment to get active projects for.
        config_file: path to main config file.
        conf_source: path to config source

    Returns:
        list: names of active projects
    """
    config_source = conf_source or AINEKO_CONFIG.get("CONF_SOURCE")
    config_file = config_file or f"{config_source}/main.yml"
    main_config = load_yamls(config_file)
    if env in main_config:
        return main_config[env]["active_projects"]
    else:
        return []


def main(
    env: str, conf_source: Optional[str] = None, destroy: bool = False
) -> None:
    """Main function to run the provisioner from the command line.

    Args:
        env: Environment to provision for.
        conf_source: Path to the directory containing the configuration files.
        destroy: Whether to destroy the existing resources. (default: False)
    """
    if destroy:
        provisioner = Provisioner(project=None)

    else:
        active_projects = get_active_projects(env=env, conf_source=conf_source)
        provisioner = Provisioner(
            project=active_projects, conf_source=conf_source
        )

    output = provisioner.run()

    sys.stdout.write(json.dumps(output))
