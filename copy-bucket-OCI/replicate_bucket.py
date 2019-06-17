#!/usr/bin/env python

import cPickle as pickle
import time

import oci

#
# Edit these values to configure the script
#

profile_name = 'OCITSAMMUT'

source_namespace = 'ocitsammut'
source_region = 'us-ashburn-1'
source_bucket = 'repl_source_small'

destination_namespace = 'ocitsammut'
destination_region = 'us-ashburn-1'
destination_bucket = 'repl_destination'

#
# Should not need to edit below here
#

interval = 60
state_file = 'copy_status'

config = oci.config.from_file(profile_name=profile_name)
object_storage_client = oci.object_storage.ObjectStorageClient(config)

data = {}

def get_bucket_compartment(ns, bucket):
    return object_storage_client.get_bucket(ns, bucket).data.compartment_id

def list_objects(ns, bucket):
    return [x.name for x in oci.pagination.list_call_get_all_results(
            object_storage_client.list_objects, ns, bucket).data.objects]

def set_state_for_object(object_, state, persist=True):
    global data
    data[object_] = state

    if persist:
        with open(state_file, 'wb') as sf:
            pickle.dump(data, sf, protocol=pickle.HIGHEST_PROTOCOL)

    return data[object_]

def save_all_state():
    with open(state_file, 'wb') as sf:
        pickle.dump(data, sf, protocol=pickle.HIGHEST_PROTOCOL)

def get_state_for_object(object_):
    return data[object_]

def list_outstanding_requests_from_state():
    return [x for x in data.keys() if data[x].get('status') == 'REQUESTED']

def get_outstanding_work_request_count():
    return len(list_outstanding_requests_from_state())

def list_unrequested_copies_from_state():
    return [x for x in data.keys() if data[x].get('status') == 'KNOWN']

def get_unrequested_copies_count():
    return len(list_unrequested_copies_from_state())

def copy_object(src_ns, src_r, src_b, src_o, dst_ns, dst_r, dst_b, dst_o):
    copy_request = oci.object_storage.models.copy_object_details.CopyObjectDetails()
    # src_r not currently used here
    copy_request.source_object_name = src_o
    copy_request.destination_namespace = dst_ns
    copy_request.destination_region = dst_r
    copy_request.destination_bucket = dst_b
    copy_request.destination_object_name = dst_o

    return object_storage_client.copy_object(src_ns, src_b, copy_request) 

def update_all_work_requests_status(ns, bucket):
    work_requests = {}
    for wr in oci.pagination.list_call_get_all_results(
            object_storage_client.list_work_requests, 
            get_bucket_compartment(ns, bucket)).data:

        if wr.operation_type == "COPY_OBJECT" and \
                wr.resources[0].metadata['OBJECT'] in data.keys():

            work_requests[wr.id] = wr

    for object_ in data.keys():
        state = get_state_for_object(object_)
        state['status'] = work_requests[state['work-request-id']].status

        set_state_for_object(object_, state, persist=False)

        if state['status'] in ('COMPLETED', 'FAILED', 'CANCELED'):
            print("  %s has completed with status %s" % (object_, state['status']))

    save_all_state()

def main():
    print("Getting list of objects from source bucket (%s)" % (source_bucket))
    for object_ in list_objects(source_namespace, source_bucket):
        set_state_for_object(object_, {'status': 'KNOWN'}, persist=False)

    save_all_state()

    while True:
        if get_outstanding_work_request_count() > 0:
            print("Determining copy status")
            update_all_work_requests_status(source_namespace, source_bucket)
                
        if get_unrequested_copies_count() > 0:
            print("Sending copy requests")

            for object_ in list_unrequested_copies_from_state():
                state = get_state_for_object(object_)

                try:
                    response = copy_object(source_namespace, source_region, source_bucket, object_,
                            destination_namespace, destination_region, destination_bucket, object_)

                except Exception:
                    print("  Received %s error from API, will wait before making additional requests." % (
                            response.status))
                    time.sleep(interval)
                    continue

                state['work-request-id'] = response.headers.get('opc-work-request-id')
                state['status'] = 'REQUESTED'
                set_state_for_object(object_, state)

        if get_outstanding_work_request_count() == 0 and \
                get_unrequested_copies_count() == 0:
            break

        print("Waiting %s seconds before checking status." % (interval))
        time.sleep(interval)

if __name__ == '__main__':
    main()
