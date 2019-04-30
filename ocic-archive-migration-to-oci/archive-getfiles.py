#!/usr/bin/env python

import argparse
import pickle
import re
import requests
import sys
import time

# This URL comes from the OCI-C Object Storage Console

authUrl = ''

# Authentication information

authIdentityDomain = ''
authUsername = ''
authPassword = ''

# How many days should restored objects be available, must be > 1

daysAvailable = 3

#
# Shouldn't need to edit below here
#

def getAuthTokenAndStorageUrl():
    headers = {
                'X-Storage-User': 'Storage-%s:%s' % (authIdentityDomain, authUsername),
                'X-Storage-Pass': authPassword
              }

    response = requests.get(authUrl, headers=headers)
    response.raise_for_status()

    return (response.headers['X-Auth-Token'], response.headers['X-Storage-Url'])

def getContainers():
    # curl -s -S -X GET -H "X-Auth-Token: <token>" <storage url>

    url = '%s' % (swiftUrl)
    headers = {'X-Auth-Token': token}

    response = requests.get(url, headers=headers)
    response.raise_for_status()

    data = [item for item in response.text.split('\n') if item != '']
    return data

def getObjectsInContainer(container):
    # curl -s -S -X GET -H "X-Auth-Token: <token>" <storage url>/mycontainer

    url = '%s/%s' % (swiftUrl, container)
    headers = {'X-Auth-Token': token}

    response = requests.get(url, headers=headers)
    response.raise_for_status()

    data = [item for item in response.text.split('\n') if item != '']
    return data

def requestRestore(container, obj):
    # curl -v -X POST -H "X-Auth-Token: <token>" <storage url>/container/object?restore

    # Archiving not part of Swift standard, so at /v0 not /v1
    swiftUrl_v0 = re.sub(r'/v1/', r'/v0/', swiftUrl)

    url = '%s/%s/%s?restore' % (swiftUrl_v0, container, obj)
    headers = {
                'X-Auth-Token': token,
                'X-Archive-Restore-Expiration': daysAvailable
              }

    response = requests.post(url, headers=headers)
    response.raise_for_status()

    data = {
                'X-Archive-Restore-Tracking': response.headers['X-Archive-Restore-Tracking'],
                'X-Archive-Restore-JobId': response.headers['X-Archive-Restore-JobId']
           }

    return data

def checkObjectRestoreStatus(container, obj):
    # curl -v -X GET -H "X-Auth-Token: <token>" <storage url>/container?jobs&jobid=<job id>

    url = state['%s/%s' % (container, obj)]['X-Archive-Restore-Tracking']
    headers = {'X-Auth-Token': token}

    response = requests.get(url, headers=headers)
    response.raise_for_status()

    return response.json()

def loadState():
    try:
        with open(restoreState, 'r') as state_file:
            return pickle.load(state_file)
    except IOError:
        return {}

def saveState():
    with open(restoreState, 'w') as state_file:
        pickle.dump(state, state_file)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Restore Objects from OCI-C Archive')
    parser.add_argument('--request-restore', dest='container_to_restore',
            help='Request restores for all objects in a container')
    parser.add_argument('--list-objects', dest='container_to_list',
            help='List objects that have been completely restored')
    parser.add_argument('-q', '--quiet', action='store_true',
            help='Limit output to aid use with other utilities')

    args = parser.parse_args()

    if args.container_to_restore is not None and args.container_to_list is not None:
        print "Please only include one of --request-restore or --list-objects"
        sys.exit()

    # Request restores for objects in container
    if args.container_to_restore:
        containerToRestore = args.container_to_restore
        restoreState = 'archive_restore_%s.state' % (containerToRestore)
        state = loadState()
        token, swiftUrl = getAuthTokenAndStorageUrl()

        if not args.quiet:
            print "Getting objects from container: '%s'" % (containerToRestore)
        objects = getObjectsInContainer(containerToRestore)
        if not args.quiet:
            print "  - Got %s objects" % (len(objects))

        # TODO: We should skip objects that are already in the process of
        # being restored

        for obj in objects:
            state['%s/%s' % (containerToRestore, obj)] = {'state': 'not-started'}

        saveState()

        if not args.quiet:
            print "  - Object names saved to '%s'" % (restoreState)
            print "Requesting object restores"

        for obj in state.keys():
            container, object_name = obj.split('/')
            data = requestRestore(container, object_name)

            for key in data.keys():
                state[obj][key] = data[key]

            state[obj]['state'] = 'restore-in-progress'
            saveState()

            if not args.quiet:
                print "  - Completed request for '%s'" % (object_name)
            else:
                print "%s" % (object_name)

    # List objects that are restored and ready to be copied
    elif args.container_to_list:
        containerToRestore = args.container_to_list
        restoreState = 'archive_restore_%s.state' % (containerToRestore)
        state = loadState()
        token, swiftUrl = getAuthTokenAndStorageUrl()

        if not args.quiet:
            print "Removing restored objects from local state info that have expired."

        updated_state = {}
        for obj in state.keys():
            if state[obj].get('expires') and time.time() > state[obj]['expires']:
                if not args.quiet:
                    print "  - %s, restore expired"
            else:
                updated_state[obj] = state[obj]

        state = updated_state

        if not args.quiet:
            print "Getting objects from '%s' that are restored completely" % (containerToRestore)

        for obj in state.keys():
            container, object_name = obj.split('/')

            if state[obj]['state'] == 'restore-completed':
                if not args.quiet:
                    print "  - %s, expires at %s" % (object_name,
                            time.ctime(state[obj]['expires']))
                else:
                    print "%s" % (object_name)
                continue

            status = checkObjectRestoreStatus(container, object_name)

            if status['completed'] is True:
                state[obj]['state'] = 'restore-completed'
                state[obj]['expires'] = float(status['jobDetails']['objectExpiration']) / 1000
                saveState()

                if not args.quiet:
                    print "  - %s, expires at %s" % (object_name,
                            time.ctime(state[obj]['expires']))
                else:
                    print "%s" % (object_name)

    else:
        print "Please include one of --request-restore or --list-objects"
        sys.exit()
