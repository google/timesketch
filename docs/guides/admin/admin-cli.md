---
hide:
  - footer
---
## tsctl

tsctl is a command-line tool for managing and interacting with a Timesketch instance. It allows users to create and delete sketches, add and remove data sources, manage users and groups, and perform various other tasks.

Its commands can be accessed by running tsctl followed by the desired subcommand. For example, to list all the available sketches in a Timesketch instance, tsctl list-sketches can be run.

### Config

The `--config` parameter in tsctl is used to specify the location of a configuration file that contains settings for tsctl. This configuration file can specify default values for various tsctl options, such as the `hostname` and `port` of the Timesketch server, the `username` and `password` to use when authenticating with the server, and other settings.

Parameters:

```shell
--config / -c (optional)
```

Example

```shell
tsctl run -c /etc/timesketch/timesketch.conf
```

### version

Displays the version of Timesketch installed on the system

Example

```shell
tsctl version
Timesketch version: 20210602
```

### info

Displays various useful version information used on the system Timesketch is installed on.

Example

```shell
tsctl info
Timesketch version: 20210602
plaso - psort version 20220930
Node version: v14.20.1
npm version: 6.14.17
yarn version: 1.22.19
Python version: Python 3.10.6
pip version: pip 22.0.2 from /usr/lib/python3/dist-packages/pip (python 3.10)
```

### User management

#### Adding users

tsctl provides a subcommand for creating users in a Timesketch instance. This subcommand is called `create-user`, and it allows you to specify the `username`, `password`, and other details for the user you want to create.

To use the `create-user` subcommand, you would run `tsctl create-user` followed by the desired options and arguments. For example, to create a user with the username "john" and the password "123456", you could run the following command: `tsctl create-user john --password 123456`.

Once the user is created, they will be able to log in to the Timesketch instance using their username and password. You can then use the `list-users` subcommand to verify that the user was created successfully.

Command:

```shell
tsctl create-user [OPTIONS] USERNAME
```

Parameters:

```shell
--password / -p (optional)
```

Example

```shell
tsctl create-user foo
tsctl create-user foo --password bar
```

#### Change user password

To change a user password, the `create-user` command can be used, as it is checking if the user exists if yes it will update the user.

This command would change the password of the user with the specified username to the new password provided. The user will then be able to log in to the Timesketch instance using their new password.

Command:

```shell
tsctl create-user [OPTIONS] USERNAME
```

Parameters:

```shell
--password / -p (optional)
```

Example

```shell
tsctl create-user foo
tsctl create-user foo --password bar
```

#### Removing users

tsctl provides a subcommand for disabling users in a Timesketch instance. This subcommand is called `disable-user`, and it allows you to specify the username or user ID of the user you want to disable.

To use the `disable-user` subcommand, you would run `tsctl disable-user` followed by the desired options and arguments. For example, to disable a user with the username "john", you could run the following command:
`tsctl disable-user john`.

This command would disable the user with the specified username, preventing them from logging in to the Timesketch instance. However, their user account will still exist in the system, and you can use the enable-user subcommand to re-enable their account at any time.

Disabled users are not removed from the system, but marked as disabled.
The current implementation is not complete. Disabled users will still show up for other commands.

Command:

```shell
tsctl disable_user
tsctl enable_user
```


Example

```shell
tsctl disable_user foo
tsctl enable_user foo
```

#### List users

tsctl provides a subcommand for listing the users in a Timesketch instance. This subcommand is called `list-users`, and it allows you to view a list of the users in the system, along with their username, user ID, and other details.

To use the `list-users` subcommand, you would run `tsctl list-users` followed by the desired options and arguments. For example, to list all the users in the Timesketch instance, you could run the following command: `tsctl list-users`.

This command would display a list of the users in the Timesketch instance, along with their username and other details.

Example

```shell
tsctl list-users
foo
bar
dev (admin)
```

Adding `--status` will add the status of the user to the output.

Example
```shell
tsctl list-users --status
dev (active: True)
admin (active: True)
foobar2 (active: True)
foobar (active: False)
```

