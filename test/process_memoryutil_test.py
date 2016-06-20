import mock
import unittest
from pcp_pidstat import ProcessMemoryUtil

class TestProcessMemoryUtil(unittest.TestCase):
    def setUp(self):
        self.__metric_repository = mock.Mock()
        self.__metric_repository.current_value = mock.Mock(side_effect=self.metric_repo_current_value_side_effect)
        self.__metric_repository.previous_value = mock.Mock(side_effect=self.metric_repo_previous_value_side_effect)

    def metric_repo_current_value_side_effect(self, metric_name,instance):
        if metric_name == 'proc.psinfo.vsize' and instance == 1:
            return 120084
        if metric_name == 'proc.psinfo.rss' and instance == 1:
            return 6272
        if metric_name == 'proc.psinfo.cmin_flt' and instance == 1:
            return 573935
        if metric_name == 'proc.psinfo.minflt' and instance == 1:
            return 14509
        if metric_name == 'proc.psinfo.cmaj_flt' and instance == 1:
            return 647
        if metric_name == 'proc.psinfo.maj_flt' and instance == 1:
            return 54
        if metric_name == 'mem.physmem':
            return 3794764
        if metric_name == 'proc.psinfo.cmd' and instance == 1:
            return "test"
        if metric_name == 'proc.psinfo.processor' and instance == 1:
            return 0
        if metric_name == 'proc.id.uid' and instance == 1:
            return 1
        if metric_name == 'proc.psinfo.pid' and instance == 1:
            return 1

    def metric_repo_previous_value_side_effect(self, metric_name,instance):
        if metric_name == 'proc.psinfo.cmin_flt' and instance == 1:
            return 573930
        if metric_name == 'proc.psinfo.minflt' and instance == 1:
            return 14500
        if metric_name == 'proc.psinfo.cmaj_flt' and instance == 1:
            return 645
        if metric_name == 'proc.psinfo.maj_flt' and instance == 1:
            return 50

    def test_vsize(self):
        process_memory_usage = ProcessMemoryUtil(1,1.34,self.__metric_repository)

        vsize = process_memory_usage.vsize()

        self.assertEquals(vsize, 120084)

    def test_rss(self):
        process_memory_usage = ProcessMemoryUtil(1,1.34,self.__metric_repository)

        rss = process_memory_usage.rss()

        self.assertEquals(rss, 6272)

    def test_mem(self):
        process_memory_usage = ProcessMemoryUtil(1,1.34,self.__metric_repository)
        test_mem = float("%.2f"%(100*float(6272)/3794764))

        mem = process_memory_usage.mem()

        self.assertEquals(mem, test_mem)

    def test_min_flt(self):
        process_memory_usage = ProcessMemoryUtil(1,1.34,self.__metric_repository)
        test_min_flt = float("%.2f"%(((573935 + 14509) - (573930 + 14500))/1.34))

        min_flt = process_memory_usage.minflt()

        self.assertEquals(min_flt, test_min_flt)

    def test_maj_flt(self):
        process_memory_usage = ProcessMemoryUtil(1,1.34,self.__metric_repository)
        test_maj_flt = float("%.2f"%(((647 + 54) - (645 + 50))/1.34))

        maj_flt = process_memory_usage.majflt()

        self.assertEquals(maj_flt, test_maj_flt)

    def test_pid(self):
        process_memory_usage = ProcessMemoryUtil(1,1.34,self.__metric_repository)

        pid = process_memory_usage.pid()

        self.assertEqual(pid,1)

    def test_process_name(self):
        process_memory_usage = ProcessMemoryUtil(1,1.34,self.__metric_repository)

        name = process_memory_usage.process_name()

        self.assertEqual(name,'test')


    def test_user_id(self):
        process_memory_usage = ProcessMemoryUtil(1,1.34,self.__metric_repository)

        user_id = process_memory_usage.user_id()

        self.assertEqual(user_id,1)


if __name__ == '__main__':
    unittest.main()
