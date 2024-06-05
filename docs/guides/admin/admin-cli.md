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

To use the `create-user` subcommand, you would run `tsctl create-user` followed by the desired options and arguments. For example, to create a user with the username "john" and the password "123456", you could run the following command: `tsctl create-user --username john --password 123456`.

Once the user is created, they will be able to log in to the Timesketch instance using their username and password. You can then use the list-users subcommand to verify that the user was created successfully.

Command:

```shell
tsctl create-user
```

Parameters:

```shell
--name / -n
--password / -p (optional)
```

Example

```shell
tsctl create-user foo
```

#### Change user password

To change a user password, the create-user command can be used, as it is checking if the user exists if yes it will update the update.

This command would change the password of the user with the specified username to the new password provided. The user will then be able to log in to the Timesketch instance using their new password.

Command:

```shell
tsctl create-user
```

Parameters:

```shell
--username / -u
--password / -p (optional)
```

Example

```shell
tsctl create-user foo
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

#### Make admin

tsctl provides a subcommand for granting administrator privileges to a user in a Timesketch instance. This subcommand is called `make-admin`, and it allows you to specify the username of the user you want to grant administrator privileges to.

To use the `make-admin` subcommand, you would run `tsctl make-admin` followed by the desired options and arguments. For example, to grant administrator privileges to a user with the username "john", you could run the following command: `tsctl make-admin  john`

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

tsctl provides a subcommand for adding groups in a Timesketch instance. This subcommand is called `add-group`, and it allows you to specify the name and description of the group you want to add.

To use the `add-group` subcommand, you would run tsctl add-group followed by the desired options and arguments. For example, to add a group called "analysts" with the description "Group for analysts", you could run the following command: `tsctl add-group --name analysts --description "Group for analysts"`
This command would create a new group with the specified name and description. Once the group is created, you can use the `list-groups` subcommand to verify that the group was added successfully.

You can also use the `add-user-to-group` subcommand to add users to the group you have created. This allows you to manage the members of the group, and control which users have access to the sketches and data sources associated with the group.

Command:

```shell
tsctl add_group
```

Parameters:

```shell
--name / -n
```

#### Removing groups

Not yet implemented.

#### Managing group membership

##### Add a suer to a group

tsctl provides a subcommand for adding users to a group in a Timesketch instance. This subcommand is called `add-group-member`, and it allows you to specify the username of the user you want to add to the group, as well as the name of the group you want to add the user to.

To use the `add-group-member` subcommand, you would run `tsctl add-group-member` followed by the desired options and arguments. For example, to add a user with the username "john" to a group called "analysts", you could run the following command: `tsctl add-group-member --username john --group-name analysts`.
This command would add the user with the specified username to the group with the specified name.

Once the user is added to the group, they will be able to access the sketches and data sources associated with the group, based on the permissions granted to the group. You can use the `list-groups` subcommand to verify that the user was added to the group successfully.

Command:

```shell
tsctl add-group-member
```

Example:

```shell
tsctl add-group-member --username john --group-name analysts
```

##### Removing a group member

tsctl provides a subcommand for removing users from a group in a Timesketch instance. This subcommand is called `remove-group-member`, and it allows you to specify the username of the user you want to remove from the group, as well as the name of the group you want to remove the user from.

To use the `remove-group-member` subcommand, you would run `tsctl remove-group-member` followed by the desired options and arguments. For example, to remove a user with the username "john" from a group called "analysts", you could run the following command: `tsctl remove-group-member --username john --group-name analysts`

This command would remove the user with the specified username from the group with the specified name.

Once the user is removed from the group, they will no longer be able to access the sketches and data sources associated with the group. You can use the list-groups subcommand to verify that the user was removed from the group successfully.


Command:

```shell
tsctl remove-group-member
```

Example:

```shell
tsctl remove-group-member --username john --group-name analysts
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

Displays various information about a given sketch.

```shell
tsctl sketch-info
```

Example:

```shell
Sketch 1 Name: (aaa)
searchindex_id index_name                       created_at                 user_id description
1              a17732074d8b492e934ef79910bfefa1 2022-10-21 15:06:52.849124 1       20200918_0417_DESKTOP-SDN1RPT
3              88002da782f64061bf3703bc782b6006 2022-10-21 15:19:26.072964 1       all_packets
1              a17732074d8b492e934ef79910bfefa1 2022-10-21 15:28:55.474166 1       E01-DC01_20200918_0347_CDrive
4              11d761cd266640d798e30bb897c8dd4e 2022-10-21 15:32:15.060184 1       autoruns-desktop-sdn1rpt_fresh_import
3              88002da782f64061bf3703bc782b6006 2022-10-31 10:15:12.316273 1       sigma_events
3              88002da782f64061bf3703bc782b6006 2022-10-31 10:15:48.592320 1       sigma_events2
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

Therefore the following command can be used:

```bash
# tsctl searchindex-info --searchindex_id asd
Searchindex: asd not found in database.
# tsctl searchindex-info --searchindex_id 4c5afdf60c6e49499801368b7f238353
Searchindex: 4c5afdf60c6e49499801368b7f238353 Name: sigma_events found in database.
Corresponding Timeline id: 3 in Sketch Id: 2
Corresponding Sketch id: 2 Sketch name: asdasd
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
