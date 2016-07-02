from mock import Mock
import unittest
from pcp_pidstat import CpuProcessStackUtilReporter

class TestProcessStackUtilReporter(unittest.TestCase):
    def setUp(self):
        self.options = Mock(
                        show_process_user = None)

        process_1 = Mock(pid = Mock(return_value = 1),
                        process_name = Mock(return_value = "process_1"),
                        user_name = Mock(return_value='pcp'),
                        user_id = Mock(return_value=1000),
                        stack_size = Mock(return_value=136))

        self.processes = [process_1]

    def test_print_report_without_filtering(self):
        process_stack_util = Mock()
        process_filter = Mock()
        printer = Mock()
        process_filter.filter_processes = Mock(return_value=self.processes)
        reporter = CpuProcessStackUtilReporter(process_stack_util, process_filter, printer, self.options)

        reporter.print_report(123)

        printer.assert_called_with("123\t1000\t1\t136\tprocess_1")

    def test_print_report_with_user_name(self):
        self.options.show_process_user = 'pcp'
        process_stack_util = Mock()
        process_filter = Mock()
        printer = Mock()
        process_filter.filter_processes = Mock(return_value=self.processes)
        reporter = CpuProcessStackUtilReporter(process_stack_util, process_filter, printer, self.options)

        reporter.print_report(123)

        printer.assert_called_with("123\tpcp\t1\t136\tprocess_1")

if __name__ == "__main__":
    unittest.main()
