import unittest
from mock import Mock
import  mock
from pcp_pidstat import CpuProcessStackUtil


class TestCpuProcessStackUtil(unittest.TestCase):

    def test_get_processes(self):
        metric_repository = mock.Mock()
        cpu_process_stack_util = CpuProcessStackUtil(metric_repository)

        with mock.patch.object(CpuProcessStackUtil,'_CpuProcessStackUtil__pids',return_value=[1,2,5,10]) as method:
            processes_list = cpu_process_stack_util.get_processes()

        self.assertEquals(len(processes_list),4)

if __name__ == '__main__':
    unittest.main()
