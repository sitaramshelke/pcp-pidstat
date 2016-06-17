import unittest
from mock import Mock
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


    # def test_cpu_usage_system_time_percentage_for_instance(self):
    #     m_repo_mock = Mock()
    #     cpu_usage = CpuUsage(m_repo_mock)
    #     cpu_usage.user_for_instance = Mock(return_value=2.23)
    #     cpu_usage.guest_for_instance = Mock(return_value=0.00)
    #     cpu_usage.system_for_instance = Mock(return_value=4.12)
    #
    #     cpu_percent_used = cpu_usage.cpuusage_for_instance(123, 1.34)
    #
    #     self.assertEquals(cpu_percent_used, 6.35)

if __name__ == '__main__':
    unittest.main()
