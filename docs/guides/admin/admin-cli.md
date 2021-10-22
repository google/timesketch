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
tsctl add_user
```

Parameters:

```shell
--name / -n
--password / -p (optional)
```

Example

```shell
tsctl add_user --name foo
```

#### Change user password

To change a user password, the add_user command can be used, as it is checking if the user exists if yes it will update the update.

Command:

```shell
tsctl add_user
```

Parameters:

```shell
--username / -u
--password / -p (optional)
```

Example

```shell
tsctl add_user --username foo
```

#### Removing users

Not yet implemented.

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

Delete timeline permanently from Timesketch and Elasticsearch. It will alert if a timeline is still in use in a sketch and prompt for confirmation before deletion.

```shell
 Args:
   index_name: The name of the index in Elasticsearch
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