#### Make admin

tsctl provides a subcommand for granting administrator privileges to a user in a Timesketch instance. This subcommand is called `make-admin`, and it allows you to specify the username of the user you want to grant administrator privileges to.

To use the `make-admin` subcommand, you would run `tsctl make-admin` followed by the desired options and arguments. For example, to grant administrator privileges to a user with the username "john", you could run the following command: `tsctl make-admin john`

This command would grant the user with the specified username administrator privileges.

Once a user has administrator privileges, they will be able to perform a wider range of tasks in the Timesketch instance. You can use the `list-users` subcommand to verify that the user has been granted administrator privileges successfully.

You can use `tsctl revoke-admin` to revoke admin privileges.

#### Revoke admin

tsctl provides a subcommand for revoking administrator privileges from a user in a Timesketch instance. This subcommand is called `revoke-admin`, and it allows you to specify the username of the user you want to revoke administrator privileges from.

To use the `revoke-admin` subcommand, you would run `tsctl revoke-admin` followed by the desired options and arguments. For example, to revoke administrator privileges from a user with the username "john", you could run the following command: `tsctl revoke-admin john`

This command would revoke the administrator privileges of the user with the specified username.

Once a user's administrator privileges are revoked, they will no longer be able to perform tasks that require administrator privileges in the Timesketch instance. You can use the `list-users` subcommand to verify that the user's administrator privileges have been revoked successfully.

### Group management

#### Adding groups

tsctl provides a subcommand for adding groups in a Timesketch instance. This subcommand is called `create-group`, and it allows you to specify the name of the group you want to add.

To use the `create-group` subcommand, you would run `tsctl create-group` followed by the desired options and arguments. For example, to add a group called "analysts", you could run the following command: `tsctl create-group analysts`
This command would create a new group with the specified name. Once the group is created, you can use the `list-groups` subcommand to verify that the group was added successfully.

You can also use the `add-user-to-group` subcommand to add users to the group you have created. This allows you to manage the members of the group, and control which users have access to the sketches and data sources associated with the group.

Command:

```shell
tsctl create-group [OPTIONS] GROUP_NAME
```


#### Removing groups

Not yet implemented.

#### Managing group membership

##### List groups

To list groups, use `tsctl list-groups`. This can be extended  to show the members of a group using `tsctl list-groups --showmembership`

Example:

```bash
tsctl list-groups --showmembership
foobar:
foobar-group:foobar2,foobar
```

##### Add a user to a group

tsctl provides a subcommand for adding users to a group in a Timesketch instance. This subcommand is called `add-group-member`, and it allows you to specify the username of the user you want to add to the group, as well as the name of the group you want to add the user to.

To use the `add-group-member` subcommand, you would run `tsctl add-group-member` followed by the desired options and arguments. For example, to add a user with the username "john" to a group called "analysts", you could run the following command: `tsctl add-group-member --username john analysts`.
This command would add the user with the specified username to the group with the specified name.

Once the user is added to the group, they will be able to access the sketches and data sources associated with the group, based on the permissions granted to the group. You can use the `list-groups` subcommand to verify that the user was added to the group successfully.

Command:

```shell
tsctl add-group-member [OPTIONS] GROUP_NAME
```

Example:

```shell
tsctl add-group-member --username john analysts
```

##### Removing a group member

tsctl provides a subcommand for removing users from a group in a Timesketch instance. This subcommand is called `remove-group-member`, and it allows you to specify the username of the user you want to remove from the group, as well as the name of the group you want to remove the user from.

To use the `remove-group-member` subcommand, you would run `tsctl remove-group-member` followed by the desired options and arguments. For example, to remove a user with the username "john" from a group called "analysts", you could run the following command: `tsctl remove-group-member --username john analysts`

This command would remove the user with the specified username from the group with the specified name.

Once the user is removed from the group, they will no longer be able to access the sketches and data sources associated with the group. You can use the list-groups subcommand to verify that the user was removed from the group successfully.


