import mock
import unittest
from pcp_pidstat import ProcessCpuUsage

class TestProcessCpuUsage(unittest.TestCase):
    def setUp(self):
        self.__metric_repository = mock.Mock()
        self.__metric_repository.current_value = mock.Mock(side_effect=self.metric_repo_current_value_side_effect)
        self.__metric_repository.previous_value = mock.Mock(side_effect=self.metric_repo_previous_value_side_effect)

    def metric_repo_current_value_side_effect(self, metric_name,instance):
        if metric_name == 'proc.psinfo.utime' and instance == 1:
            return 112233
        if metric_name == 'proc.psinfo.guest_time' and instance == 1:
            return 112213
        if metric_name == 'proc.psinfo.stime' and instance == 1:
            return 112243
        if metric_name == 'proc.psinfo.pid' and instance == 1:
            return 1
        if metric_name == 'proc.psinfo.cmd' and instance == 1:
            return "test"
        if metric_name == 'proc.psinfo.processor' and instance == 1:
            return 0
        if metric_name == 'proc.id.uid' and instance == 1:
            return 1
        if metric_name == 'proc.id.uid_nm' and instance == 1:
            return "pcp"

    def metric_repo_previous_value_side_effect(self, metric_name,instance):
        if metric_name == 'proc.psinfo.utime' and instance == 1:
            return 112223
        if metric_name == 'proc.psinfo.guest_time' and instance == 1:
            return 112203
        if metric_name == 'proc.psinfo.stime' and instance == 1:
            return 112233
        if metric_name == 'proc.psinfo.pid' and instance == 1:
            return 1
        if metric_name == 'proc.psinfo.cmd' and instance == 1:
            return "test"
        if metric_name == 'proc.psinfo.processor' and instance == 1:
            return 0
        if metric_name == 'proc.id.uid' and instance == 1:
            return 1
        if metric_name == 'proc.id.uid_nm' and instance == 1:
            return "pcp"


    def test_user_percent(self):
        process_cpu_usage = ProcessCpuUsage(1,1.34,self.__metric_repository)
        test_user_percent = float("%.2f"%(100*(112233 -112223)/(1.34*1000)))

        user_percent = process_cpu_usage.user_percent()

        self.assertEquals(user_percent, test_user_percent)

    def test_guest_percent(self):
        process_cpu_usage = ProcessCpuUsage(1,1.34,self.__metric_repository)
        test_guest_percent = float("%.2f"%(100*(112213-112203)/(1.34*1000)))

        guest_percent = process_cpu_usage.guest_percent()

        self.assertEquals(guest_percent, test_guest_percent)

    def test_system_percent(self):
        process_cpu_usage = ProcessCpuUsage(1,1.34,self.__metric_repository)
        test_system_percent = float("%.2f"%(100*(112243-112233)/(1.34*1000)))

        system_percent = process_cpu_usage.system_percent()

        self.assertEquals(system_percent, test_system_percent)

    def test_total_percent(self):
        process_cpu_usage = ProcessCpuUsage(1,1.34,self.__metric_repository)
        test_user_percent = float("%.2f"%(100*(112233 -112223)/(1.34*1000)))
        test_guest_percent = float("%.2f"%(100*(112213-112203)/(1.34*1000)))
        test_system_percent = float("%.2f"%(100*(112243-112233)/(1.34*1000)))
        test_total_percent = test_user_percent+test_guest_percent+test_system_percent

        total_percent = process_cpu_usage.total_percent()

        self.assertEquals(total_percent, test_total_percent)

    def test_pid(self):
        process_cpu_usage = ProcessCpuUsage(1,1.34,self.__metric_repository)

        pid = process_cpu_usage.pid()

        self.assertEqual(pid,1)

    def test_process_name(self):
        process_cpu_usage = ProcessCpuUsage(1,1.34,self.__metric_repository)

        name = process_cpu_usage.process_name()

        self.assertEqual(name,'test')

    def test_cpu_number(self):
        process_cpu_usage = ProcessCpuUsage(1,1.34,self.__metric_repository)

        number = process_cpu_usage.cpu_number()

        self.assertEqual(number,0)

    def test_user_id(self):
        process_cpu_usage = ProcessCpuUsage(1,1.34,self.__metric_repository)

        user_id = process_cpu_usage.user_id()

        self.assertEqual(user_id,1)

    def test_user_name(self):
        process_cpu_usage = ProcessCpuUsage(1,1.34,self.__metric_repository)

        user_name = process_cpu_usage.user_name()

        self.assertEqual(user_name,'pcp')

if __name__ == '__main__':
    unittest.main()
