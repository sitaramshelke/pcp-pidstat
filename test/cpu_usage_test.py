import unittest
from mock import Mock
import  mock
from pcp_pidstat import CpuUsage


class TestUserCpuUsage(unittest.TestCase):

    def test_get_processes(self):
        metric_repository = mock.Mock()
        cpu_usage = CpuUsage(metric_repository)

        with mock.patch.object(cpu_usage,'_CpuUsage__pids',return_value=[1,2,5,10]) as method:
            processes_list = cpu_usage.get_processes(1.34)

        self.assertEquals(len(processes_list),4)

if __name__ == '__main__':
    unittest.main()
