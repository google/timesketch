---
hide:
  - footer
---
The hashR analyzer is used to lookup sha256 hash values against a hashR database
that is created using the  [google/hashr](https://github.com/google/hashr) project.

### Use case
[Hashr](https://github.com/google/hashr) is a tool that extracts files and hashes
from input sources (e.g. raw disk image, GCE disk image, ISO file, Windows update
package, .tar.gz file, etc.) and allows you to build your own hash sets based on
your data sources.

This information can be used during an investigation to flag files that are
"known-good" files, such as files that are part of the company's golden image.
This can help to find malicious files faster by removing a lot of noise.

You can read more about a demo use case in the blog post
["Find the needle faster with hashR data"](https://osdfir.blogspot.com/2022/11/find-needle-faster-with-hashr-data.html)


### Configuration
1. Setup and generate your hashR database following the
[instructions on GitHub](https://github.com/google/hashr). Additional reading
is provided with the blog
["Generate your own hash sets with HashR"](https://osdfir.blogspot.com/2022/08/generate-your-own-hash-sets-with-hashr.html)

1. Add the information to connect to your hashR database in the
[timesketch.conf](https://github.com/google/timesketch/blob/master/data/timesketch.conf#L235)
at the `#-- hashR integration --#` section.

1. Restart your timesketch instance to load the new configuration.

1. Use the hashR lookup analyzer!
