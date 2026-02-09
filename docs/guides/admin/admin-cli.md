---
hide:
  - footer
---
# tsctl - Timesketch Control Tool

`tsctl` is a command-line tool for managing and interacting with a Timesketch instance. It allows administrators to perform a wide range of tasks, from user and sketch management to system maintenance and data integrity checks.

## Usage

All commands are run by invoking `tsctl` followed by a specific subcommand and any necessary options.

```shell
tsctl <COMMAND> [OPTIONS] [ARGUMENTS]
```

### Configuration

Most `tsctl` commands require application context to interact with the database and other services. You can specify the location of your `timesketch.conf` file to ensure the tool is properly configured.

```shell
tsctl --config /etc/timesketch/timesketch.conf <COMMAND>
```

---

## General Commands

#### `version`

Displays the installed version of Timesketch.

**Example:**
```shell
tsctl version
Timesketch version: 20210602
```

#### `info`

Displays detailed version information for Timesketch and its key dependencies, including the Git commit hash if available.

**Example:**
```shell
tsctl info
Timesketch version: 20250708
Timesketch commit: 2cb3356b (dirty)
plaso - psort version 20240308
Node version: v20.19.1
npm version: 10.8.2
yarn version: 1.22.22
Python version: Python 3.10.12
pip version: pip 22.0.2 from /usr/lib/python3/dist-packages/pip (python 3.10)
```

#### `list-config`

Lists all configuration variables currently loaded by the Timesketch application. Sensitive values like keys and passwords are automatically redacted.

**Example:**
```shell
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
Note: Some values might be sensitive and have been redacted.
```

#### `routes`

Displays all available API routes in the Timesketch instance.

**Example:**
```bash
tsctl routes
Endpoint                           Methods            Rule
---------------------------------  -----------------  -------------------------------------------------------------------------
aggregationexploreresource         POST               /api/v1/sketches/<int:sketch_id>/aggregation/explore/
```

#### `shell`

Starts an interactive Python shell with the Timesketch API client pre-initialized, allowing for direct interaction with the Timesketch backend.

**Example:**
```bash
tsctl shell
```

---

## User Management

#### `list-users`

Lists all users in the system.

**Options:**
*   `--status`: Shows the active/inactive status of each user.

**Examples:**
```shell
tsctl list-users
foo
bar
dev (admin)
```
```shell
tsctl list-users --status
dev (active: True)
admin (active: True)
foobar2 (active: True)
foobar (active: False)
```

#### `create-user`

Creates a new user or updates the password for an existing user.

**Arguments:**
*   `USERNAME`: The username for the new user.

**Options:**
*   `--password`: Set the password directly. If omitted, you will be prompted interactively.

**Examples:**
```shell
tsctl create-user foo
tsctl create-user foo --password bar
```

#### `enable-user` / `disable-user`

Activates or deactivates a user account. Disabled users cannot log in.

**Arguments:**
*   `USERNAME`: The user to enable or disable.

**Examples:**
```shell
tsctl disable-user foo
tsctl enable-user foo
```

#### `make-admin` / `revoke-admin`

Grants or revokes administrator privileges for a user.

**Arguments:**
*   `USERNAME`: The target user.

**Examples:**
```shell
tsctl make-admin dev
tsctl revoke-admin dev
```

---

## Group Management

#### `list-groups`

Lists all groups.

**Options:**
*   `--showmembership`: Includes a list of members for each group.

**Example:**
```bash
tsctl list-groups --showmembership
analysts: john, jane
incident-responders: jane
```

#### `create-group`

Creates a new group.

**Arguments:**
*   `GROUP_NAME`: The name for the new group.

**Example:**
```shell
tsctl create-group analysts
```

#### `delete-group`

Deletes a group from the database. If the group is associated with any sketches, a warning message will be displayed, and the deletion will be aborted unless the `--force` flag is used.

**Arguments:**
*   `GROUP_NAME`: The name of the group to delete.

**Options:**
*   `--force`: Force deletes the group even if it's used in sketches.

**Example:**
```shell
tsctl delete-group analysts
```
**Example (force delete):**
```shell
tsctl delete-group my-shared-group --force
```

#### `list-group-members`

Lists all members of a group.

**Arguments:**
*   `GROUP_NAME`: The group to list members for.

**Example:**
```shell
tsctl list-group-members analysts
```

#### `add-group-member` / `remove-group-member`

Adds a user to a group or removes them.

**Arguments:**
*   `GROUP_NAME`: The target group.

**Options:**
*   `--username`: The user to add or remove.

