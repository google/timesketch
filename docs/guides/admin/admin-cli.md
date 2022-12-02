## tsctl

tsctl is a command line tool to control timesketch.

Parameters:

```shell
--config / -c (optional)
```

Example

```shell
tsctl runserver -c /etc/timesketch/timesketch.conf
```

### User management

#### Adding users

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

To remove an existing user, use the disable_user command. <br />
To add the same user back, use the enable_user command. <br />
Disabled users are not removed from the system, but marked as disabled. <br />
The current implementation is not complete. Disabled users will still show up for other commands.

Command:

```shell
tsctl disable_user
tsctl enable_user
```

Parameters:

```shell
--username / -u
```

Example

```shell
tsctl disable_user --username foo
tsctl enable_user --username foo
```

### Group management

#### Adding groups

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

Add or remove a user to a group. To add a user, specify the group and user. To
remove a user, include the -r option.

Command:

```shell
tsctl manage_group
```

Parameters:

```shell
--remove / -r (optional)
--group / -g
--user / -u
```

Example:

```shell
tsctl manage_group -u user_foo -g group_bar
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

### Migrate db

Command:

```shell
tsctl db
```

### Drop database

Will drop all databases.

Command:

```shell
tsctl drop_db
```

### Import json to Timesketch

Command:

```shell
tsctl json2ts
```

### Purge

Delete timeline permanently from Timesketch and OpenSearch. It will alert if a timeline is still in use in a sketch and prompt for confirmation before deletion.

```shell
 Args:
   index_name: The OpenSearch index name
```

Command:

```shell
tsctl purge
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

Displays verious information about a given sketch.

```shell
tsctl sketch-info
```

Example:

```shell
tsctl sketch-info 1
Sketch 1 Name: (Sketch Title)
active_timelines:
+----------------+----------------------------------+----------------------------+---------+---------------------------------------+
| searchindex_id |            index_name            |         created_at         | user_id |              description              |
+----------------+----------------------------------+----------------------------+---------+---------------------------------------+
|       1        | a17732074d8b492e934ef79910bfefa1 | 2022-10-21 15:06:52.849124 |    1    |     20200918_0417_DESKTOP-SDN1RPT     |
|       3        | 88002da782f64061bf3703bc782b6006 | 2022-10-21 15:19:26.072964 |    1    |              all_packets              |
|       1        | a17732074d8b492e934ef79910bfefa1 | 2022-10-21 15:28:55.474166 |    1    |     E01-DC01_20200918_0347_CDrive     |
|       4        | 11d761cd266640d798e30bb897c8dd4e | 2022-10-21 15:32:15.060184 |    1    | autoruns-desktop-sdn1rpt_fresh_import |
|       3        | 88002da782f64061bf3703bc782b6006 | 2022-10-31 10:15:12.316273 |    1    |              sigma_events             |
|       3        | 88002da782f64061bf3703bc782b6006 | 2022-10-31 10:15:48.592320 |    1    |             sigma_events2             |
+----------------+----------------------------------+----------------------------+---------+---------------------------------------+
Shared with:
	Users:
		3: bar
	Groups:
		user-group
Sketch Status: new
Sketch is public: True
Sketch Labels: ([],)
Status:
+----+--------+----------------------------+---------+
| id | status |         created_at         | user_id |
+----+--------+----------------------------+---------+
| 1  |  new   | 2022-10-21 15:04:59.935504 |   None  |
+----+--------+----------------------------+---------+
```

### Sigma

#### List Sigma rules

Lists all Sigma rules installed on a system

```shell
tsctl list-sigma-rules
```

#### Add Sigma rules in a folder

Will add all Sigma rules in a folder and its subfolders to the databse.

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

This will remove a single Sigma rule from the databse

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

### Upgrade DB After Schema Change

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

#### Troubleshooting Database Schema Changes

If the migration file is not created, which could be an indication that the schema change
is not detected by the automation one can create an empty revision file:

```shell
tsctl db revision
```

And then fill in the blanks, see examples of changes in `timesketch/migrations/versions/*_.py`.
