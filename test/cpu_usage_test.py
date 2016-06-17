import unittest
from mock import Mock
import  mock
from pcp_pidstat import CpuUsage


class TestUserCpuUsage(unittest.TestCase):
    def test_cpu_usage_user_time_percentage_for_instance(self):
        m_repo_mock = Mock(
            current_value = Mock(return_value=113300),
            previous_value = Mock(return_value=113200)
        )
        cpu_usage = CpuUsage(m_repo_mock)

        user_percent_used = cpu_usage.user_for_instance(123, 1.34)

        self.assertEquals(user_percent_used, 7.46)

    def test_cpu_usage_guest_time_percentage_for_instance(self):
        m_repo_mock = Mock(
            current_value = Mock(return_value=113330),
            previous_value = Mock(return_value=113200)
        )
        cpu_usage = CpuUsage(m_repo_mock)

        guest_percent_used = cpu_usage.guest_for_instance(123, 1.34)

        self.assertEquals(guest_percent_used, 9.70)

    def test_cpu_usage_system_time_percentage_for_instance(self):
        m_repo_mock = Mock(
            current_value = Mock(return_value=113354),
            previous_value = Mock(return_value=113220)
        )
        cpu_usage = CpuUsage(m_repo_mock)

        system_percent_used = cpu_usage.system_for_instance(123, 1.34)

        self.assertEquals(system_percent_used, 10.0)

    def c_repo_side_effect(self, metric_name,instance):
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
            return "ram"

    def p_repo_side_effect(self, metric_name,instance):
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
            return "ram"

    def test_cpu_usage_total_time_percentage_for_instance(self):
        m_repo_mock = Mock()

        cpu_usage = CpuUsage(m_repo_mock)
        with mock.patch.object(cpu_usage,'_CpuUsage__pids',return_value=[1]) as method:
            m_repo_mock.current_value = Mock(side_effect=self.c_repo_side_effect)
            m_repo_mock.previous_value = Mock(side_effect=self.p_repo_side_effect)
            test_user_percent = float("%.2f"%(100*(112233 -112223)/(1.34*1000)))
            test_guest_percent = float("%.2f"%(100*(112213-112203)/(1.34*1000)))
            test_system_percent = float("%.2f"%(100*(112243-112233)/(1.34*1000)))

            test_total_percent = test_user_percent+test_guest_percent+test_system_percent
            process_info = cpu_usage.get_processes(1.34)
            total_percent = process_info[0].total_percent

            self.assertEquals(total_percent, test_total_percent)

if __name__ == '__main__':
    unittest.main()
