## Table of Contents
1. [tsctl](#tsctl)
   - [User management](#User-management)
     - Adding users
     - Removing users
   - Group management
3. [Using Stories](#stories)

## tsctl

tsctl is a command line tool used to control timesketch.

Parameters:
```
--config / -c (optional)
```

Example
```
tsctl runserver -c /etc/timesketch.conf
```


### Start timesketch

Will start the timesketch server

Comand:
```
tsctl runserver
```

### User management

#### Adding users

Comand:
```
tsctl add_user
```

Parameters:
```
--name / -n
--password / -p (optional)
```

Example
```
tsctl add_user --name foo
```

#### Removing users

### Group management

#### Adding groups

Comand:
```
tsctl add_user
```

Parameters:
```
--name / -n
-- password / -p (optional)
```

#### Managing group membership

## Stories

A story is a place where you can capture the narrative of your technical investigation and add detail to your story with raw timeline data.
The editor let you to write and capture the story behind your investigation and at the same time enable you to share detailed findings without spending hours writing reports.

you can add events from previously saved searches. 
Just hit enter to start a new paragraph and choose the saved search from the dropdown menu.

See [Medium article](https://medium.com/timesketch/timesketch-2016-7-db3083e78156)