Command:

```shell
tsctl remove-group-member [OPTIONS] GROUP_NAME
```

Example:

```shell
tsctl remove-group-member --username john analysts
```

### add_index

Create a new Timesketch searchindex.

Command:

```shell
tsctl add_index
```

Parameters:

```shell
--name / -n
--index / -i
--user / -u
```

Example:

```shell
tsctl add_index -u user_foo -i test_index_name -n sample
```

### routes

tsctl provides a subcommand for displaying the available API routes in a Timesketch instance. This subcommand is called `routes`, and it allows you to view a list of the API routes that are available in the Timesketch instance, along with their URL and description.

To use the routes subcommand, you would run `tsctl routes` followed by the desired options and arguments. For example, to list all the available API routes in the Timesketch instance, you could run the following command: `tsctl routes`.
This command would display a list of the available API routes in the Timesketch instance, along with their URL and description.

Example:

```bash
tsctl routes
Endpoint                           Methods            Rule
---------------------------------  -----------------  -------------------------------------------------------------------------
aggregationexploreresource         POST               /api/v1/sketches/<int:sketch_id>/aggregation/explore/
```

### db

tsctl provides a subcommand for managing the database in a Timesketch instance. This subcommand is called `db`, and it allows you to perform various operations on the Timesketch database, such as creating the database tables, initializing the database schema, and migrating the database to the latest version.

To use the `db` subcommand, you would run `tsctl db` followed by the desired options and arguments. For example, to initialize the database schema in the Timesketch instance, you could run the following command:
`tsctl db init`

Command:

```shell
tsctl db
```

Example

```bash
tsctl db --help
Usage: tsctl db [OPTIONS] COMMAND [ARGS]...

  Perform database migrations.

Options:
  --help  Show this message and exit.

Commands:
  branches   Show current branch points
  current    Display the current revision for each database.
  downgrade  Revert to a previous version
  edit       Edit a revision file
  heads      Show current available heads in the script directory
  history    List changeset scripts in chronological order.
  init       Creates a new migration repository.
  merge      Merge two revisions together, creating a new revision file
  migrate    Autogenerate a new revision file (Alias for 'revision...
  revision   Create a new revision file.
  show       Show the revision denoted by the given symbol.
  stamp      'stamp' the revision table with the given revision; don't...
  upgrade    Upgrade to a later version
```


#### Upgrade DB After Schema Change

After changing the schema for the database a revision file needs to be generated.

(temporary solution)
Before doing the database migration you'll need to modify the file `timesketch/models/__init__.py`:

```python

def init_db():
...
        BaseModel.metadata.create_all(bind=engine)
```

This line needs to be commented out, eg:

```python

def init_db():
...
        #BaseModel.metadata.create_all(bind=engine)
```

Then inside the timesketch container, to generate the file use the command:

```shell
cd /usr/local/src/timesketch/timesketch
tsctl db stamp head
tsctl db upgrade
```

This makes sure that the database is current. Then create a revision file:

```shell
tsctl db migrate -m "<message>"
```

Once the migration is done, remove the comment to re-enable the line in `timesketch/models/__init.py`.

##### Troubleshooting Database Schema Changes

If the migration file is not created, which could be an indication that the schema change
is not detected by the automation one can create an empty revision file:

```shell
tsctl db revision
```

And then fill in the blanks, see examples of changes in `timesketch/migrations/versions/*_.py`.

### Drop database

Will drop all databases.

Command:

```shell
tsctl drop_db
```

### search_template

Export/Import search templates to/from file.

Command:

```shell
tsctl search_template
```

Parameters:

```shell
--import / -i
--export / -e
```

import_location: Path to the yaml file to import templates.
export_location: Path to the yaml file to export templates.

### import

Creates a new Timesketch timeline from a file. Supported file formats are: plaso, csv and jsonl.

Command:

```shell
tsctl import
```

Parameters:

```shell
--file / -f
--sketch_id / -s      (optional)
--username / -f       (optional)
--timeline_name / -n  (optional)
```

