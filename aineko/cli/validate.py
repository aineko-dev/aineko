"""Validates Aineko config files by comparing datasets."""
import os
import sys
from typing import NoReturn, Optional

import yaml

from aineko.config import AINEKO_CONFIG
from aineko.core.config_loader import ConfigLoader


def validate_datasets_between_pipeline_catalog(
    project: str, conf_source: str, fix_catalog: bool = False
) -> bool:
    """Validates datasets between pipeline and catalog.

    Uses ConfigLoader to load config for single project and identify
    all datasets in corresponding project pipeline and catalog yaml
    files. Uses set difference to identify datasets that are in the
    pipeline yaml file(s) but not in the catalog yaml file(s).

    Prints names of datasets that are in the pipeline yaml file(s) but
    are missing from the catalog yaml file(s).

    If fix_catalog is True, then adds missing datasets to a
    catalog_fix.yml in the project directory.

    Args:
        project: project name(s) to load config for
        conf_source: path of configuration files.

    Raises:
        ValueError: If datasets are missing from either pipeline or catalog.

    Returns:
        True if datasets are consistent between pipeline and catalog
    """
    cl = ConfigLoader(project=project, conf_source=conf_source)
    project_config = cl.load_config()
    is_valid = True
    for proj_name, proj_val in project_config.items():
        for pipeline_name, pipeline_config in proj_val.items():
            set_differences = cl.compare_data_pipeline_and_catalog(
                cl.get_datasets_for_pipeline_catalog(pipeline_config),
                cl.get_datasets_for_pipeline_nodes(pipeline_config),
            )
            pipeline_only = set_differences["pipeline_only"]
            if pipeline_only:
                is_valid = False
                datasets = "\n".join(pipeline_only)
                print(
                    f"The following datasets for project `{proj_name}` in the "
                    f"pipeline config yaml for pipeline `{pipeline_name}` are "
                    "not defined in the catalog yaml: \n"
                    f"{datasets}"
                )
                if fix_catalog:
                    print("Fixing catalog yaml file...")
                    fix_catalog_file = os.path.join(
                        conf_source, proj_name, "catalog_fix.yml"
                    )
                    if os.path.isfile(fix_catalog_file):
                        with open(
                            fix_catalog_file, "r", encoding="utf-8"
                        ) as f:
                            fix_catalog_struct = yaml.safe_load(f)
                    else:
                        fix_catalog_struct = {}
                    for dataset in pipeline_only:
                        fix_catalog_struct[dataset] = {"type": "kafka_stream"}
                    with open(fix_catalog_file, "w", encoding="utf-8") as f:
                        yaml.dump(fix_catalog_struct, f)
                    print(f"Catalog yaml file fixed at {fix_catalog_file}")
    if is_valid:
        print("Successfully Validated Pipeline and Catalog Datasets")
    return is_valid


def validate_datasets_between_code_catalog(
    project: str, conf_source: str, project_dir: str, fix_catalog: bool = False
) -> bool:
    """Validates datasets between code and catalog.

    Uses ConfigLoader to load config for single project and identify
    all datasets in corresponding project code and catalog yaml
    files. Uses set difference to identify datasets that are in the
    python code file(s) but not in the catalog yaml file(s).

    Prints names of datasets that are in the python code file(s) but
    are missing from the catalog yaml file(s).

    If fix_catalog is True, then adds missing datasets to a
    catalog_fix.yml in the project directory.

    Args:
        project: project name(s) to load config for
        conf_source: path of configuration files.
        project_dir: path of project directory.

    Returns:
        True if datasets are consistent between code and catalog
    """
    cl = ConfigLoader(project=project, conf_source=conf_source)
    project_config = cl.load_config()
    is_valid = True
    for proj_name, proj_val in project_config.items():
        for pipeline_name, pipeline_config in proj_val.items():
            set_differences = cl.compare_data_code_and_catalog(
                catalog_datasets=cl.get_datasets_for_pipeline_catalog(
                    pipeline_config
                ),
                code_datasets=cl.get_datasets_for_python_files(project_dir),
            )
            code_only = set_differences["code_only"]
            if code_only:
                is_valid = False
                datasets = "\n".join(code_only)
                print(
                    f"The following datasets for project `{proj_name}` in the "
                    f"code for pipeline `{pipeline_name}` are "
                    "not defined in the catalog yaml: \n"
                    f"{datasets}"
                )
                if fix_catalog:
                    print("Fixing catalog yaml file...")
                    fix_catalog_file = os.path.join(
                        conf_source, proj_name, "catalog_fix.yml"
                    )
                    if os.path.isfile(fix_catalog_file):
                        with open(
                            fix_catalog_file, "r", encoding="utf-8"
                        ) as f:
                            fix_catalog_struct = yaml.safe_load(f)
                    else:
                        fix_catalog_struct = {}
                    for dataset in code_only:
                        fix_catalog_struct[dataset] = {"type": "kafka_stream"}
                    with open(fix_catalog_file, "w", encoding="utf-8") as f:
                        yaml.dump(fix_catalog_struct, f)
                    print(f"Catalog yaml file fixed at {fix_catalog_file}")
    if is_valid:
        print("Successfully Validated Code and Catalog Datasets")
    return is_valid


def main(
    project_names: str,
    conf_source: Optional[str] = None,
    project_dir: Optional[str] = None,
    fix_catalog: bool = False,
) -> NoReturn:
    """Main function for validating datasets between pipeline and catalog.

    Args:
        project_names: project name(s) to load config for
        conf_source: Path to the directory containing the configuration files.
        project_dir: path of project directory.
        fix_catalog: Whether to fix the catalog file. (default: False)
    """
    if conf_source is None:
        conf_source = AINEKO_CONFIG.get("CONF_SOURCE")

    is_valid_datasets_between_pipeline_catalog = (
        validate_datasets_between_pipeline_catalog(
            project=project_names,
            conf_source=conf_source,
            fix_catalog=fix_catalog,
        )
    )
    if project_dir is not None:
        is_valid_datasets_between_code_catalog = (
            validate_datasets_between_code_catalog(
                project=project_names,
                conf_source=conf_source,
                project_dir=project_dir,
                fix_catalog=fix_catalog,
            )
        )
        is_valid_all_datasets = (
            is_valid_datasets_between_pipeline_catalog
            and is_valid_datasets_between_code_catalog
        )
        if is_valid_all_datasets:
            sys.exit(0)
        else:
            sys.exit(1)
    if is_valid_datasets_between_pipeline_catalog:
        sys.exit(0)
    else:
        sys.exit(1)
