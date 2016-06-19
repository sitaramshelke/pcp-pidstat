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
                    'proc.id.uid_nm', 'proc.psinfo.rt_priority', 'proc.psinfo.policy', 'proc.psinfo.minflt',
                    'proc.psinfo.maj_flt', 'proc.psinfo.vsize', 'proc.psinfo.rss', 'mem.physmem',
                    'proc.psinfo.cmin_flt', 'proc.psinfo.cmaj_flt']
SCHED_POLICY = ['NORMAL','FIFO','RR','BATCH','','IDLE','DEADLINE']

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
    def __init__(self, instance, delta_time, metrics_repository):
        self.instance = instance
        self.__delta_time = delta_time
        self.__metric_repository = metrics_repository
    def user_percent(self):
        # Pulled out of CpuUsage class
        percent_of_time =  100 * float(self.__metric_repository.current_value('proc.psinfo.utime', self.instance) - self.__metric_repository.previous_value('proc.psinfo.utime', self.instance)) / float(1000 * self.__delta_time)
        return float("%.2f"%percent_of_time)

    def guest_percent(self):
        percent_of_time =  100 * float(self.__metric_repository.current_value('proc.psinfo.guest_time', self.instance) - self.__metric_repository.previous_value('proc.psinfo.guest_time', self.instance)) / float(1000 * self.__delta_time)
        return float("%.2f"%percent_of_time)

    def system_percent(self):
        percent_of_time =  100 * float(self.__metric_repository.current_value('proc.psinfo.stime', self.instance) - self.__metric_repository.previous_value('proc.psinfo.stime', self.instance)) / float(1000 * self.__delta_time)
        return float("%.2f"%percent_of_time)

    def total_percent(self):
        return self.user_percent()+self.guest_percent()+self.system_percent()

    def pid(self):
        return self.__metric_repository.current_value('proc.psinfo.pid', self.instance)

    def process_name(self):
        return self.__metric_repository.current_value('proc.psinfo.cmd', self.instance)

    def cpu_number(self):
        return self.__metric_repository.current_value('proc.psinfo.processor', self.instance)

    def user_id(self):
        return self.__metric_repository.current_value('proc.id.uid', self.instance)

    def user_name(self):
        return self.__metric_repository.current_value('proc.id.uid_nm', self.instance)

class CpuUsage:
    def __init__(self, metric_repository):
        self.__metric_repository = metric_repository

    def get_processes(self, delta_time):
        return map(lambda pid: (ProcessCpuUsage(pid,delta_time,self.__metric_repository)), self.__pids())

    def __pids(self):
        pid_dict = self.__metric_repository.current_values('proc.psinfo.pid')
        return pid_dict.values()


class ProcessPriority:
    def __init__(self, instance, metrics_repository):
        self.instance = instance
        self.__metric_repository = metrics_repository

    def pid(self):
        return self.__metric_repository.current_value('proc.psinfo.pid', self.instance)

    def user_id(self):
        return self.__metric_repository.current_value('proc.id.uid', self.instance)

    def process_name(self):
        return self.__metric_repository.current_value('proc.psinfo.cmd', self.instance)

    def priority(self):
        return self.__metric_repository.current_value('proc.psinfo.rt_priority', self.instance)

    def policy_int(self):
        return self.__metric_repository.current_value('proc.psinfo.policy', self.instance)

    def policy(self):
        policy_int = self.__metric_repository.current_value('proc.psinfo.policy', self.instance)
        return SCHED_POLICY[policy_int]

class CpuProcessPriorities:
    def __init__(self, metric_repository):
        self.__metric_repository = metric_repository
    def get_processes(self):
        return map((lambda pid: (ProcessPriority(pid,self.__metric_repository))), self.__pids())

    def __pids(self):
        pid_dict = self.__metric_repository.current_values('proc.psinfo.pid')
        return pid_dict.values()

class ProcessMemoryUtil:
    def __init__(self, instance, delta_time,  metric_repository):
        self.instance = instance
        self.__metric_repository = metric_repository
        self.delta_time = delta_time

    def pid(self):
        return self.__metric_repository.current_value('proc.psinfo.pid', self.instance)

    def user_id(self):
        return self.__metric_repository.current_value('proc.id.uid', self.instance)

    def process_name(self):
        return self.__metric_repository.current_value('proc.psinfo.cmd', self.instance)

    def minflt(self):
        c_min_flt = self.__metric_repository.current_value('proc.psinfo.minflt', self.instance) + self.__metric_repository.current_value('proc.psinfo.cmin_flt', self.instance)
        p_min_flt = self.__metric_repository.previous_value('proc.psinfo.minflt', self.instance) + self.__metric_repository.previous_value('proc.psinfo.cmin_flt', self.instance)

        return float("%.2f" % ((c_min_flt - p_min_flt)/self.delta_time))

    def majflt(self):
        c_maj_flt = self.__metric_repository.current_value('proc.psinfo.maj_flt', self.instance) + self.__metric_repository.current_value('proc.psinfo.cmaj_flt', self.instance)
        p_maj_flt = self.__metric_repository.previous_value('proc.psinfo.maj_flt', self.instance) + self.__metric_repository.previous_value('proc.psinfo.cmaj_flt', self.instance)
        maj_flt_per_sec =  (c_maj_flt - p_maj_flt)/self.delta_time
        return float("%.2f"%maj_flt_per_sec)

    def vsize(self):
        return self.__metric_repository.current_value('proc.psinfo.vsize', self.instance)

    def rss(self):
        return self.__metric_repository.current_value('proc.psinfo.rss', self.instance)

    def mem(self):
        total_mem = self.__metric_repository.current_value('mem.physmem', None)
        rss = self.__metric_repository.current_value('proc.psinfo.rss', self.instance)
        return float("%.2f" % (100*float(rss)/total_mem))

