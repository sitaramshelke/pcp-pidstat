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
class CpuUsage:
    def __init__(self, metric_repository):
        self.__metric_repository = metric_repository

    def user_for_instance(self, instance, delta_time):
        percent_of_time =  100 * float(self.__metric_repository.current_value('proc.psinfo.utime', instance) - self.__metric_repository.previous_value('proc.psinfo.utime', instance)) / float(1000 * delta_time)
        return float("%.2f"%percent_of_time)

    def guest_for_instance(self, instance, delta_time):
        percent_of_time =  100 * float(self.__metric_repository.current_value('proc.psinfo.guest_time', instance) - self.__metric_repository.previous_value('proc.psinfo.guest_time', instance)) / float(1000 * delta_time)
        return float("%.2f"%percent_of_time)

    def system_for_instance(self, instance, delta_time):
        percent_of_time = 100 * float(self.__metric_repository.current_value('proc.psinfo.stime', instance) - self.__metric_repository.previous_value('proc.psinfo.stime', instance)) / float(1000 * delta_time)
        return float("%.2f"%percent_of_time)

    def cpuusage_for_instance(self, instance, delta_time):
        return self.user_for_instance(instance,delta_time)+self.guest_for_instance(instance,delta_time)+ self.system_for_instance(instance,delta_time)


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

        # Fetch metrics which only require current values
        inst_list = self.instlist(group,'proc.psinfo.pid')      #get all instance names
        pids = self.curVals(group,'proc.psinfo.pid')            #pids of the processes
        commandnames = self.curVals(group,'proc.psinfo.cmd')    #names of all processes
        cpuids = self.curVals(group,'proc.psinfo.processor')    #last processor id of the process
        userids = self.curVals(group,'proc.id.uid')             #user id of the process
        num_cpu = self.get_ncpu(group)
        user_names = self.curVals(group,'proc.id.uid_nm')

        #Fetch per Process Current and previous values
        c_usertimes = self.curVals(group,'proc.psinfo.utime')   #time spent in user mode
        p_usertimes = self.prevVals(group,'proc.psinfo.utime')

        c_guesttimes = self.curVals(group,'proc.psinfo.guest_time') #time spent in guest mode
        p_guesttimes = self.prevVals(group,'proc.psinfo.guest_time')

        c_systimes = self.curVals(group,'proc.psinfo.stime')        #time spent in sys mode
        p_systimes = self.prevVals(group,'proc.psinfo.stime')



        #calculate percentage values
        percusertime = {}
        percguesttime = {}
        percsystime = {}
        perccpuusage = {}


        interval_in_seconds = self.timeStampDelta(group)

        metric_repository = ReportingMetricRepository(group)
        cpu_usage = CpuUsage(metric_repository)

        for inst in inst_list:
            percusertime[inst] = cpu_usage.user_for_instance(inst, interval_in_seconds)
            percguesttime[inst] = cpu_usage.guest_for_instance(inst, interval_in_seconds)
            percsystime[inst] = cpu_usage.system_for_instance(inst, interval_in_seconds)
            perccpuusage[inst] = cpu_usage.cpuusage_for_instance(inst, interval_in_seconds)

            if PidstatOptions.IFlag:
                perccpuusage[inst] = perccpuusage[inst]/int(num_cpu)

        inst_list.sort()
        filtered_inst_list = inst_list
        if PidstatOptions.plist:
            filtered_inst_list = PidstatOptions.plist
        elif PidstatOptions.pFlag == "SELF":
            filtered_inst_list = [os.getpid()]
        else:
            if PidstatOptions.UFlag:
                filtered_inst_list = self.matchInstances(inst_list,user_names,PidstatOptions.UStr)
            if PidstatOptions.GFlag != "":
                filtered_inst_list = self.matchInstances(filtered_inst_list,commandnames,PidstatOptions.GFlag)

        for inst in filtered_inst_list:
            if inst != '':
                if PidstatOptions.UFlag:
                    print("%s\t%s\t%d\t%.2f\t%.2f\t%.2f\t%.2f\t%d\t%s" % (timestamp[3],user_names[inst],pids[inst],percusertime[inst],percsystime[inst],percguesttime[inst],perccpuusage[inst],cpuids[inst],commandnames[inst]))
                else:
                    print("%s\t%d\t%d\t%.2f\t%.2f\t%.2f\t%.2f\t%d\t%s" % (timestamp[3],userids[inst],pids[inst],percusertime[inst],percsystime[inst],percguesttime[inst],perccpuusage[inst],cpuids[inst],commandnames[inst]))

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
