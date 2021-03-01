## Timesketch API Client Config

In order to make it simpler to connect to the API client a config file
can be generated or created to store information needed to connect.

The file is stored in the user's home directory, in a file called
`$HOME/.timesketchrc`.

The content of the file is:

```
[timesketch]
...
```

An example config file for an API client that uses OAUTH to connect:

```
[timesketch]
client_secret = <redacted secret>
host_uri = https://mytimesketchhost.com
username = myusername@mydomain.com
auth_mode = oauth
client_id = <redacted client ID>
verify = True
```

A config file can have multiple sections to define which host to connect to.
This is useful if you want to be able to connect to more than a single
Timesketch instance, for instance your development instance and a production
one.

An example of that would be:

```
[timesketch]
host_uri = https://myprodtimesketch.corp.com
username = myselfandirene
verify = True
client_id = 
client_secret = 
auth_mode = userpass
cred_key = <redacted>

[timesketch-dev]
host_uri = http://localhost:5000
username = dev
verify = True
client_id = 
client_secret = 
auth_mode = userpass
cred_key = <redacted>
token_file_path = /home/myselfandirene/.timesketch.dev.token
```

Each of the additional sections needs to define a separate token file using the
`token_file_path`, otherwise the config will attempt to read the default token
file.
