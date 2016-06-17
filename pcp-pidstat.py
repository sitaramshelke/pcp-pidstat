import sys
import re
import os
from pcp import pmcc
from pcp import pmapi

# Metric list to be fetched
PIDSTAT_METRICS = ['pmda.uname','hinv.ncpu','proc.psinfo.pid','proc.nprocs','proc.psinfo.utime',
                    'proc.psinfo.stime','proc.psinfo.guest_time','proc.psinfo.processor',
                    'proc.id.uid','proc.psinfo.cmd','kernel.all.cpu.user','kernel.all.cpu.vuser',
                    'kernel.all.cpu.sys','kernel.all.cpu.guest','kernel.all.cpu.nice','kernel.all.cpu.idle',
                    'proc.id.uid_nm']
class ReportingMetricRepository:
    def __init__(self,group):
        self.group = group
        self.current_cached_values = {}
        self.previous_cached_values = {}
    def __fetch_current_values(self,metric,instance):
        if instance:
            return dict(map(lambda x: (x[0].inst, x[2]), self.group[metric].netValues))
        else:
            return self.group[metric].netValues[0][2]

    def __fetch_previous_values(self,metric,instance):
        if instance:
            return dict(map(lambda x: (x[0].inst, x[2]), self.group[metric].netPrevValues))
        else:
            return self.group[metric].netPrevValues[0][2]

    def current_value(self, metric, instance):
        if not metric in self.group:
            return None
        if instance:
            if not metric in self.current_cached_values.keys():
                lst = self.__fetch_current_values(metric,instance)
                self.current_cached_values[metric] = lst
            if instance in self.current_cached_values[metric].keys():
                return self.current_cached_values[metric].get(instance,None)
            else:
                return None
        else:
            if not metric in self.current_cached_values.keys():
                self.current_cached_values[metric] = self.__fetch_current_values(metric,instance)
            return self.current_cached_values[metric]
    def previous_value(self, metric, instance):
        if not metric in self.group:
            return None
        if instance:
            if not metric in self.previous_cached_values.keys():
                lst = self.__fetch_previous_values(metric,instance)
                self.previous_cached_values[metric] = lst
            if instance in self.previous_cached_values[metric].keys():
                return self.previous_cached_values[metric].get(instance,None)
            else:
                return 0
        else:
            if not metric in self.previous_cached_values.keys():
                self.previous_cached_values[metric] = self.__fetch_previous_values(metric,instance)
            return self.previous_cached_values[metric]

    def current_values(self, metric_name):
        return dict(map(lambda x: (x[0].inst, x[2]), self.group[metric_name].netValues))

    def previous_values(self, metric_name):
        return dict(map(lambda x: (x[0].inst, x[2]), self.group[metric_name].netPrevValues))

class ProcessCpuUsage:
    def __init__(self, user_percent, guest_percent, system_percent, pid, process_name, cpu_number, user_id, user_name):
        self.user_percent = user_percent
        self.guest_percent = guest_percent
        self.system_percent = system_percent
        self.total_percent = user_percent + guest_percent + system_percent
        self.pid = pid
        self.process_name = process_name
        self.cpu_number = cpu_number
        self.user_id = user_id
        self.user_name = user_name

