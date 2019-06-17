#!/bin/bash

# File used to save object copy state locally
STATE_FILE=copy_status.json

# Default interval between copy status checks, in seconds
DEFAULT_INTERVAL=60

# Limit of allowed outstanding copy operations
LIMIT_OUTSTANDING=10000

function usage(){
    echo This script facilitates the one-time replication of an OCI Object Storage
    echo bucket using Object Storage\'s Cross Region Copy functionality.
    echo
    echo The following command line options are supported.
    echo "  --source-namespace NAMESPACE         The source namespace [REQUIRED]"
    echo "  --source-region REGION               The source region [REQUIRED]"
    echo "  --source-bucket BUCKET               The source bucket [REQUIRED]"
    echo
    echo "  --destination-namespace NAMESPACE    The destination namespace [REQUIRED]"
    echo "  --destination-region REGION          The destination region [REQUIRED]"
    echo "  --destination-bucket BUCKET          The destination bucket [REQUIRED]"
    echo
    echo "  --destination-prefix PREFIX          An optional string to preprend to"
    echo "                                       destination object names."
    echo "  --interval SECONDS                   The number of seconds between copy"
    echo "                                       status checks. Default: $DEFAULT_INTERVAL"
    echo "  --resume                             Resumes a previous bucket"
    echo "                                       replication using an existing"
    echo "                                       copy_status.json file"
    echo
    echo NOTES:
    echo "  - The source and destination namespace may be the same."
    echo "  - The source and destination region may be the same."
    echo "  - The source and destination bucket may be the same IF the"
    echo "    --destination-prefix PREFIX option is used."
}

function parse_options(){
    while true; do
        case "$1" in
            --source-namespace | -sn)
                source_namespace="$2"
                shift 2
                ;;
            --source-region | -sr)
                source_region="$2"
                shift 2
                ;;
            --source-bucket | -sb)
                source_bucket="$2"
                shift 2
                ;;
            --destination-namespace | -dn)
                destination_namespace="$2"
                shift 2
                ;;
            --destination-region | -dr)
                destination_region="$2"
                shift 2
                ;;
            --destination-bucket | -db)
                destination_bucket="$2"
                shift 2
                ;;
            --destination-prefix | -dp)
                destination_prefix="$2"
                shift 2
                ;;
            --interval | -i)
                interval="$2"
                shift 2
                ;;
            --help | -h)
                usage
                exit
                ;;
            --resume | -r)
                resume="true"
                shift 1
                ;;
            -*)
                echo Unknown option: $1
                echo
                usage
                exit
                ;;
            *)
                break
                ;;
        esac
    done

    if [[ -z "$source_namespace" ]] || \
            [[ -z "$source_region" ]] || \
            [[ -z "$source_bucket" ]] || \
            [[ -z "$destination_namespace" ]] || \
            [[ -z "$destination_region" ]] || \
            [[ -z "$destination_bucket" ]]; then

        echo One or more required arguments is missing.
        echo
        usage
        exit
    fi

    if [[ "$source_namespace" = "$destination_namespace" ]] && \
            [[ "$source_region" = "$destination_region" ]] && \
            [[ "$source_bucket" = "$destination_bucket" ]] && \
            [[ -z "$destination_prefix" ]]; then

        echo Using the same bucket for source and destination is allowed but
        echo requires use of --destination-prefix PREFIX.
        echo
        usage
        exit
    fi

    if [[ -z "$interval" ]]; then
        interval=$DEFAULT_INTERVAL
    fi
}

function check_prerequisites(){
    if ! which jq >/dev/null 2>&1; then
        echo The 'jq' tool must be installed.
        exit
    fi

    if ! which oci >/dev/null 2>&1; then
        echo The OCI CLI must be installed.
        exit
    fi

    if ! oci os object copy --help >/dev/null 2>&1; then
        echo The installed version of the OCI CLI does not support Cross Region Copy. Please upgrade.
        exit
    fi
}

