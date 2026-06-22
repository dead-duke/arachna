# Copyright (C) 2026 Artem Terenin / arachna — AGPLv3
"""CLI handlers for 'arachna doctor' command."""

import sys

from ..config.doctor import print_doctor, run_doctor
from ..config.profile_config import ArachnaConfig
from . import register


@register("doctor")
def _cmd_doctor(args, config: ArachnaConfig):
    report = run_doctor(config=config)
    print_doctor(report)
    sys.exit(1 if report["total_errors"] > 0 else 0)