class CpuUsage:
    def __init__(self, metric_repository):
        self.__metric_repository = metric_repository

    def get_processes(self, delta_time):
        return map(lambda pid: (self.__create_process_cpu_usage(pid,delta_time)), self.__pids())

    def __pids(self):
        pid_dict = self.__metric_repository.current_values('proc.psinfo.pid')
        return pid_dict.values()

    def __create_process_cpu_usage(self, instance, delta_time):
        user_percent =  100 * float(self.__metric_repository.current_value('proc.psinfo.utime', instance) - self.__metric_repository.previous_value('proc.psinfo.utime', instance)) / float(1000 * delta_time)
        user_percent = float("%.2f"%user_percent)

        guest_percent =  100 * float(self.__metric_repository.current_value('proc.psinfo.guest_time', instance) - self.__metric_repository.previous_value('proc.psinfo.guest_time', instance)) / float(1000 * delta_time)
        guest_percent = float("%.2f"%guest_percent)

        system_percent = 100 * float(self.__metric_repository.current_value('proc.psinfo.stime', instance) - self.__metric_repository.previous_value('proc.psinfo.stime', instance)) / float(1000 * delta_time)
        system_percent = float("%.2f"%system_percent)

        pid = self.pid_for_instance(instance)
        process_name= self.process_name_for_instance(instance)
        cpu_id = self.cpu_number_for_instance(instance)
        user_id = self.user_id_for_instance(instance)
        user_name = self.user_name_for_instance(instance)

        return ProcessCpuUsage(user_percent,guest_percent,system_percent,pid,process_name,cpu_id,user_id,user_name)

    def pid_for_instance(self, instance):
        return self.__metric_repository.current_value('proc.psinfo.pid', instance)

    def process_name_for_instance(self, instance):
        return self.__metric_repository.current_value('proc.psinfo.cmd', instance)

    def cpu_number_for_instance(self, instance):
        return self.__metric_repository.current_value('proc.psinfo.processor', instance)

    def user_id_for_instance(self, instance):
        return self.__metric_repository.current_value('proc.id.uid', instance)

    def user_name_for_instance(self, instance):
        return self.__metric_repository.current_value('proc.id.uid_nm', instance)

# more pmOptions to be set here
class PidstatOptions(pmapi.pmOptions):
    GFlag = ""
    IFlag = 0
    UFlag = 0
    UStr = ""
    pFlag = ""
    plist = []
    def extraOptions(self, opt,optarg, index):
        if opt == 'G':
            PidstatOptions.GFlag = optarg
        elif opt == 'I':
            PidstatOptions.IFlag = 1
        elif opt == 'U':
            PidstatOptions.UFlag = 1
            PidstatOptions.UStr = optarg
        elif opt == 'P':
            if optarg == "ALL" or optarg == "SELF":
                PidstatOptions.pFlag = optarg
            else:
                PidstatOptions.pFlag = "ALL"
                try:
                    PidstatOptions.plist = map(lambda x:int(x),optarg.split(','))
                except ValueError as e:
                    print "Invalid Process Id List: use comma separated pids without whitespaces"
                    sys.exit(1)

    def __init__(self):
        pmapi.pmOptions.__init__(self,"s:t:G:IU:P:V?")
        self.pmSetOptionCallback(self.extraOptions)
        self.pmSetLongOptionSamples()
        self.pmSetLongOptionInterval()
        self.pmSetLongOption("process_name",1,"G","process name","Select process names using regular expression.")
        self.pmSetLongOption("",0,"I","","In SMP environment, show CPU usage per processor")
        self.pmSetLongOption("user_name",0,"U","[username]","Show real user name of the tasks and optionally filter by user name")
        self.pmSetLongOption("pid_list",1,"P","pid","Show stats for specified pids, Use SELF for current process and ALL for all processes")
        self.pmSetLongOptionVersion()
        self.pmSetLongOptionHelp()

