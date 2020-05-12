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


