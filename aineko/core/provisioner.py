"""Module that provisions the IAC necessary for a pipeline."""
from typing import List, Optional, Union

from aineko.config import AINEKO_CONFIG, AWS_CONFIG
from aineko.core.config_loader import ConfigLoader


class Provisioner:
    """Class that creates the IAC necessary for a pipeline.

    The generated variables will be used to provision machines in the CI/CD
    process.

    Args:
        project (Union[str,list]): name of the project
        conf_source (str): source path of the config

    Attributes:
        project (str): name of the project
        conf_source (str): source path of the config
    """

    def __init__(
        self,
        project: Optional[Union[str, list]] = None,
        conf_source: Optional[str] = None,
    ):
        """Initializes the provisioner class."""
        self.project = project
        self.conf_source = conf_source

    def run(self) -> dict:
        """Runs the provisioner.

        Step 1: Load config for pipelines and amber
        Step 2: Determine required AWS compute instance types

        Returns:
            dict: dictionary of required resources for each pipeline
        """
        if self.project:
            config = ConfigLoader(self.project, self.conf_source).load_config()
        else:
            config = {}

        amber_config = ConfigLoader(
            AINEKO_CONFIG.get("AMBER_PROJECT_DIR"),
            AINEKO_CONFIG.get("AMBER_CONF_SOURCE"),
        ).load_config()

        return {
            "pipelines": self._determine_resources(config),
            "amber_pipeline": self._determine_resources(amber_config),
        }

    def _determine_resources(self, config: dict) -> List[dict]:
        """Determines the aws resources required for each pipeline.

        Depending on the compute resources required. For EC2 instances, the
        instance chosen will be the smallest one that fulfills both memory and
        vcpu specifications.

        Args:
            config: config object returned by the config loader

        Returns:
            List of AWS resource required for each pipeline.
                Example:
                    [
                        {
                            "project": "test",
                            "pipeline": "test_pipeline",
                            "instance_type": "t2.xlarge"
                        },
                        ...
                    ]
        """
        required_resources = []

        for project, project_config in config.items():
            for pipeline, pipeline_config in project_config.items():
                machine_config = pipeline_config["machine_config"]

                # Use biggest by default
                selected_instance = list(AWS_CONFIG.get("EC2_SPEC"))[-1]
                for instance, specs in AWS_CONFIG.get("EC2_SPEC").items():
                    if (machine_config["mem"] <= specs["mem"]) and (
                        machine_config["vcpu"] <= specs["vcpu"]
                    ):
                        # Pick smallest instance that fulfills conditions
                        selected_instance = instance
                        break

                required_resources.append(
                    {
                        "project": project,
                        "pipeline": pipeline,
                        "instance_type": selected_instance,
                        "aws_secrets": ",".join(
                            pipeline_config.get("aws_secrets", [""])
                        ),
                    }
                )
        return required_resources
