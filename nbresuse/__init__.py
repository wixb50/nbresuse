import json
import psutil
from traitlets import Float
from traitlets.config import Configurable
from notebook.utils import url_path_join
from notebook.base.handlers import IPythonHandler


class MetricsHandler(IPythonHandler):

    def _get_sys_mem_limit(self):
        mem_limit_cg_file = "/sys/fs/cgroup/memory/memory.limit_in_bytes"
        mem_limit = 1024**3  # default value 1G
        try:
            with open(mem_limit_cg_file) as limitf:
                mem_limit = int(limitf.read())
        except FileNotFoundError:
            pass
        return mem_limit

    def _get_sys_mem_info(self):
        mem_usage_cg_file = "/sys/fs/cgroup/memory/memory.usage_in_bytes"
        mem_usage = 0
        try:
            with open(mem_usage_cg_file) as usagef:
                mem_usage = int(usagef.read())
        except FileNotFoundError:
            pass
        return mem_usage

    def _get_ipykernel_mem_info(self, kernel_id):
        mem_usage = 0
        for proc in psutil.process_iter():
            cmdline = proc.cmdline()
            if cmdline and "kernel-{}.json".format(kernel_id) in cmdline[-1]:
                mem_usage = proc.memory_info().rss
        return mem_usage

    def get(self):
        """
        Calculate and return current resource usage metrics
        """
        kernel_id = self.get_query_argument('kernel_id')
        config = self.settings['nbresuse_display_config']
        rss = self._get_ipykernel_mem_info(kernel_id) if kernel_id else self._get_sys_mem_info()

        limits = {}
        mem_limit = self._get_sys_mem_limit()

        limits['memory'] = {
            'rss': mem_limit
        }
        if config.mem_warning_threshold != 0:
            limits['memory']['warn'] = (mem_limit - rss) < (mem_limit * config.mem_warning_threshold)
        metrics = {
            'rss': rss,
            'limits': limits,
        }
        self.write(json.dumps(metrics))


def _jupyter_server_extension_paths():
    """
    Set up the server extension for collecting metrics
    """
    return [{
        'module': 'nbresuse',
    }]


def _jupyter_nbextension_paths():
    """
    Set up the notebook extension for displaying metrics
    """
    return [{
        "section": "notebook",
        "dest": "nbresuse",
        "src": "static",
        "require": "nbresuse/main"
    }]


class ResourceUseDisplay(Configurable):
    """
    Holds server-side configuration for nbresuse
    """

    mem_warning_threshold = Float(
        0.1,
        help="""
        Warn user with flashing lights when memory usage is within this fraction
        memory limit.

        For example, if memory limit is 128MB, `mem_warning_threshold` is 0.1,
        we will start warning the user when they use (128 - (128 * 0.1)) MB.

        Set to 0 to disable warning.
        """,
        config=True
    )

    cpu_warning_threshold = Float(
        0.1,
        help="""
        Warn user with flashing lights when cpu usage is within this fraction
        cpu limit.

        Set to 0 to disable warning.
        """,
        config=True
    )


def load_jupyter_server_extension(nbapp):
    """
    Called during notebook start
    """
    resuseconfig = ResourceUseDisplay(parent=nbapp)
    nbapp.web_app.settings['nbresuse_display_config'] = resuseconfig
    route_pattern = url_path_join(nbapp.web_app.settings['base_url'], '/metrics')
    nbapp.web_app.add_handlers('.*', [(route_pattern, MetricsHandler)])
