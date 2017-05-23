#!/usr/bin/env python
import json
import os
import signal
import sys
import threading
import time

class akita:

    def __init__(self):
        self.active = True
        self.userConfigDirectory = os.path.expanduser('~/.config/akita/')
        self.akitaProcDirectory = self.userConfigDirectory + 'proc.d/'
        self.akitaConfigFile = self.userConfigDirectory + 'akita.json'
        self.userConfigFile = self.userConfigDirectory + 'jobs.json'
        self.config = self.readConfig()
        self.jobs = self.prepareJobs()

        # Hook sigint
        signal.signal(signal.SIGINT, self.sig_handler)

    def readConfig(self):
        config = []
        if not os.path.exists(self.userConfigDirectory):
            os.makedirs(self.userConfigDirectory)
        if os.path.isfile(self.userConfigFile):
            with open(self.userConfigFile, 'r') as f:
                raw_data = f.read()

            if raw_data:
                try:
                    config = json.loads(raw_data)
                except:
                    print "Invalid JSON in config file ", self.userConfigFile
                    print "Please fix this and relaunch akita"
                    sys.exit(1)

        return config

    def prepareJobs(self):
        # Parses jobs stored in self.config
        # Loads them into a nice dictionary to be used by the watcher
        jobs = []
        for job in self.config:
            jobs.append( self.buildJob( job ) )

        return jobs

    def buildJob(self, jobEntry):
        if not 'name' in jobEntry or not 'ip' in jobEntry:
            print "Invalid entry in ", self.userConfigFile
            print "Missing name or ip in object ", jobEntry
            print "Please fix this and relaunch akita"
            sys.exit(1)

        reconnectAction = False
        if 'reconnectAction' in jobEntry:
            reconnectAction = jobEntry['reconnectAction']

        reconnectTimer = 120
        if 'reconnectTimer' in jobEntry:
            reconnectTimer = int(jobEntry['reconnectTimer'])

        disconnectAction = False
        if 'disconnectAction' in jobEntry:
            disconnectAction = jobEntry['disconnectAction']

        disconnectTimer = 60
        if 'disconnectTimer' in jobEntry:
            disconnectTimer = int(jobEntry['disconnectTimer'])
        
        job = {
            'name': jobEntry['name'],
            'ip': jobEntry['ip'],
            'lastSeen': time.time(),
            'reconnectAction': reconnectAction,
            'reconnectTimer': reconnectTimer,
            'disconnectAction': disconnectAction,
            'disconnectTimer': disconnectTimer
        }
        return job

    def sig_handler(self, signal, frame):
        print "User interrupted. Exiting!"
        self.active = False
        sys.exit(0)

    def main(self):
        if len(self.jobs) < 1:
            print "There are no jobs configured for watching. Goodbye"
            sys.exit(0)

        print "Found " + str(len(self.jobs)) + " jobs to monitor"

        for job in self.jobs:
            job['thread'] = threading.Thread(target=self.watch, args=[job])
            job['thread'].start()

        # Wait for sigint in the main thread.
        while self.active:
            time.sleep(0.1)

    def watch(self, job):
        print "Starting monitor thread for " + job['name']

        lastAttempt = 0
        hasTriggeredOffline = False
        pollingFrequency = 5

        while self.active:

            now = int(time.time())
            loopDiff = now - lastAttempt
            timeDiff = int(round((now - job['lastSeen'])))

            if loopDiff >= pollingFrequency:
                print "Polling " + job['ip']

                # Check for a ping
                if self.isDevicePresent( job['ip'] ):
                    
                    print "Reply from " + job['ip']
                    if timeDiff >= job['reconnectTimer']:
                        print job['ip'] + ' has reconnected after ' + str(timeDiff) + ' seconds. Proc!'
                        self.fireTrigger('reconnectAction', job, timeDiff)

                    job['lastSeen'] = now
                    timeDiff = 0
                    hasTriggeredOffline = False
                else:
                    #Increase the number of failed attempts
                    print job['name'] + ' did not respond (' + str(timeDiff) + ' seconds)'

                # If there is a failed event and we haven't already fired it
                if not hasTriggeredOffline:

                    if timeDiff >= job['disconnectTimer']:
                        print job['ip'] + ' has bee off for ' + str(timeDiff) + ' seconds. Proc!'
                        self.fireTrigger('disconnectAction', job, timeDiff)
                        hasTriggeredOffline = True

                lastAttempt = now


            time.sleep(0.1)

    def isDevicePresent(self, ip):
        query = "/usr/bin/fping -t 200 " + ip + ' > /dev/null 2>&1'
        response = os.system(query)
        if response == 0:
            return True

        return False

    def fireTrigger(self, triggerType, job, timeDiff):

        ex = False

        if not triggerType in job or not job[triggerType]:
            if triggerType == "disconnectAction":
                ex = self.akitaProcDirectory + job['ip'] + '-disconnect.sh'
            else:
                ex = self.akitaProcDirectory + job['ip'] + '-reconnect.sh'
        else:
            ex = job[triggerType]

        triggerThread = threading.Thread(target=self.executeAction, args=[job, ex, timeDiff])
        triggerThread.start()

    def executeAction(self, job, ex, timeDiff):
        fire = '%s -t %s' % (ex, str(timeDiff))
        if os.path.isfile(ex):
            print "Firing action for " + job['ip'] + ' : ' + fire
            os.system(fire + ' > /dev/null 2>&1 &')
        else:
            print "Not firing " + ex + ' - file does not exist'

ak = akita()
ak.main()