# reporting class
class PidstatReport(pmcc.MetricGroupPrinter):
    infoCount = 0      #print machine info only once
    hCount = 0         #print header labels

    def timeStampDelta(self, group):
        s = group.timestamp.tv_sec - group.prevTimestamp.tv_sec
        u = group.timestamp.tv_usec - group.prevTimestamp.tv_usec
        return (s + u / 1000000.0)

    def print_machine_info(self,group):
        machine_name = group['pmda.uname'].netValues[0][2]
        no_cpu =self.get_ncpu(group)
        print("%s\t(%s CPU)" % (machine_name,no_cpu))

    def get_ncpu(self,group):
        return group['hinv.ncpu'].netValues[0][2]
    def print_header(self):
        if PidstatOptions.UFlag:
            print "Timestamp\tUName\tPID\t%usr\t%system\t%guest\t%CPU\tCPU\tCommand"
        else:
            print "Timestamp\tUID\tPID\t%usr\t%system\t%guest\t%CPU\tCPU\tCommand"

    def instlist(self, group, name):
        return dict(map(lambda x: (x[0].inst, x[2]), group[name].netValues)).keys()

    def curVals(self, group, name):
        return dict(map(lambda x: (x[0].inst, x[2]), group[name].netValues))

    def prevVals(self, group, name):
        return dict(map(lambda x: (x[0].inst, x[2]), group[name].netPrevValues))

    def matchInstances(self,inst_list,values_list,regexp):
        matched_list = []
        for inst in inst_list:
            if re.search(regexp,values_list[inst]):
                matched_list.append(inst)
        return matched_list

    def print_process_stat(self, timestamp, processes, inst):
        if PidstatOptions.UFlag:
            print("%s\t%s\t%d\t%.2f\t%.2f\t%.2f\t%.2f\t%d\t%s" % (timestamp,processes[inst].user_name,processes[inst].pid,processes[inst].user_percent,processes[inst].system_percent,processes[inst].guest_percent,processes[inst].total_percent,processes[inst].cpu_number,processes[inst].process_name))
        else:
            print("%s\t%d\t%d\t%.2f\t%.2f\t%.2f\t%.2f\t%d\t%s" % (timestamp,processes[inst].user_id,processes[inst].pid,processes[inst].user_percent,processes[inst].system_percent,processes[inst].guest_percent,processes[inst].total_percent,processes[inst].cpu_number,processes[inst].process_name))

    def report(self,manager):
        group = manager['pidstat']
        if not self.infoCount:
            self.print_machine_info(group)  #print machine info once at the top
            self.infoCount = 1

        if group['proc.psinfo.utime'].netPrevValues == None:
            # need two fetches to report rate converted counter metrics
            return
        self.print_header()                 #print header labels everytime

        timestamp = group.contextCache.pmCtime(int(group.timestamp)).rstrip().split()
        interval_in_seconds = self.timeStampDelta(group)
        ncpu = self.get_ncpu(group)

        metric_repository = ReportingMetricRepository(group)
        cpu_usage = CpuUsage(metric_repository)
        process_list = cpu_usage.get_processes(interval_in_seconds)

        inst_list = map(lambda x: x.pid,process_list)
        user_names = dict(map(lambda x: (x.pid,x.user_name),process_list))
        command_names = dict(map(lambda x: (x.pid,x.process_name),process_list))
        processes = dict(map(lambda x: (x.pid,x),process_list))

        filtered_inst_list = inst_list

        if PidstatOptions.plist:
            filtered_inst_list = PidstatOptions.plist
        elif PidstatOptions.pFlag == "SELF":
            filtered_inst_list = [os.getpid()]
        else:
            if PidstatOptions.UFlag:
                filtered_inst_list = self.matchInstances(inst_list,user_names,PidstatOptions.UStr)
            if PidstatOptions.GFlag != "":
                filtered_inst_list = self.matchInstances(filtered_inst_list,command_names,PidstatOptions.GFlag)

        filtered_inst_list.sort()

        for inst in filtered_inst_list:
            if PidstatOptions.IFlag:
                processes[inst].total_percent /= ncpu
            self.print_process_stat(timestamp[3], processes, inst)


        print ("\n")



if __name__ == "__main__":
    try:
        opts = PidstatOptions()
        manager = pmcc.MetricGroupManager.builder(opts,sys.argv)
        manager['pidstat'] = PIDSTAT_METRICS
        manager.printer = PidstatReport()
        sts = manager.run()
        sys.exit(sts)
    except pmapi.pmErr as pmerror:
        sys.stderr.write('%s: %s\n' % (pmerror.progname,pmerror.message()))
    except pmapi.pmUsageErr as usage:
        usage.message()
        sys.exit(1)
    except KeyboardInterrupt:
        pass
