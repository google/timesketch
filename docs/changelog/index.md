---
hide:
  - title
  - navigation
  - footer
---

# Changelog

## Version 20230526
Released: 2023-05-26

#### 🚨 Security
* Fix for upload path bug that made it possible for an **authenticated** user to save user-controlled content to the server. See details in: [issue #2766](https://github.com/google/timesketch/issues/2766)

#### 🐞 Fixes
* Implicit String Fix
* Fixes/updates for AggregateDialog
* Fix invalid sigma YAML

#### 🏠 Internal
Dependency updates

* alembic==1.11.1
* celery==5.2.7
* cryptography==39.0.1
* Flask==2.3.2
* flask_bcrypt==1.0.1
* flask_login==0.6.2
* flask_migrate==4.0.4
* flask_restful==0.3.10
* flask_sqlalchemy==3.0.3
* flask_wtf==1.1.1
* redis==4.4.4
* requests==2.31.0
* SQLAlchemy==1.4.48
* Werkzeug==2.3.4
* WTForms==3.0.1
* prometheus-client==0.16.0
* prometheus-flask-exporter==0.22.4

---

## Version 20230518
Released: 2023-05-25

#### 🚨 Security
* Fix for bug that made it possible for an **authenticated** user to save user-controlled content as a search template. See details in: [issue #2765](https://github.com/google/timesketch/issues/2765)

#### ✨ Features
* Context Search in WebUI (#2715)
* Add "remove tag" to timesketch-cli-client (#2732)
* Add "untag_event" and "untag_events" to timesketch-api-client (#2729)
* Add untag event to WebUI + some minor WebUI tag aspects (#2694)

#### 🐞 Fixes
* Pagination fixes
* Timeline details were missing the Context
* Fixed inconsistencies in left panel
* Events without a “tag” attribute couldn’t have new tags added
* The search can only be triggered via the enter key
* Dark UI problem with graphs
* With broken timelines there is an error that the event counter cannot be processed
* Saved searches throwing errors
* Exit early if there is no Cytoscape graph instance
* Analyzer related bugfixes (#2722, #2725)
* Sigma parsing NoneType Error (#2716)

---

### Previous release notes
* [March 2023](/changelog/2023-03/)
* [February 2023](/changelog/2023-02/)
* [January 2023](/changelog/2023-01/)
* [December 2022](/changelog/2022-12/)
* [October 2022](/changelog/2022-10/)
* [September 2022](/changelog/2022-09/)