The sketch id is inferred from the filename if it starts with a number. The timeline name can also be generated from the filename if not specified.

### similarity_score

Command:

```shell
tsctl similarity_score
```

### Sketch

#### sketch-info Get information about a sketch

Displays detailed information about a specific sketch.

This command retrieves and displays comprehensive information about a
Timesketch sketch, including:

- **Sketch Details:** The sketch's ID and name.
- **Active Timelines:** A table listing the active timelines within the
  sketch, including their search index ID, index name, creation date,
  user ID, description, status, timeline name, and timeline ID.
- **Sharing Information:** Details about users and groups with whom the
  sketch is shared.
- **Sketch Status:** The current status of the sketch (e.g., "ready",
  "archived").

```shell
tsctl sketch-info
```

Example:

```shell
Sketch 1 Name: (aaa)
searchindex_id index_name                       created_at                 user_id description             status timeline_name           timeline_id
1              3e062029b52f4e1a8a103488b99bc2b3 2025-03-18 14:49:52.402364 1       my_file_with_a_timeline ready  my_file_with_a_timeline 2
1              3e062029b52f4e1a8a103488b99bc2b3 2025-03-18 16:21:07.707528 1       evtx_part               ready  evtx_part               3
1              3e062029b52f4e1a8a103488b99bc2b3 2025-03-21 15:24:55.935364 1       sigma_events            ready  sigma_events            10
10             9a0f22670bf74ba6884f3ba9b261bf13 2025-03-21 15:31:45.279662 1       evtx                    ready  evtx                    11
1              3e062029b52f4e1a8a103488b99bc2b3 2025-03-21 15:41:10.860161 1       sigma_eventsa           ready  sigma_eventsa           12
Shared with:
    Users: (user_id, username)
        3: bar
    Groups:
        user-group
Sketch Status: new
Sketch is public: True
Sketch Labels: ([],)
Status:
id status created_at                 user_id
1  new    2022-10-21 15:04:59.935504 None
```

### Timeline info

In some cases, logs present a OpenSearch Index id and it is not easy to find out
which Sketch that index is related to.

Therefore the following command can be used `tsctl searchindex-info`:

Displays detailed information about a specific search index. You can specify the index using either its database ID or its OpenSearch index name. 
The command shows the search index ID and name, and lists all timelines associated with the index, including their IDs, names, and associated sketch IDs and names.

```bash
# tsctl searchindex-info --searchindex_id 99
Searchindex: asd not found in database.
# tsctl searchindex-info --searchindex_id 1
Searchindex: 1 Name: sigma_events found in database.
Corresponding Timeline id: 3 in Sketch Id: 2
Corresponding Sketch id: 2 Sketch name: asdasd
# tsctl searchindex-info --index_name 4c5afdf60c6e49499801368b7f238353
Searchindex: 4c5afdf60c6e49499801368b7f238353 Name: sigma_events found in database.
Corresponding Timeline id: 3 in Sketch Id: 2
Corresponding Sketch id: 2 Sketch name: asdasd
```

If neither `searchindex_id` nor `index_name` is provided, an error message is printed. If no matching search index is found, an appropriate message is printed

### Timeline status

The `tsctl timeline-status` command allows to get or set a timeline status.
This can be useful in the following scenarios:

* Monitoring processing In large-scale investigations, timelines can take a considerable amount of time to process.
This feature allows administrators or automated scripts to monitor the processing status of timelines, ensuring that they are progressing as expected.

* Automated Status updates: Scripts can be used to automatically update the status of timelines based on the results of automated analysis or processing steps. For example, if an automated script detects a critical error during analysis, it can set the timeline status to "fail."

* Toubeshooting and Error handling: 
** Quickly identifying timelines with a "fail" status allows investigators to troubleshoot issues and re-process data if necessary.
** By monitoring the status of timelines, administrators can identify potential bottlenecks or errors in the processing pipeline.
** Set the status to `fail` is a task is stuck.

Usage:

