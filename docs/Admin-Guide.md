## Table of Contents

- [Table of Contents](#table-of-contents)
- [Installation](#installation)
- [Upgrading](#upgrading)
- [tsctl](#tsctl)
  - [User management](#user-management)
    - [Adding users](#adding-users)
    - [Change user password](#change-user-password)
    - [Removing users](#removing-users)
  - [Group management](#group-management)
    - [Adding groups](#adding-groups)
    - [Removing groups](#removing-groups)
    - [Managing group membership](#managing-group-membership)
  - [add_index](#add_index)
  - [Migrate db](#migrate-db)
  - [Drop database](#drop-database)
  - [Import json to Timesketch](#import-json-to-timesketch)
  - [Purge](#purge)
  - [search_template](#search_template)
  - [import](#import)
  - [similarity_score](#similarity_score)

## Installation

To install Timesketch, please see [Installation documentation](/docs/Installation.md)

## Upgrading

To upgrade Timesketch, please see [Upgrade documentation](/docs/Upgrade.md)

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

Comand:

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

Comand:

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


After changin the schema for the database a revision file needs to be generated.
To generate the file use the command:

```shell
tsctl db stamp head
tsctl db upgrade
```

This makes sure that the database is current. Then create a revision file:

```shell
tsctl db migrate -m "<message>"
```
