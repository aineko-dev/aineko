# """Tests for aineko.cli.validate module."""

# from aineko.cli import validate


# def test_validate_datasets_between_pipeline_catalog(conf_directory):
#     result1 = validate.validate_datasets_between_pipeline_catalog(
#         project="test_project", conf_source=conf_directory
#     )
#     result2 = validate.validate_datasets_between_pipeline_catalog(
#         project="test_project2", conf_source=conf_directory
#     )
#     result3 = validate.validate_datasets_between_pipeline_catalog(
#         project="test_project3", conf_source=conf_directory
#     )
#     assert result1 is True
#     assert result2 is True
#     assert result3 is False


# def test_validate_datasets_between_code_catalog(conf_directory):
#     validate_pass = validate.validate_datasets_between_code_catalog(
#         project="test_project",
#         conf_source=conf_directory,
#         project_dir="tests/artifacts/sample_nodes",
#     )
#     validate_fail = validate.validate_datasets_between_code_catalog(
#         project="test_project",
#         conf_source=conf_directory,
#         project_dir="tests/artifacts/sample_nodes_fail",
#     )
#     assert validate_pass is True
#     assert validate_fail is False