function check_iam_policy(){
    # Acceptable policies look like one of the following:
    # - allow service objectstorage-<source region> to manage objects in tenancy
    # - allow service objectstorage-<source region> {OBJECT_READ, \
    #       OBJECT_CREATE, OBJECT_OVERWRITE, OBJECT_INSPECT, OBJECT_DELETE} in tenancy

    output=$(oci iam policy list --all --region $destination_region | \
            jq '.data | map(.statements) | .[] | .[]')

    if [[ $? -ne 0 ]]; then
        echo Error executing OCI CLI.
        echo $output
        exit
    fi

    local found=false

    while read line; do
        local line=$(echo $line | tr A-Z a-z | sed -e 's/  */ /g' -e 's/\"//g' -e 's/ to / /g')

        if `echo $line | grep -qiE "^allow service objectstorage-$source_region manage (objects|object-family) in tenancy\$"`; then
            found=true

        elif `echo $line | grep -qiE "^allow service objectstorage-$source_region \{[^\}]+\} in tenancy\$"`; then
            if `echo $line | grep -qi 'OBJECT_READ'` && \
                   `echo $line | grep -qi 'OBJECT_CREATE'` && \
                   `echo $line | grep -qi 'OBJECT_OVERWRITE'` && \
                   `echo $line | grep -qi 'OBJECT_INSPECT'` && \
                   `echo $line | grep -qi 'OBJECT_DELETE'` ; then
                found=true
            fi
        fi
    done < <(echo $output | grep -oE '"[^"]+"')

    if [[ $found = true ]]; then
        return 0
    else
        return 1
    fi
}

function list_objects_in_bucket(){
    local namespace=$1
    local bucket=$2

    output=$(oci os object list --all --namespace $namespace --bucket-name $bucket 2>&1)

    if [[ $? -ne 0 ]]; then
        echo Error executing OCI CLI.
        echo $output
        exit
    else
        echo $output | jq --compact-output '.data | .[]'
    fi
}

function request_copy(){
    local src_namespace=$1
    local src_region=$2
    local src_bucket=$3
    local object=$4
    local dst_namespace=$5
    local dst_region=$6
    local dst_bucket=$7
    local dst_prefix=$8

    output=$(oci os object copy --namespace $src_namespace --region $src_region \
            --bucket-name $src_bucket --source-object-name "$object" \
            --destination-namespace $dst_namespace --destination-region $dst_region \
            --destination-bucket $dst_bucket \
            --destination-object-name "$dst_prefix$object" 2>&1)

    if [[ $? -ne 0 ]]; then
        local status=$(echo $output | sed -e 's/^ServiceError://' | jq .status)
        echo $status
    else
        state=$(echo $output | jq --compact-output '. + {"status": "REQUESTED"}')
        set_state_for_object "$object" "$state"
    fi
}

function get_state_file_for_object(){
    local file=$1

    echo $STATE_FILE.$(echo $file | md5sum - | cut -c1-2)
}

function get_state_for_object(){
    local file=$1

    local state_file=$(get_state_file_for_object $file)

    if [[ ! -f $state_file ]]; then
        echo State file, $state_file, does not exist. Creating.
        touch $state_file
        # return no data since no saved state exists
        echo

    else
        data=$(jq --compact-output '."'"$file"'"' < $state_file)
        echo $data
    fi
}

function set_state_for_object(){
    local file=$1
    local state=$2
    local data=''

    local state_file=$(get_state_file_for_object $file)

    if [[ -f $state_file ]]; then
        data=$(cat $state_file 2>/dev/null)
    fi

    local update=$(echo $state | jq --compact-output '. + {"object": "'"$file"'"}')

    if `echo $data | grep -E '\S' >/dev/null`; then
        echo $data | jq '. + {"'"$file"'": '"$update"'}' > $state_file
    else
        echo '{}' | jq '. + {"'"$file"'": '"$update"'}' > $state_file
    fi
}

function list_unrequested_copies_from_state(){
    cat $STATE_FILE* | jq --compact-output 'map(select(.status == "KNOWN")) | map({"object": .object}) | .[]'
}