class CpuProcessMemoryUtil:
    def __init__(self, metric_repository):
        self.__metric_repository = metric_repository

    def get_processes(self, delta_time):
        return map((lambda pid: (ProcessMemoryUtil(pid, delta_time, self.__metric_repository))), self.__pids())

    def __pids(self):
        pid_dict = self.__metric_repository.current_values('proc.psinfo.pid')
        return pid_dict.values()

# more pmOptions to be set here
class PidstatOptions(pmapi.pmOptions):
    GFlag = ""
    RFlag = 0
    IFlag = 0
    UFlag = 0
    UStr = ""
    pFlag = ""
    plist = []
    def extraOptions(self, opt,optarg, index):
        if opt == 'r':
            PidstatOptions.rFlag = 1
        elif opt == 'R':
            PidstatOptions.RFlag = 1
        elif opt == 'G':
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
        pmapi.pmOptions.__init__(self,"s:t:G:IU:P:RrV?")
        self.pmSetOptionCallback(self.extraOptions)
        self.pmSetLongOptionSamples()
        self.pmSetLongOptionInterval()
        self.pmSetLongOption("process-name",1,"G","process name","Select process names using regular expression.")
        self.pmSetLongOption("",0,"I","","In SMP environment, show CPU usage per processor.")
        self.pmSetLongOption("user-name",0,"U","[username]","Show real user name of the tasks and optionally filter by user name.")
        self.pmSetLongOption("pid-list",1,"P","pid","Show stats for specified pids, Use SELF for current process and ALL for all processes.")
        self.pmSetLongOption("",0,"R","","Report realtime priority and scheduling policy information.")
        self.pmSetLongOption("",0,"r","","Report page faults and memory utilization.")
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
        if PidstatOptions.rFlag:
            print "Timestamp\tUID\tPID\tMinFlt/s\tMajFlt/s\tVSize\tRSS\t%Mem\tCommand"
        elif PidstatOptions.RFlag:
            print "Timestamp\tUID\tPID\tprio\tpolicy\tCommand"
        elif PidstatOptions.UFlag:
            print "Timestamp\tUName\tPID\tusr\t%ystem\tguest\t%CPU\tCPU\tCommand"
        else:
            print "Timestamp\tUID\tPID\tusr\tsystem\tguest\t%CPU\tCPU\tCommand"

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
        if PidstatOptions.rFlag:
            print("%s\t%d\t%d\t%.2f\t\t%.2f\t\t%d\t%d\t%.2f\t%s" % (timestamp,processes[inst].user_id(),processes[inst].pid(),processes[inst].minflt(),processes[inst].majflt(),processes[inst].vsize(),processes[inst].rss(),processes[inst].mem(),processes[inst].process_name()))
        elif PidstatOptions.RFlag:
            print("%s\t%d\t%d\t%d\t%s\t%s" % (timestamp,processes[inst].user_id(),processes[inst].pid(),processes[inst].priority(),processes[inst].policy(),processes[inst].process_name()))
        elif PidstatOptions.UFlag:
            print("%s\t%s\t%d\t%.2f\t%.2f\t%.2f\t%.2f\t%d\t%s" % (timestamp,processes[inst].user_name(),processes[inst].pid(),processes[inst].user_percent(),processes[inst].system_percent(),processes[inst].guest_percent(),processes[inst].total_percent(),processes[inst].cpu_number(),processes[inst].process_name()))
        else:
            print("%s\t%d\t%d\t%.2f\t%.2f\t%.2f\t%.2f\t%d\t%s" % (timestamp,processes[inst].user_id(),processes[inst].pid(),processes[inst].user_percent(),processes[inst].system_percent(),processes[inst].guest_percent(),processes[inst].total_percent(),processes[inst].cpu_number(),processes[inst].process_name()))

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
        filtered_inst_list = []
        processes = {}

        if(PidstatOptions.rFlag):
            process_memory_util = CpuProcessMemoryUtil(metric_repository)
            process_list = process_memory_util.get_processes(1.34)
            inst_list = map(lambda x: x.pid(),process_list)
            processes = dict(map(lambda x: (x.pid(),x),process_list))

            filtered_inst_list = [process.pid() for process in process_list if process.vsize() > 0]
            processes = dict(map(lambda x: (x.pid(),x),process_list))
        elif(PidstatOptions.RFlag):
            process_priority = CpuProcessPriorities(metric_repository)
            process_list = process_priority.get_processes()
            inst_list = map(lambda x: x.pid(),process_list)
            processes = dict(map(lambda x: (x.pid(),x),process_list))

            filtered_inst_list = [process.pid() for process in process_list if process.vsize() > 0]
            processes = dict(map(lambda x: (x.pid(),x),process_list))
        else:
            cpu_usage = CpuUsage(metric_repository)
            process_list = cpu_usage.get_processes(interval_in_seconds)

            inst_list = map(lambda x: x.pid(),process_list)
            user_names = dict(map(lambda x: (x.pid(),x.user_name()),process_list))
            command_names = dict(map(lambda x: (x.pid(),x.process_name()),process_list))
            processes = dict(map(lambda x: (x.pid(),x),process_list))

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
