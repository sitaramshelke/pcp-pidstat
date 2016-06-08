import unittest
from mock import Mock
from pcp_pidstat import UserCpuUsage


class TestUserCpuUsage(unittest.TestCase):
    def test_cpu_usage_for_an_instance(self):
        utime_mock = Mock(
            netValues=[(Mock(inst=123), 'inst', 113300)],
            netPrevValues=[(Mock(inst=123), 'inst', 113200)]
        )
        group = {'proc.psinfo.utime': utime_mock}
        user_cpu_usage = UserCpuUsage(group)

        user_percent_used = user_cpu_usage.for_instance(123, 1.34)

        self.assertEquals(user_percent_used, 13.4)

    def test_cpu_usage_for_an_instance_when_no_previous_values_returns_zero(self):
        utime_mock = Mock(
            netValues=[(Mock(inst=123), 'inst', 113300)],
            netPrevValues=None
        )
        group = {'proc.psinfo.utime': utime_mock}
        user_cpu_usage = UserCpuUsage(group)

        user_percent_used = user_cpu_usage.for_instance(123, 1.34)

        self.assertEquals(user_percent_used, 0)

    def test_cpu_usage_when_no_instance_found_returns_none(self):
        utime_mock = Mock(
            netValues=[(Mock(inst=456), 'inst', 113300)],
            netPrevValues=[(Mock(inst=456), 'inst', 113200)]
        )
        group = {'proc.psinfo.utime': utime_mock}
        user_cpu_usage = UserCpuUsage(group)

        user_percent_used = user_cpu_usage.for_instance(123, 1.34)

        self.assertIsNone(user_percent_used)


if __name__ == '__main__':
    unittest.main()
