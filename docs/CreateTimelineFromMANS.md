# Create timeline from MANS file

You need to run version mans-to-es >=  1.0 on your Timesketch server. See the [mans_to_es documentation](https://github.com/LDO-CERT/mans_to_es) for installing mans_to_es and it's dependencies. If you haven't installed Timesketch yet, take a look at the [installation instructions](Installation.md).

When you have working installations of Timesketch and mans_to_es you can, from the command line, do:

```
$ mans_to_es.py --help
usage: MANS to ES [-h] [--filename FILENAME] [--name NAME] [--index INDEX]
                  [--es_host ES_HOST] [--es_port ES_PORT]
                  [--cpu_count CPU_COUNT] [--bulk_size BULK_SIZE] [--version]

Push .mans information in Elasticsearch index

optional arguments:
  -h, --help            show this help message and exit
  --filename FILENAME   Path of the .mans file
  --name NAME           Timeline name
  --index INDEX         ES index name
  --es_host ES_HOST     ES host
  --es_port ES_PORT     ES port
  --cpu_count CPU_COUNT
                        cpu count
  --bulk_size BULK_SIZE
                        Bulk size for multiprocessing parsing and upload
  --version             show program's version number and exit
```