```bash
tsctl timeline-status [OPTIONS] TIMELINE_ID
--action [get|set]
        Specify whether to get or set the timeline status.
        - "get": Retrieves the current status of the timeline.
        - "set": Sets the status of the timeline to the value specified by "--status".
        (Required)

    --status [ready|processing|fail]
        The desired status to set for the timeline.
        This option is only valid when "--action" is set to "set".
        Valid options are:
        - "ready": Indicates that the timeline is ready for analysis.
        - "processing": Indicates that the timeline is currently being processed.
        - "fail": Indicates that the timeline processing failed.
        (Required when --action is set to set)
```

Examples:
```bash
# Get the status of timeline with ID 123:
    tsctl timeline-status --action get 123

    # Set the status of timeline with ID 456 to "ready":
    tsctl timeline-status --action set --status ready 456

    # Set the status of timeline with ID 789 to "fail":
    tsctl timeline-status --action set --status fail 789

    # Try to set a status without the action set to set.
    tsctl timeline-status --status fail 789
    # This will fail and display an error message.
```

### Searchindex-status

The `tsctl searchindex-status` command allows to get or set a searchindex status.

Usage:
```
tsctl searchindex-status --help
Usage: tsctl searchindex-status [OPTIONS] SEARCHINDEX_ID

  Get or set a searchindex status

  If "action" is "set", the given value of status will be written in the
  status.

  Args:     action: get or set searchindex status.     status: searchindex
  status. Only valid choices are ready, processing, fail.

Options:
  --action [get|set]              get or set timeline status.
  --status [ready|processing|fail]
                                  get or set timeline status.
  --searchindex_id TEXT           Searchindex ID to search for e.g.
                                  4c5afdf60c6e49499801368b7f238353.
                                  [required]
  --help                          Show this message and exit.
```


Examples:
```bash
tsctl searchindex-status --action set 1 --status fail
Searchindex 1 status set to fail
To verify run: tsctl searchindex-status 1 --action get
tsctl searchindex-status --action set --status fail 1
Searchindex 1 status set to fail
To verify run: tsctl searchindex-status 1 --action get
tsctl searchindex-status 1 --action get
searchindex_id index_name                       created_at                 user_id description status
1              f609b138aa1e4c448ece6c012dcb2bab 2025-03-07 09:23:37.172143 1       #           fail
```

### Sigma

#### List Sigma rules

Lists all Sigma rules installed on a system

```shell
tsctl list-sigma-rules
```

```bash
tsctl list-sigma-rules --columns=rule_uuid,title,status
rule_uuid,title,status
['8c10509b-9ba5-4387-bf6c-e347931b646f', 'SigmaRuleTemplateTitledddd', 'experimental']
['5266a592-b793-11ea-b3de-0242ac130004', 'Suspicious Installation of Zenmap', 'experimental']
['e5684ad6-5824-4680-9cc5-e8f0babd77bb', 'Foobar', 'experimental']
tsctl list-sigma-rules --columns=rule_uuid,title,status | grep experimental | wc -l
3
```

#### Add Sigma rules in a folder

Will add all Sigma rules in a folder and its subfolders to the database.

```shell
tsctl import-sigma-rules sigma/rules/cloud/gcp/
Importing: Google Cloud Kubernetes RoleBinding
Importing: Google Cloud Storage Buckets Modified or Deleted
Importing: Google Cloud VPN Tunnel Modified or Deleted
Importing: Google Cloud Re-identifies Sensitive Information
...
```

#### Export Sigma rules

Will export all Sigma rules to a folder.

```shell
tsctl export-sigma-rules ./test
13 Sigma rules exported
```

#### Remove a Sigma rule

This will remove a single Sigma rule from the database

```shell
tsctl remove-sigma-rule 13f81a90-a69c-4fab-8f07-b5bb55416a9f
Rule 13f81a90-a69c-4fab-8f07-b5bb55416a9f deleted
```

#### Drop all Sigma rules

Will drop all Sigma rules from database.

Command:

