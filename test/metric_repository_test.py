import unittest
from mock import Mock
from pcp_pidstat import ReportingMetricRepository

class ReportingMetricRepositoryTest(unittest.TestCase):

    def test_returns_the_current_value_for_a_metric_that_has_instances(self):
        utime_mock = Mock(
            netValues = [(Mock(inst=111),'dummyprocess',12345)],
            netPrevValues = [(Mock(inst=111),'dummyprocess',12354)]
        )
        group = {'proc.psinfo.utime':utime_mock}
        m_repo = ReportingMetricRepository(group)

        c_utime = m_repo.current_value('proc.psinfo.utime',111)

        self.assertEquals(c_utime,12345)

    def test_returns_the_current_value_for_a_metric_that_has_no_instances(self):
        utime_mock = Mock(
            netValues = [('NULL',None,12345)],
            netPrevValues = [('NULL',None,12354)]
        )
        group = {'kernel.all.cpu.user':utime_mock}
        m_repo = ReportingMetricRepository(group)

        c_utime = m_repo.current_value('kernel.all.cpu.user',None)

        self.assertEquals(c_utime,12345)

    def test_returns_none_if_a_metric_does_not_exist_for_an_instance(self):
        utime_mock = Mock(
            netValues = [(Mock(inst=111),'dummyprocess',12345)],
            netPrevValues = [(Mock(inst=111),'dummyprocess',12354)]
        )
        group = {'proc.psinfo.utime':utime_mock}
        m_repo = ReportingMetricRepository(group)

        c_utime = m_repo.current_value('proc.psinfo.time',111)

        self.assertIsNone(c_utime)

    def test_returns_none_if_a_metric_does_not_exist_for_a_metric_that_has_no_instance(self):
        utime_mock = Mock(
            netValues = [('NULL',None,12345)],
            netPrevValues = [('NULL',None,12354)]
        )
        group = {'kernel.all.cpu.user':utime_mock}
        m_repo = ReportingMetricRepository(group)

        c_utime = m_repo.current_value('kernel.all.cpu.guest',None)

        self.assertIsNone(c_utime)

    def test_returns_the_previous_value_for_a_metric_that_has_instances(self):
        utime_mock = Mock(
            netValues = [(Mock(inst=111),'dummyprocess',12345)],
            netPrevValues = [(Mock(inst=111),'dummyprocess',12354)]
        )
        group = {'proc.psinfo.utime':utime_mock}
        m_repo = ReportingMetricRepository(group)

        c_utime = m_repo.previous_value('proc.psinfo.utime',111)

        self.assertEquals(c_utime,12354)

    def test_returns_the_previous_value_for_a_metric_that_has_no_instances(self):
        utime_mock = Mock(
            netValues = [('NULL',None,12345)],
            netPrevValues = [('NULL',None,12354)]
        )
        group = {'kernel.all.cpu.user':utime_mock}
        m_repo = ReportingMetricRepository(group)

        c_utime = m_repo.previous_value('kernel.all.cpu.user',None)

        self.assertEquals(c_utime,12354)

    def test_returns_none_if_a_metric_for_previous_value_does_not_exist_for_an_instance(self):
        utime_mock = Mock(
            netValues = [(Mock(inst=111),'dummyprocess',12345)],
            netPrevValues = [(Mock(inst=111),'dummyprocess',12354)]
        )
        group = {'proc.psinfo.utime':utime_mock}
        m_repo = ReportingMetricRepository(group)

        c_utime = m_repo.previous_value('proc.psinfo.time',111)

        self.assertIsNone(c_utime)

    def test_returns_none_if_a_metric_for_previous_value_does_not_exist_for_a_metric_that_has_no_instance(self):
        utime_mock = Mock(
            netValues = [('NULL',None,12345)],
            netPrevValues = [('NULL',None,12354)]
        )
        group = {'kernel.all.cpu.user':utime_mock}
        m_repo = ReportingMetricRepository(group)

        c_utime = m_repo.previous_value('kernel.all.cpu.guest',None)

        self.assertIsNone(c_utime)

if __name__ == "__main__":
    unittest.main()
