---
hide:
  - footer
---
The hashR analyzer is used to lookup sha256 hash values against a hashR database
that is created using the [google/hashr](https://github.com/google/hashr) project.

### Use case

[Hashr](https://github.com/google/hashr) is a tool that extracts files and hashes
from input sources (e.g. raw disk image, GCE disk image, ISO file, Windows update
package, .tar.gz file, etc.) and allows you to build your own hash sets based on
your data sources.

This information can be used during an investigation to flag files that are
known, such as files that are part of the company's golden image.
This can help to find suspicious files faster by removing a lot of noise.

To learn more about HashR and how it can help investigations in Timesketch,
read our post ["Find the needle faster with hashR data"](https://osdfir.blogspot.com/2022/11/find-needle-faster-with-hashr-data.html)
over at osdfir blog.

### Configuration

1. Setup and generate your hashR database following the
[instructions on GitHub](https://github.com/google/hashr).

1. Add the information to connect to your hashR database in the
[timesketch.conf](https://github.com/google/timesketch/blob/master/data/timesketch.conf#L235)
at the `#-- hashR integration --#` section.

```
#-- hashR integration --#
# https://github.com/google/hashr
# Uncomment and fill this section if you want to use the hashR lookup analyzer.
# Provide hashR postgres database connection information below:
HASHR_DB_USER = 'hashRuser'
HASHR_DB_PW = 'xxxxxxxxxxxxxxxxx'
HASHR_DB_ADDR = '127.0.0.1'
HASHR_DB_PORT = '5432'
HASHR_DB_NAME = 'hashr'

# The total number of unique hashes that are checked against the database is
# split into multiple batches. This number defines how many unique hashes are
# checked per query. 50000 is the default value.
HASHR_QUERY_BATCH_SIZE = '50000'

# Set as True if you want to add the source of the hash ([repo:imagename]) as
# an attribute to the event. WARNING: This will increase the processing time
# of the analyzer!
HASHR_ADD_SOURCE_ATTRIBUTE = True
```

1. Restart your timesketch instance to load the new configuration.

1. Use the hashR lookup analyzer from the list of available analyzers in the
Timesketch UI.