```shell
tsctl remove-all-sigma-rules
Do you really want to drop all the Sigma rules? [y/N]: y
Are you REALLLY sure you want to DROP ALL the Sigma rules? [y/N]: y
All rules deleted
```

### Shell

tsctl provides a subcommand for starting an interactive Python shell with the Timesketch API client pre-initialized. This subcommand is called `shell`, and it allows you to access the Timesketch API and perform various operations using the Python interpreter.

To use the `shell` subcommand, you would run `tsctl shell` followed by the desired options and arguments. For example, to start an interactive Python shell with the Timesketch API client pre-initialized, you could run the following command: `tsctl shell`.

### Context Links Configuration

We can use `tsctl` to test the yaml config file for the context link feature.
This is especially useful if an entry that is added to the configuration file
does not show up as a context link in the frontend.

```
tsctl validate-context-links-conf <PATH TO CONFIG FILE>
```

The default config can be found at `data/context_links.yaml` .

The output will tell if there is a value not matching the schema requirements:

**No error:** All entries in the configuration file match the schema requirements.

```
$ tsctl validate-context-links-conf ./context_links.yaml
=> OK: "virustotal"
=> OK: "unfurl"
=> OK: "mseventid"
=> OK: "urlhaus"
```

**With an error:** Here the validator tells us that there is an error with the
replacement pattern in the `context_link` entry.

```
$ tsctl validate-context-links-conf ./context_links.yaml
=> ERROR: "virustotal" >> 'https://www.virustotal.com/gui/search/<ATTR_VALUE' does not match '<ATTR_VALUE>'

Failed validating 'pattern' in schema['properties']['context_link']:
    {'pattern': '<ATTR_VALUE>', 'type': 'string'}

On instance['context_link']:
    'https://www.virustotal.com/gui/search/<ATTR_VALUE'

=> OK: "unfurl"
=> OK: "mseventid"
=> OK: "urlhaus"
```

### Analyzer-stats

`tsctl`offers a method called `analyzer-stats` to display various information about analyzer runs of the past.

To use the `analyzer-stats` subcommand, you would run `tsctl analyzer-stats` followed by the desired options and arguments.

```shell
tsctl analyzer-stats
```

Example:

```shell
tsctl analyzer-stats --help
Usage: tsctl analyzer-stats [OPTIONS] ANALYZER_NAME

  Prints analyzer stats.

Options:
  --timeline_id TEXT         Timeline ID if the analyzer results should be
                             filtered by timeline.
  --scope TEXT               Scope on: [many_hits, long_runtime, recent]
  --result_text_search TEXT  Search in result text. E.g. for a specific
                             rule_id.
  --help                     Show this message and exit.
tsctl analyzer-stats sigma --scope many_hits --result_text_search 71a52
     runtime  hits                                                                          result  analysis_id                 created_at
36  0.083333  3657  3657 events tagged for rule [Scheduler] (71a5257c-222f-4898-a117-694d6c63457c)           51 2023-01-03 21:33:14.475700
37  0.083333  3657  3657 events tagged for rule [Scheduler] (71a5257c-222f-4898-a117-694d6c63457c)           52 2023-01-03 21:33:40.477309
39  0.083333  2344  2344 events tagged for rule [Scheduler] (71a5257c-222f-4898-a117-694d6c63457c)           54 2023-01-03 21:33:40.594573
38  0.000000   145   145 events tagged for rule [Scheduler] (71a5257c-222f-4898-a117-694d6c63457c)           55 2023-01-03 21:33:40.626931
47  0.100000   145   145 events tagged for rule [Scheduler] (71a5257c-222f-4898-a117-694d6c63457c)           61 2023-01-04 17:09:04.078641
40  0.000000     0     0 events tagged for rule [Scheduler] (71a5257c-222f-4898-a117-694d6c63457c)           53 2023-01-03 21:33:40.521002
41  0.000000     0     0 events tagged for rule [Scheduler] (71a5257c-222f-4898-a117-694d6c63457c)           56 2023-01-03 21:33:40.658743
42  0.000000     0     0 events tagged for rule [Scheduler] (71a5257c-222f-4898-a117-694d6c63457c)           57 2023-01-03 21:33:40.696942
43  2.800000     0                                * Scheduler 71a5257c-222f-4898-a117-694d6c63457c           58 2023-01-04 17:09:03.751176
44  2.816667     0                                * Scheduler 71a5257c-222f-4898-a117-694d6c63457c           62 2023-01-04 17:09:04.112822
45  2.833333     0                                * Scheduler 71a5257c-222f-4898-a117-694d6c63457c           60 2023-01-04 17:09:04.046003
46  2.833333     0                                * Scheduler 71a5257c-222f-4898-a117-694d6c63457c           59 2023-01-04 17:09:04.014973
48  2.750000     0                                * Scheduler 71a5257c-222f-4898-a117-694d6c63457c           63 2023-01-04 17:09:04.148185
```

