"""Tests for the aineko.core.provisioner module."""

from aineko.core.provisioner import Provisioner


def test_determine_resources(provisioner: type[Provisioner]) -> None:
    # Test conf/test
    expected = {
        "pipelines": [
            {
                "project": "test_project",
                "pipeline": "test_run_1",
                "instance_type": "m5.xlarge",
                "aws_secrets": "test/aineko_secret",
            },
            {
                "project": "test_project",
                "pipeline": "test_run_2",
                "instance_type": "m5.xlarge",
                "aws_secrets": "test/aineko_secret",
            },
        ],
        "amber_pipeline": [
            {
                "aws_secrets": "",
                "instance_type": "m5.xlarge",
                "pipeline": "monitoring_pipeline",
                "project": "amber",
            }
        ],
    }

    required_resources = provisioner.run()
    assert required_resources == expected


def test_determine_resources_range(provisioner: type[Provisioner]) -> None:
    # Test other configs
    config = {
        "test_project": {
            # Same vcpu smaller mem
            "pipeline_1": {
                "machine_config": {"type": "ec2", "mem": 0.5, "vcpu": 2}
            },
            # Same mem smaller vcpu
            "pipeline_2": {
                "machine_config": {"type": "ec2", "mem": 16, "vcpu": 2}
            },
            # Smaller mem and vcpu
            "pipeline_3": {
                "machine_config": {"type": "ec2", "mem": 12, "vcpu": 3}
            },
            # Larger mem and vcpu
            "pipeline_4": {
                "machine_config": {"type": "ec2", "mem": 33, "vcpu": 9}
            },
        },
    }
    # pylint: disable=protected-access
    required_resources = provisioner._determine_resources(config)
    # pylint: enable=protected-access
    expected = [
        {
            "project": "test_project",
            "pipeline": "pipeline_1",
            "instance_type": "m5.large",
            "aws_secrets": "",
        },
        {
            "project": "test_project",
            "pipeline": "pipeline_2",
            "instance_type": "m5.xlarge",
            "aws_secrets": "",
        },
        {
            "project": "test_project",
            "pipeline": "pipeline_3",
            "instance_type": "m5.xlarge",
            "aws_secrets": "",
        },
        {
            "project": "test_project",
            "pipeline": "pipeline_4",
            "instance_type": "m5.4xlarge",
            "aws_secrets": "",
        },
    ]

    assert required_resources == expected


def test_no_projects_provisioner() -> None:
    provisioner = Provisioner(None)
    pipelines = provisioner.run()
    assert not pipelines["pipelines"]
    assert pipelines["amber_pipeline"]
