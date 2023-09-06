# Copyright 2023 Aineko Authors
# SPDX-License-Identifier: Apache-2.0
"""Pipeline metrics classes."""
from collections import defaultdict
from datetime import datetime
from typing import Optional

import ray

from aineko.config import AINEKO_CONFIG
from aineko.core.node import AbstractNode
from aineko.utils import imports


@ray.remote(num_cpus=AINEKO_CONFIG.get("DEFAULT_NUM_CPUS"))
class Alerts(AbstractNode):
    """Alerts.

    Produces alerts to the alerts dataset. Alerts are triggered by
    metrics produced to the metrics dataset. Alerts are configured
    in the pipeline config file as follows:
    _alert_name_:
        metric: _metric_name_
        func: _trigger_function_
        params: _trigger_function_params_
        metadata: _metadata_to_include_in_alert_

    Methods:
        _pre_loop_hook: called upon initialization.
        _execute: Execute the node.
    """

    def _pre_loop_hook(self, params: Optional[dict] = None) -> None:
        """Pre-loop hook.

        Args:
            params: Parameters for the node
        """
        # Setup alert triggers
        if params is None:
            raise ValueError("Alerts node requires params.")

        self.triggers = defaultdict(list)
        for _, trigger_conf in params.get(
            "triggers", AINEKO_CONFIG.get("AMBER_ALERT_TRIGGERS")
        ).items():
            self.triggers[trigger_conf["metric"]].append(
                AlertTrigger(trigger_conf)
            )

    def _execute(self, params: Optional[dict] = None) -> Optional[bool]:
        """Execute the node.

        Args:
            params: Parameters for the node
        """
        # Consume messages
        message = self.consumers["metrics"].consume(how="next", timeout=0)
        if message is None or message["message"]["metric"] not in self.triggers:
            return None

        # Check if alert is triggered
        for trigger in self.triggers[message["message"]["metric"]]:
            if trigger.check(message["message"]):
                self.producers["alerts"].produce(
                    {
                        "message": trigger.alert_msg,
                        "timestamp": datetime.now().strftime(
                            AINEKO_CONFIG.get("MSG_TIMESTAMP_FORMAT")
                        ),
                    }
                )

        return None


class AlertTrigger:
    """Alert trigger.

    Args:
        trigger_conf (dict): Trigger configuration
            of the form: {"metric": str,
                          "params": dict,
                          "metadata_filter": dict,
                          "func": str,}

    Attributes:
        metric (str): Metric name
        params (dict): Trigger parameters
        metadata_filter (dict): Trigger metadata filter
        func (function): Trigger function
        alert_msg (str): Alert message

    Methods:
        check_metadata: Check if the message metadata matches
            the required trigger metadata
        check: Check if an alert is triggered
    """

    def __init__(self, trigger_conf: dict):
        """Initialize the metric trigger."""
        # Set trigger configuration
        self.metric = trigger_conf["metric"]
        self.params = trigger_conf["params"]
        self.metadata_filter = trigger_conf.get("metadata_filter", {})

        # Import trigger function
        self.func = imports.import_from_string(
            attr=trigger_conf["func"],
            kind="function",
            reqd_params=["value", "params"],
            ret_type=bool,
        )
        self.alert_msg = (
            f"{trigger_conf['func'].rsplit('.', 1)[-1]} alert "
            f"triggered for metric {self.metric}"
        )

    def check_metadata(self, message: dict, metadata_filter: dict) -> bool:
        """Check if the message metadata matches the required trigger metadata.

        Args:
            message: Message
            metadata_filter: Trigger metadata filter

        Returns:
            True if message metadata matches the trigger metadata else False
        """
        for key, value in metadata_filter.items():
            if message["metadata"][key] != value:
                return False
        return True

    def check(self, message: dict) -> bool:
        """Check if an alert is triggered.

        Args:
            message: Message

        Returns:
            True if metric value satisfies func with params else False
        """
        if not self.check_metadata(message, self.metadata_filter):
            return False
        return self.func(message["value"], self.params)