### Celery Task Management

These commands allow you to inspect and manage Celery tasks within the Timesketch application.

#### `tsctl celery-tasks-redis`

**Description:**

Checks and displays the status of all Celery tasks stored in Redis. This command connects to the Redis instance used by Celery to store task metadata and retrieves information about all tasks. It then presents this information in a formatted table, including the task ID, name, status, and result.

Notes:

* Celery tasks have a result_expire date, which by default is one day. After that, the results will no longer be available.

**Usage:**

```bash
tsctl celery-tasks-redis
```

**Output:**

A table with the following columns:

* Task ID: The unique identifier for the Celery task.
* Name: The name of the task.
* Status: The current status of the task (e.g., SUCCESS, FAILURE, PENDING).
* Result: The result of the task if it has completed successfully.

```
Task ID                          Name Status  Result
13a995db28d2479b854db177d1301ecb None SUCCESS 3e062029b52f4e1a8a103488b99bc2b3
1829df81cb534ab29fe44d1e8c605c95 None SUCCESS 3e062029b52f4e1a8a103488b99bc2b3
ffd3d6157e0f458bbe5f4c97e6d70d03 None SUCCESS 9a0f22670bf74ba6884f3ba9b261bf13
```

#### tsctl celery-tasks

Shows running or past Celery tasks. This command provides various ways to inspect and view the status of Celery tasks within the Timesketch application. It can display information about a specific task, list active tasks, or show all tasks (including pending, active, and failed).

**Usage**

```bash
tsctl celery-tasks [OPTIONS]
```

Options:

* `--task_id TEXT`: Show information about a specific task ID.
* `--active`: Show only active tasks.
* `--show_all`: Show all tasks, including pending, active, and failed.

**Notes**

* Celery tasks have a `result_expire date`, which defaults to one day. After this period, task results may no longer be available.
* When displaying all tasks, the status of each task is retrieved, which may take some time.
* If no arguments are provided, it will print a message to use `--active` or `--show_all`.

**Examples**

```bash
tsctl celery-tasks --task_id <task_id>
tsctl celery-tasks --active
tsctl celery-tasks --show_all
```

#### celery-revoke-task

Revokes (cancels) a Celery task. This command attempts to revoke a running Celery task, effectively canceling its execution. It uses the task ID to identify the specific task to revoke.

Note: For short tasks, they have to be cancelled quick.

**Usage**

```bash
tsctl celery-revoke-task  TASK_ID
```

Example:
```
tsctl celery-revoke-task 8115648e-944c-4452-962e-644041603419
```

#### list-config

**Description:**

Lists all configuration variables currently loaded by the Timesketch Flask application (`current_app.config`).

This command iterates through the application's configuration settings. 

It automatically identifies keys commonly associated with sensitive information (like `SECRET_KEY`, `PASSWORD`, `API_KEY`, `TOKEN`, etc.) based on a predefined list of keywords.
To prevent accidental exposure, the values corresponding to these sensitive keys are redacted and replaced with `******** (redacted)` in the output. All other configuration key-value pairs are displayed as they are loaded.

