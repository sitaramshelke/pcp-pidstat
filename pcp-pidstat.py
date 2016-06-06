import sys
from pcp import pmcc
from pcp import pmapi

# Metric list to be fetched
PIDSTAT_METRICS = ['pmda.uname','hinv.ncpu','proc.psinfo.pid','proc.nprocs','proc.psinfo.utime',
                    'proc.psinfo.stime','proc.psinfo.guest_time','proc.psinfo.processor',
                    'proc.id.uid','proc.psinfo.cmd','kernel.all.cpu.user','kernel.all.cpu.vuser',
                    'kernel.all.cpu.sys','kernel.all.cpu.guest','kernel.all.cpu.nice','kernel.all.cpu.idle']

# more pmOptions to be set here
class PidstatOptions(pmapi.pmOptions):
    def __init__(self):
        pmapi.pmOptions.__init__(self)
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
        return dict(map(lambda x: (x[1], x[2]), group[name].netValues)).keys()

    def curVal(self,group,name):
        return group[name].netValues[0][2]
    def prevVal(self,group,name):
        return group[name].netPrevValues[0][2]
    def curVals(self, group, name):
        return dict(map(lambda x: (x[1], x[2]), group[name].netValues))

    def prevVals(self, group, name):
        return dict(map(lambda x: (x[1], x[2]), group[name].netPrevValues))

    def report(self,manager):
        group = manager['pidstat']
        if not self.infoCount:
            self.print_machine_info(group)  #print machine info once at the top
            self.infoCount = 1

        self.print_header()                 #print header labels everytime
        if group['proc.psinfo.utime'].netPrevValues == None:
            # need two fetches to report rate converted counter metrics
            return

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

        #Fetch total times for cpu
        c_totalusertimes = self.curVal(group,'kernel.all.cpu.vuser')    #time spent in user mode excluding guest
        p_totalusertimes = self.prevVal(group,'kernel.all.cpu.vuser')

        c_totalguesttimes = self.curVal(group,'kernel.all.cpu.guest')   #time spent in guest mode
        p_totalguesttimes = self.prevVal(group,'kernel.all.cpu.guest')

        c_totalsystimes = self.curVal(group,'kernel.all.cpu.sys')       #time spent in sys mode
        p_totalsystimes = self.prevVal(group,'kernel.all.cpu.sys')

        c_totalnicetimes = self.curVal(group,'kernel.all.cpu.nice')     #time spent in user nice mode
        p_totalnicetimes = self.prevVal(group,'kernel.all.cpu.nice')

        c_totalidletimes = self.curVal(group,'kernel.all.cpu.idle')     #time spent in idle mode
        p_totalidletimes = self.prevVal(group,'kernel.all.cpu.idle')

        #calculate percentage values
        percusertime = {}
        percguesttime = {}
        percsystime = {}
        perccpuusage = {}


        interval_in_seconds = self.timeStampDelta(group)

        for inst in inst_list:
            if inst != '':
                percusertime[inst] = 100*float(c_usertimes[inst] - p_usertimes[inst])/1000*interval_in_seconds
                if (c_totalguesttimes - p_totalguesttimes) != 0:
                    percguesttime[inst] = 100*float(c_guesttimes[inst] - p_guesttimes[inst])/1000*interval_in_seconds
                else:
                    percguesttime[inst] = 0.00
                percsystime[inst] = 100*(float((c_systimes[inst] - p_systimes[inst]))/(c_totalsystimes - p_totalsystimes))
                percsystime[inst] = 100*float(c_systimes[inst] - p_systimes[inst])/1000*interval_in_seconds

                c_proctimes = c_usertimes[inst]+c_systimes[inst]
                p_proctimes = p_usertimes[inst]+p_systimes[inst]

                c_cputimes = c_totalusertimes+c_totalsystimes+c_totalidletimes+c_totalnicetimes
                p_cputimes = p_totalusertimes+p_totalsystimes+p_totalidletimes+p_totalnicetimes

                ncpu = self.get_ncpu(group)
                perccpuusage[inst] = (ncpu * 100 * float(c_proctimes-p_proctimes))/(c_cputimes - p_cputimes)

        inst_list.sort()
        for inst in inst_list:
            if inst != '':
                print("%s\t%d\t%d\t%.2f\t%.2f\t%.2f\t%.2f\t%d\t%s" % (timestamp[3],userids[inst],pids[inst],percusertime[inst],percsystime[inst],percguesttime[inst],perccpuusage[inst],cpuids[inst],commandnames[inst]))

        print ("\n\n")



if __name__ == "__main__":
    try:
        opts = PidstatOptions()
        # opts.pmSetOptionSamples('1')
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