**Examples:**
```shell
tsctl add-group-member analysts --username john
tsctl remove-group-member analysts --username john
```

#### `sync-groups-from-json`

Synchronizes user group memberships from a JSON file. This command will create,
add, and remove users from groups to match the state defined in the JSON file.

**Arguments:**
*   `FILEPATH`: Path to a JSON file containing the group membership definition.

**Options:**
*   `--dry-run`: If set, the command will print the changes it would make without
    actually modifying the database.

**JSON File Format:**

The JSON file must be a dictionary where each key is a group name and the value
is a list of usernames to be in that group.

**Example JSON (`/tmp/groups.json`):**
```json
{
    "analysts": ["user1@timesketch.org", "user2@timesketch.org"],
    "incident-responders": ["user2@timesketch.org", "user3@timesketch.org"]
}
```

**Behavior:**
*   **Groups**: Creates groups if they don't exist. Groups in the database but
    not in the JSON file are ignored.
*   **Users**: Creates users if they don't exist (with a random password).
*   **Membership**:
    *   Adds users to groups to match the JSON file.
    *   Removes users from groups if they are in the database but not in the
        corresponding list in the JSON file.

**Example Usage:**
```shell
# Perform a dry run to see what changes would be made
tsctl sync-groups-from-json /tmp/groups.json --dry-run

# Apply the changes to the database
tsctl sync-groups-from-json /tmp/groups.json
```

---

## Sketch Management

#### `list-sketches`

Lists sketches in the database.

**Options:**
*   `--archived`: Show only archived sketches.
*   `--archived-with-open-indexes`: Show archived sketches that have at least one searchindex with status 'new', 'ready', 'processing', 'fail', 'archived' or 'timeout'. Mutually exclusive with --archived.
*   `--include-deleted`: Include sketches marked as deleted.

**Example:**
```shell
tsctl list-sketches
1 'Project-X' (status: new)
2 'Incident-Y' (status: archived)
```

#### `sketch-info`

Displays detailed information about a specific sketch. This includes a summary of all timelines, a list of data sources for each timeline, sharing status, labels, and a history of status changes.

**Arguments:**
*   `SKETCH_ID`: The ID of the sketch.

**Example:**
```shell
tsctl sketch-info 1
Sketch 1 Name: (New Sketch From Importer CLI)

Timelines:
ID Name              Search Index ID Index Name                       Created At                 User ID Description   Status
36 3173_web          27              b857825d9c024bb2bdefe8f98c9519d8 2025-11-07 14:43:24.489482 1       3173          ready
38 new_cli           27              b857825d9c024bb2bdefe8f98c9519d8 2025-11-07 15:46:11.607402 1       new_cli       ready
37 import_client_old 27              b857825d9c024bb2bdefe8f98c9519d8 2025-11-07 14:53:04.528269 1       import_client ready

Data Sources per Timeline:

Timeline: 3173_web (ID: 36)
ID File Path                             Status Error Message
37 /tmp/0bed74e6918f4262a5a72ce319123b5f ready  N/A

Timeline: new_cli (ID: 38)
ID File Path Status Error Message
39           ready  N/A

Timeline: import_client_old (ID: 37)
ID File Path Status Error Message
38           ready  N/A

Created by: dev
Shared with:
	Users: (user_id, username, access_level)
	No users shared with.
	Groups (0): (group_name, access_level)
	No groups shared with.
Sketch Status: new
Sketch is public: False
Sketch Labels: ([],)
Status:
id status created_at                 user_id
65 new    2025-11-07 14:42:18.813488 None
...
```

#### `event-details`

Display all data for a specific event.

**Options:**
*   `--sketch-id INTEGER`: (Required) The ID of the sketch.
*   `--event-id TEXT`: (Required) The ID of the event.
*   `--searchindex-id TEXT`: The OpenSearch index name for the event.

**Example:**
```bash
tsctl event-details --sketch-id 1 --event-id 12345
```

#### `grant-user`

Grants a user access to a specific sketch.

**Arguments:**
*   `USERNAME`: The user to grant access to.

**Options:**
*   `--sketch_id INTEGER`: (Required) The ID of the sketch.
*   `--read-only`: Grant only read access.

**Examples:**
```shell
# Grant read and write access to user 'john' for sketch ID 123
tsctl grant-user john --sketch_id 123
# Grant read-only access to user 'jane' for sketch ID 456
tsctl grant-user jane --sketch_id 456 --read-only
```

#### `grant-group`

Grants a group access to a specific sketch.

**Arguments:**
*   `GROUP_NAME`: The group to grant access to.