The output is sorted alphabetically by key for consistent and predictable results. A note is included at the end to remind the user that some values may have been redacted for security reasons.

**Usage:**

```bash
tsctl list-config
Timesketch Configuration Variables:
-----------------------------------
ANALYZERS_DEFAULT_KWARGS: {}
APPLICATION_ROOT: /
AUTO_SKETCH_ANALYZERS: []
AUTO_SKETCH_ANALYZERS_KWARGS: {}
CELERY_BROKER_URL: redis://redis:6379
CELERY_RESULT_BACKEND: redis://redis:6379
CONTEXT_LINKS_CONFIG_PATH: /etc/timesketch/context_links.yaml
DATA_FINDER_PATH: /etc/timesketch/data_finder.yaml
DEBUG: False
OPENSEARCH_HOST: 127.0.0.1
OPENSEARCH_PORT: 9200
SECRET_KEY: ******** (redacted)
SQLALCHEMY_DATABASE_URI: ******** (redacted)
UPLOAD_ENABLED: True
...
-----------------------------------
Note: Some values might be sensitive (e.g., SECRET_KEY, passwords).
```

### export-sketch

Exports a Timesketch sketch to a zip archive. The archive contains:

1.  **`metadata.json`**: A comprehensive JSON file detailing the sketch, including:
    *   Basic sketch information (ID, name, description, status, timestamps, owner).
    *   Permissions and sharing details.
    *   Associated timelines with their configurations and data sources.
    *   Saved views (queries, filters, DSL).
    *   Stories, including their content.
    *   Aggregations and aggregation groups.
    *   Saved graphs.
    *   Analysis sessions and their results.
    *   DFIQ scenarios, including nested facets and investigative questions.
    *   Sketch attributes.
    *   Comments linked to specific events within the sketch.
    *   Export timestamp and Timesketch version.
2.  **Event Data File**: (e.g., `events.csv` or `events.jsonl`)
    *   All events from the sketch's active (not failed or processing) timelines, processed in batches to conserve memory.
    *   The format can be specified as CSV (default) or JSONL using the `--output-format` option.
    *   By default all fields are exported. Using `--default-fields` a predefined set (DEFAULT_SOURCE_FIELDS in `timesketch/lib/definitions.py`) of common event fields are exported.

**WARNING:** Re-importing this archive into Timesketch is not natively supported. This export is primarily for data archival, external analysis, or manual migration.

Progress messages are printed to the console during the export process.

**Usage:**

Parameters:

* **<SKETCH_ID>:** (Required) The ID of the sketch to export.
* **--filename / -f:** (Optional) The name for the output zip file. Default: sketch_{sketch_id}_{output_format}_export.zip
* **--output-format:** (Optional) The format for the event data ('csv' or 'jsonl'). Default: 'csv'.
* **--all-fields:** (Optional default: True) Export all event fields instead of the default set.

*Note on Container Usage:* When running this command within a container (e.g., Docker), the output zip file is written inside the container's filesystem. Ensure you write to a mounted volume or copy the file out of the container afterwards.

Example:

```bash
tsctl export-sketch  1

Exporting sketch [1] "aaaa" to sketch_1_csv_export.zip...

WARNING: There is currently no native method to re-import this exported archive back into Timesketch.

Gathering metadata...
  Processing comments for 4 event(s)...
  2025-05-14 10:02:00 INFO     GET http://opensearch:9200/ [status:200 request:0.008s]
  Exporting all event fields.
  Requesting event data (preferring JSONL)...
2025-05-14 10:02:00 INFO     POST http://opensearch:9200/484a472fd004a72f2ee857c39a4fb17c,9c49430d1e5f42849bdb253647e1f836,5caa30a18efa4333971b42957d86d09e/_search?scroll=1m&search_type=query_then_fetch [status:200 request:0.214s]

[...]

  Detected non-JSONL format in response (assuming CSV).
  303490 events processed for export.
  Input is not JSONL, using as CSV...
Creating zip archive...
Sketch exported successfully to sketch_1_csv_export.zip
```