function get_unrequested_copies_count(){
    local count=0

    if `find $STATE_FILE* >/dev/null 2>&1`; then
        for N in $(cat $STATE_FILE* | jq 'map(select(.status == "KNOWN")) | length'); do
            count=$(( $N + $count ))
        done
    fi

    echo $count
}

function list_outstanding_requests_from_state(){
    if `find $STATE_FILE* >/dev/null 2>&1`; then
        cat $STATE_FILE* | jq --compact-output 'map(select(.status == "REQUESTED")) | map({"object": .object, "request": ."opc-work-request-id"}) | .[]'
    fi
}

function get_outstanding_work_request_count(){
    local count=0

    if `find $STATE_FILE* >/dev/null 2>&1`; then
        for N in $(cat $STATE_FILE* | jq 'map(select(.status == "REQUESTED")) | length'); do
            count=$(( $N + $count ))
        done
    fi

    echo $count
}

function get_work_request_status(){
    local region=$1
    local request=$2

    output=$(oci os work-request get --region $region --work-request-id $request | jq '.data.status' 2>/dev/null)
    echo $output
}

function main(){
    parse_options "$@"

    check_prerequisites

    if ! check_iam_policy; then
        echo "Required IAM policy is not present."
        exit
    fi

    if [[ "$resume" != "true" ]]; then
        echo "Getting list of objects from source bucket ($source_bucket)"

        while read item; do
            object=$(echo $item | jq --raw-output '.name')

            state=$(echo '{}' | jq --compact-output '. + {"status": "KNOWN"}')
            set_state_for_object "$object" "$state"
        done < <(list_objects_in_bucket $source_namespace $source_bucket)
    else
        echo "Resuming previously started bucket replication"

        if `find $STATE_FILE* >/dev/null 2>&1`; then
            echo State file does not exist but is required when --resume is used.
            echo Exiting.
            exit
        fi
    fi

    while true; do
        if [[ "$(get_outstanding_work_request_count)" -gt 0 ]]; then
            echo Determining copy status.

            while read request; do
                object=$(echo $request | jq --compact-output '.object' | sed -e 's/\"//g')
                request_id=$(echo $request | jq --compact-output '.request' | sed -e 's/\"//g')
                status=$(get_work_request_status $source_region $request_id)

                if [[ "$status" = \"COMPLETED\" ]] || \
                        [[ "$status" = \"FAILED\" ]] || \
                        [[ "$status" = \"CANCELED\" ]]; then
                    current_state=$(get_state_for_object "$object")
                    new_state=$(echo $current_state | jq --compact-output '. + {"status": '$status'}')

                    set_state_for_object "$object" "$new_state"
                    echo "  $object has completed"
                else
                    requests_outstanding=true
                fi
            done < <(list_outstanding_requests_from_state)
        fi

        if [[ "$(get_unrequested_copies_count)" -gt 0 ]]; then
            echo "Sending copy requests"

            while read request; do
                if [[ $(get_outstanding_work_request_count) -ge $LIMIT_OUTSTANDING ]]; then
                    echo "Outstanding copy request limit ($LIMIT_OUTSTANDING) reached."
                    break
                fi

                object=$(echo $request | jq --compact-output '.object' | sed -e 's/\"//g')

                local status=$(request_copy $source_namespace $source_region $source_bucket "$object" \
                        $destination_namespace $destination_region $destination_bucket \
                        "$destination_prefix")

                if [[ "$status" -ge 400 ]] && [[ "$status" -le 499 ]]; then
                    echo Received $status error from API, will wait before making additional requests.
                    break
                fi
            done < <(list_unrequested_copies_from_state)
        fi

        if [[ "$(get_unrequested_copies_count)" -eq 0 ]] && \
                [[ "$(get_outstanding_work_request_count)" -eq 0 ]]; then
            break
        else
            echo Waiting $interval seconds before checking status.
            sleep $interval
        fi
    done
}

# Only execute main() if the script is being run and not sourced
if ! return >/dev/null 2>&1; then
    main "$@"
fi