**Options:**
*   `--sketch_id INTEGER`: (Required) The ID of the sketch.
*   `--read-only`: Grant only read access.

**Examples:**
```shell
tsctl grant-group analysts --sketch_id 123
tsctl grant-group incident-responders --sketch_id 456 --read-only
```

#### `export-sketch`

Exports a sketch to a zip archive, including all metadata and event data.

!!! warning "Archive and Re-import"
    This export is primarily for data archival or external analysis. Re-importing this archive into Timesketch is not natively supported.

**Arguments:**
*   `SKETCH_ID`: The ID of the sketch to export.

**Options:**
*   `--filename`: The name for the output zip file. Default: `sketch_{sketch_id}_{output_format}_export.zip`
*   `--output-format`: Format for event data ('csv' or 'jsonl'). Default: 'csv'.
*   `--default-fields`: Export only the default set of event fields. If not specified, all fields are exported.

**Example:**
```bash
tsctl export-sketch 1 --filename "project_x_export.zip"
```

#### `sketch-label-stats`

Provides detailed statistics on label and tag usage within a sketch, querying both the database and OpenSearch.

**Options:**
*   `--sketch_id <SKETCH_ID>`: (Required) The ID of the sketch to analyze.
*   `--verbose`: If set, the command will show full event data instead of just counts for each category.

**Example:**
```bash
tsctl sketch-label-stats --sketch_id 1 --verbose
```

---

## Timeline & SearchIndex Management


#### `searchindex-info`

Displays information about a search index, including which timelines and sketches it belongs to.

**Options:**
*   `--searchindex_id INTEGER`: The database ID of the search index.
*   `--index_name TEXT`: The OpenSearch name of the index.

**Examples:**
```bash
tsctl searchindex-info --searchindex_id 1
tsctl searchindex-info --index_name 4c5afdf60c6e49499801368b7f238353
```

#### `timeline-status`

Gets or sets the status of a timeline. This is useful for manually correcting the state of an import that has failed or stalled.

**Arguments:**
*   `TIMELINE_ID`: The ID of the timeline.

**Options:**
*   `--action [get|set]`: The action to perform.
*   `--status [ready|processing|fail]`: The status to set.

**Examples:**
```bash
# Get the status of timeline with ID 123:
tsctl timeline-status 123 --action get

# Set the status of timeline with ID 456 to "ready":
tsctl timeline-status 456 --action set --status ready
```

#### `searchindex-status`

Gets or sets the status of a search index.

**Options:**
*   `--searchindex_id`: The ID of the search index.
*   `--action [get|set]`: The action to perform.
*   `--status [ready|processing|fail]`: The status to set.

**Example:**
```bash
tsctl searchindex-status --searchindex_id 1 --action set --status fail
```

---

## Search Template Management

#### `import-search-templates`

Imports search templates from YAML files in a given directory path.

**Arguments:**
*   `PATH`: The directory to import templates from.

**Example:**
```shell
tsctl import-search-templates /path/to/my_templates/
```

---

## Sigma Rule Management

#### `list-sigma-rules`

Lists all installed Sigma rules.

**Options:**
*   `--columns`: Comma-separated list of columns to display (e.g., `rule_uuid,title,status`).

**Example:**
```bash
tsctl list-sigma-rules --columns=rule_uuid,title,status
```

#### `import-sigma-rules`

Imports Sigma rules from a given file or directory path.

**Arguments:**
*   `PATH`: The file or directory to import from.

**Example:**
```shell
tsctl import-sigma-rules sigma/rules/cloud/gcp/
```

#### `export-sigma-rules`

Exports all Sigma rules from the database to a directory.

**Arguments:**
*   `PATH`: The directory to export rules to.

**Example:**
```shell
tsctl export-sigma-rules ./my_exported_rules
```

#### `remove-sigma-rule`

Deletes a single Sigma rule from the database.

**Arguments:**
*   `RULE_UUID`: The UUID of the rule to delete.

**Example:**
```shell
tsctl remove-sigma-rule 13f81a90-a69c-4fab-8f07-b5bb55416a9f
```

#### `remove-all-sigma-rules`

Deletes all Sigma rules from the database after confirmation.

**Example:**
```shell
tsctl remove-all-sigma-rules
```

---

## System Administration

#### `db`

Provides access to database migration commands (init, migrate, upgrade, etc.) via `Flask-Migrate`.

**Example:**
```shell
# Generate a new migration after a schema change
tsctl db migrate -m "Add new column to user table"

# Apply migrations
tsctl db upgrade
```

