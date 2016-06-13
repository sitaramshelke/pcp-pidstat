import sys
from pcp import pmcc
from pcp import pmapi

# Metric list to be fetched
PIDSTAT_METRICS = ['pmda.uname','hinv.ncpu','proc.psinfo.pid','proc.nprocs','proc.psinfo.utime',
                    'proc.psinfo.stime','proc.psinfo.guest_time','proc.psinfo.processor',
                    'proc.id.uid','proc.psinfo.cmd','kernel.all.cpu.user','kernel.all.cpu.vuser',
                    'kernel.all.cpu.sys','kernel.all.cpu.guest','kernel.all.cpu.nice','kernel.all.cpu.idle']
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
    def __init__(self):
        pmapi.pmOptions.__init__(self,"s:t:V?")
        self.pmSetLongOptionSamples()
        self.pmSetLongOptionInterval()
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
        print "Timestamp\tUID\tPID\t%usr\t%system\t%guest\t%CPU\tCPU\tCommand"

    def instlist(self, group, name):
        return dict(map(lambda x: (x[0].inst, x[2]), group[name].netValues)).keys()

    def curVals(self, group, name):
        return dict(map(lambda x: (x[0].inst, x[2]), group[name].netValues))

    def prevVals(self, group, name):
        return dict(map(lambda x: (x[0].inst, x[2]), group[name].netPrevValues))

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

        inst_list.sort()
        for inst in inst_list:
            if inst != '':
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
