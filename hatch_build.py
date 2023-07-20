import logging
import subprocess
from pathlib import Path

from hatchling.builders.hooks.plugin.interface import BuildHookInterface

logger = logging.getLogger(__name__)


class GetJsDepsHook(BuildHookInterface):
    def initialize(self, version, build_data):
        subprocess.run(
            str(Path(self.root).joinpath("get_js_deps.sh")),  # noqa : S603
            check=True,
        )
        return super().initialize(version, build_data)