#### `drop-db`

Permanently drops all tables from the relational database. This is a destructive action.

**Example:**
```bash
tsctl drop-db
```

#### `export-db` / `import-db`

Exports or imports the relational database metadata.

!!! warning "Metadata Only - Use with Caution"
    These commands only handle the relational database (e.g., PostgreSQL) and do **NOT** affect the event data in OpenSearch. For a full backup or migration, you must handle OpenSearch data separately (e.g., with snapshots). Importing a DB without its corresponding OpenSearch indices will result in a broken system.

**Examples:**
```shell
tsctl export-db output.zip
tsctl import-db output.zip
```

#### `check-opensearch-links`

Verifies that every timeline in the database has a corresponding index in OpenSearch, helping to identify broken timelines.

**Example:**
```bash
tsctl check-opensearch-links
```

#### `validate-context-links-conf`

Validates the syntax of a context links YAML configuration file.

**Arguments:**
*   `PATH`: Path to the `context_links.yaml` file.

**Example:**
```bash
tsctl validate-context-links-conf data/context_links.yaml
```

#### `check-db-orphaned-data`

Checks for various types of orphaned data in the database.

**Options:**
*   `--verbose-checks`: Show output for all checks, even those that find no orphans.

**Example:**
```bash
tsctl check-db-orphaned-data --verbose-checks
```

#### `find-inconsistent-archives`

Finds sketches that are in an inconsistent archival state.

An inconsistent state is defined as a sketch that has been marked as 'archived', but still contains one or more timelines that are not also archived.

**Example:**
```bash
tsctl find-inconsistent-archives
```

#### `analyzer-stats`

Displays statistics about past analyzer runs.

**Arguments:**
*   `ANALYZER_NAME`: (Optional) The name of the analyzer to filter by.

**Options:**
*   `--timeline_id INTEGER`: Timeline ID if the analyzer results should be filtered by timeline.
*   `--scope [many_hits|long_runtime|recent]`: Sorts the results.
*   `--result_text_search TEXT`: Search in result text. E.g. for a specific rule_id.
*   `--limit INTEGER`: Limits the number of results.
*   `--export_csv TEXT`: Export the results to a CSV file.

**Example:**
```shell
tsctl analyzer-stats sigma --scope many_hits --result_text_search 71a52
```

---

## Analyzer Management

#### `list-analyzer-runs`

Lists the analyzer runs for a specific sketch. By default, only runs with a `PENDING` status are shown.

**Arguments:**
*   `SKETCH_ID`: The ID of the sketch to list runs for.

**Options:**
*   `--show-all`: Show all analyzer runs, regardless of their status (e.g., DONE, ERROR, REVOKED).

**Example:**
```bash
tsctl list-analyzer-runs 1
tsctl list-analyzer-runs 1 --show-all
```

#### `manage-analyzer-run`

Manages specific analyzer runs, allowing you to change their status or revoke associated Celery tasks.

**Arguments:**
*   `ANALYSIS_IDS`: A comma-separated list of analysis run IDs to manage (e.g., `123,456,789`).

**Options:**
*   `--status [ERROR|DONE|STARTED]`: Manually set the status of the analysis run(s). This will also update the result field with an audit note.
*   `--kill`: Attempt to find and revoke (kill) the active or queued Celery task associated with this analysis. If no status is provided, it defaults to `ERROR`.

**Examples:**
```bash
# Set status to ERROR for a single analysis
tsctl manage-analyzer-run 123 --status ERROR

# Kill multiple tasks (sets status to ERROR for each)
tsctl manage-analyzer-run 123,456,789 --kill

# Set status to DONE for multiple analyses
tsctl manage-analyzer-run 123,456 --status DONE
```

---

## Celery Task Management

#### `celery-tasks-redis`

Displays the status of all Celery tasks as recorded in Redis.

**Example:**
```bash
tsctl celery-tasks-redis
```

#### `celery-tasks`

Shows running or past Celery tasks from the Celery worker.

**Options:**
*   `--task_id TEXT`: Show information for a specific task.
*   `--active`: Show only currently active tasks.
*   `--show_all`: Show all tasks (pending, active, failed).

**Examples:**
```bash
tsctl celery-tasks --active
tsctl celery-tasks --task_id <TASK_ID>
```

#### `celery-revoke-task`

Revokes (cancels) a running Celery task.

**Arguments:**
*   `TASK_ID`: The ID of the task to revoke.

**Example:**
```bash
tsctl celery-revoke-task 8115648e-944c-4452-962e-644041603419
```
