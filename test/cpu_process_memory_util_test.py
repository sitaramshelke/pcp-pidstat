import unittest
from mock import Mock
import  mock
from pcp_pidstat import CpuProcessMemoryUtil


class TestCpuProcessMemoryUtil(unittest.TestCase):

    def test_get_processes(self):
        metric_repository = mock.Mock()
        cpu_process_memory_util = CpuProcessMemoryUtil(metric_repository)

        with mock.patch.object(CpuProcessMemoryUtil,'_CpuProcessMemoryUtil__pids',return_value=[1,2,5,10]) as method:
            processes_list = cpu_process_memory_util.get_processes(1.34)

        self.assertEquals(len(processes_list),4)

if __name__ == '__main__':
    unittest.main()
