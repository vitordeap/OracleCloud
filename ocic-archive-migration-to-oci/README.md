# OCI-C Archive to OCI Migration Script

This set of scripts can be used to migrate data from an OCI-C archive
container to an OCI bucket. Specifically, they perform the following actions:
 - Restore all of the objects in an OCI-C Archive Container
 - Check the status of OCI-C archive restore operations
 - Copy all objects from an OCI-C Archive Container to an OCI Bucket

## Prerequisites

In order to use these scripts, you must:
 - Have appropriate credentials and access in OCI-C and OCI
 - Have a working python installation
 - If you want to copy objects from OCI-C to OCI, you must have rclone
   installed, however no existing rclone configuration is required

## Using These Scripts

To use these scripts, first edit the archive-restore.py script to
specify your OCI-C authentication information. It is also possible to
specify how long objects should remain restored and available
before being archived again. Make sure this time is long enough for
you to perform the copy operation.

Next, execute the archive-restore.py script, specifying
--request-restore and the name of the OCI-C container holding the
objects you would like to restore. For example, the output shown below
is requesting restoration of objects in an OCI-C container named
'archive-container'.

    $ ./archive-restore.py --request-restore archive-container
    Getting objects from container: 'archive-container'
      - Got 111 objects
      - Object names saved to 'archive_restore_archive-container.state'
    Requesting object restores
      - Completed request for '1mb-9'
      - Completed request for '1mb-8'
      - Completed request for '1mb-1'
      - Completed request for '1mb-3'
    ...

The OCI-C object restoration process takes time to complete. You can
use the archive-restore.py script to see which objects are restored
and available for copy or use. This is shown below using the OCI-C
container named 'archive-container'. 

    $ ./archive-restore.py --list-objects archive-container
    Getting objects from 'archive-container' that are restored completely
      - 1mb-9, expires at Thu Aug 30 00:08:06 2018
      - 1mb-8, expires at Thu Aug 30 00:08:06 2018
      - 1mb-1, expires at Thu Aug 30 00:08:06 2018
      - 1mb-3, expires at Thu Aug 30 00:08:07 2018
      - 1mb-2, expires at Thu Aug 30 00:08:07 2018
      - 1mb-5, expires at Thu Aug 30 00:08:07 2018
    ...

Once objects have been restored, you can use the copy.sh script to
perform the copy from the OCI-C container to an OCI bucket. Although
this step can be performed on any host with access to OCI-C and OCI
object stores, it is best to run copy.sh on a compute instance in
either OCI or OCI-C. Before attempting to run copy.sh, you must edit
it to provide your OCI-C and OCI authentication credentials and
container and bucket names.

**Please Note:** The OCI configuration in copy.sh uses the OCI Object
Storage S3 Compatible API and must be provided with S3 credentials
obtained from the Identity section of OCI Console.

copy.sh uses the archive-restore.py script to get a list of files that
have been restored and can be copied. Additionally, copy.sh uses
rclone to perform the actual copy operation. rclone will not overwrite
files that have already been copied. It is therefore possible to run
copy.sh repeatedly in order to copy files from OCI-C to OCI as they
are restored. However, while rclone will not overwrite the files, it
will interact with the OCI-C API which may incur usage charges.

Running copy.sh takes no command line arguments. An example is shown
below.

    $ ./copy.sh
    Copying OCI-C:archive-container/1mb-9 -> OCI:ocic-archive-migration-test/1mb-9
    Copying OCI-C:archive-container/1mb-8 -> OCI:ocic-archive-migration-test/1mb-8
    Copying OCI-C:archive-container/1mb-1 -> OCI:ocic-archive-migration-test/1mb-1
    Copying OCI-C:archive-container/1mb-3 -> OCI:ocic-archive-migration-test/1mb-3
    Copying OCI-C:archive-container/1mb-2 -> OCI:ocic-archive-migration-test/1mb-2
    ...

## Limitations

These scripts are working examples of how to perform OCI-C Archive to
OCI migrations. However, they are not perfect and do have some
limitations. The known limitations of these scripts are:
 - The scripts do some local caching of OCI-C archive object state,
   but do use the OCI-C APIs frequently. When many objects are
   involved, this may produce non-negligible costs. 
 - These scripts do not currently perform any verification that
   objects were copied without errors to OCI. This is a step best
   performed by the user.

## Getting Help

Please email object_storage_help_ww_grp@oracle.com to get support with
these scripts. 
