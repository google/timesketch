---
hide:
  - title
  - navigation
  - footer
---

# Changelog


## Version 20240328
Released: 2024-03-28

### ⚠️ Note
Upgrading to this Timesketch version requires a database upgrade!

See https://timesketch.org/guides/admin/upgrade/ for more details.

### What's Changed
#### ✨ Features

* DFIQ new UI and navigation by @berggren in [#3041](https://github.com/google/timesketch/pull/3041)
* User profile and settings support by @berggren in [3048](https://github.com/google/timesketch/pull/3048)
* Enhancements to Yeti indicators by @tomchop in [3038](https://github.com/google/timesketch/pull/3038)

#### 🐞 Fixes

* Improvements to the sigma handling by @tomchop in [3050](https://github.com/google/timesketch/pull/3050)
* Update run_analyzers in the api client by @jkppr in [3037](https://github.com/google/timesketch/pull/3037)
* Fix a bug in the feature_extraction analyzer by @jkppr in [3047](https://github.com/google/timesketch/pull/3047)


**Full Changelog**: [20240207...20240328](https://github.com/google/timesketch/compare/20240207...20240328)

## Version 20240207
Released: 2024-02-07

### What's Changed
#### ✨ Features

* Collapsable left panel by @berggren in [#3008](https://github.com/google/timesketch/pull/3008)
* Support for Large Language Model (LLM) services by @berggren in [#3019](https://github.com/google/timesketch/pull/3019)
* Implement user management (create, list, get) via API by @lo-chr in [#3024](https://github.com/google/timesketch/pull/3024)
* Setup frontend unit tests with vitest by @Annoraaq in [#3013](https://github.com/google/timesketch/pull/3013)

#### 🐞 Fixes

* Move "old UI" button by @jkppr in [#3033](https://github.com/google/timesketch/pull/3033)
* Mark events with indicator's relevant_tags (Yeti) by @tomchop in [#3022](https://github.com/google/timesketch/pull/3022)
* Fix failing Plaso uploads after 6 months by @jkppr in [#3017](https://github.com/google/timesketch/pull/3017)
* Fix error handling in the API client by @jkppr in [#3006](https://github.com/google/timesketch/pull/3006)
* Add optional TLS verification by @tomchop in [#3016](https://github.com/google/timesketch/pull/3016)
* Yeti analyzer fix: use session object by @tomchop in [#3020](https://github.com/google/timesketch/pull/3020)
* Adjust query for Yeti indicators by @tomchop in [#3009](https://github.com/google/timesketch/pull/3009)
* Bump cryptography from 41.0.4 to 41.0.6 by @dependabot in [#2998](https://github.com/google/timesketch/pull/2998)
* SQLalchemy upgrade - step one by @berggren in [#2979](https://github.com/google/timesketch/pull/2979)
* Fix: get and use access token for Yeti by @tomchop in [#3010](https://github.com/google/timesketch/pull/3010)
* Adding form validation to prevent names > 255 char. by @jkppr in [#3026](https://github.com/google/timesketch/pull/3026)
* Update black formatting by @jkppr in [#3031](https://github.com/google/timesketch/pull/3031)
* Timesketch API client: Adding type check to prevent error. by @jkppr in [#3030](https://github.com/google/timesketch/pull/3030)
* Fix double escaping in sigma_util causing yaml.parser.ParserError by @lo-chr in [#3028](https://github.com/google/timesketch/pull/3028)
* UI build 20240207 by @jkppr in [#3035](https://github.com/google/timesketch/pull/3035)

### New Contributors
* @lo-chr made their first contribution in [#3028](https://github.com/google/timesketch/pull/3028)

**Full Changelog**: [20231206...20240207](https://github.com/google/timesketch/compare/20231206...20240207)

## Version 20231206
Released: 2023-12-06

### What's Changed
#### ✨ Features

* Left panel timeline management by @Annoraaq in [#2999](https://github.com/google/timesketch/pull/2999)
* Extract Windows log event data message attributes by @roshanmaskey in [#2910](https://github.com/google/timesketch/pull/2910)
* Highlight DFIQ context card by @berggren in [#2996](https://github.com/google/timesketch/pull/2996)
* "Add to Threat Intelligence" via context links by @jkppr in [#2980](https://github.com/google/timesketch/pull/2980)
* Adding a copy action to filter chips by @JohannesLks in [#2990](https://github.com/google/timesketch/pull/2990)

#### 🐞 Fixes

* API client: Return all field for analysis sessions by @tomchop in [#2504](https://github.com/google/timesketch/pull/2504)
* Introduce (large) CSV import in e2e tests by @jaegeral in [#2912](https://github.com/google/timesketch/pull/2912)
* Graph bug and layout fix by @berggren in [#2994](https://github.com/google/timesketch/pull/2994)
* Feature extraction config for BITS and Terminal Services by @roshanmaskey in [#2974](https://github.com/google/timesketch/pull/2974)
* Adjust default example text for yeti endpoint by @tomchop in [#2963](https://github.com/google/timesketch/pull/2963)
* Update to the windows deployment script by @coloradosarge in [#3000](https://github.com/google/timesketch/pull/3000)
* Adding and updating tooltips for icons by @jkppr in [#2983](https://github.com/google/timesketch/pull/2983)
* Fix hidden text by @jkppr in [#2965](https://github.com/google/timesketch/pull/2965)
* bug-fix for context links by @jkppr in [#2962](https://github.com/google/timesketch/pull/2962)
* Update for upgrade documentation by @jkppr in [#2967](https://github.com/google/timesketch/pull/2967)
* Removing old feature extractor analyzer by @jkppr in [#2969](https://github.com/google/timesketch/pull/2969)
* Update for the context_links documentation by @jkppr in [#2970](https://github.com/google/timesketch/pull/2970)
* Updating the feature extraction analyzer documentation by @jkppr in [#2973](https://github.com/google/timesketch/pull/2973)
* [tests] Add jsonl e2e tests by @jaegeral in [#2976](https://github.com/google/timesketch/pull/2976)
* Fix vue dependency issues with "v-calendar" by @jkppr in [#2989](https://github.com/google/timesketch/pull/2989)
* Mute noisy info logging in the feature extraction analyzer by @jkppr in [#2993](https://github.com/google/timesketch/pull/2993)
* New empty-state and left panel bugfix by @berggren in [#2991](https://github.com/google/timesketch/pull/2991)
* Update the analyzer timeline picker by @jkppr in [#3001](https://github.com/google/timesketch/pull/3001)
* UI build 20231206 by @jkppr in [#3002](https://github.com/google/timesketch/pull/3002)

### New Contributors
* @JohannesLks made their first contribution in [#2990](https://github.com/google/timesketch/pull/2990)
* @coloradosarge made their first contribution in [#3000](https://github.com/google/timesketch/pull/3000)

**Full Changelog**: [20231025...20231206](https://github.com/google/timesketch/compare/20231025...20231206)

## Version 20231025
Released: 2023-10-25

### ⚠️ Note
Upgrading to this Timesketch version requires a database upgrade!

See https://timesketch.org/guides/admin/upgrade/ for more details.

### What's Changed
#### ✨ Features
* Unfurl integration by @jkppr in https://github.com/google/timesketch/pull/2897
* DFIQ context in SearchHistory by @berggren in https://github.com/google/timesketch/pull/2957
* Multi analyzer result support by @jkppr in https://github.com/google/timesketch/pull/2894
* Add intelligence command to the CLI client by @jaegeral in https://github.com/google/timesketch/pull/2864
* Update yeti analyzer by @tomchop in https://github.com/google/timesketch/pull/2930
* SSL/TLS support and authentication for SMTP by @fazledyn-or in https://github.com/google/timesketch/pull/2940

#### 🐞 Fixes

* Filter chip fixes by @jkppr in https://github.com/google/timesketch/pull/2893
* Fix CSV upload without timestamp_desc by @jkppr in https://github.com/google/timesketch/pull/2896
* Bump cryptography from 41.0.3 to 41.0.4 by @dependabot in https://github.com/google/timesketch/pull/2904
* Deprecate Sigma status CSV usage from code by @jaegeral in https://github.com/google/timesketch/pull/2913
* Fix missing plaso_formatters by @jkppr in https://github.com/google/timesketch/pull/2933
* Refactor base layout by @berggren in https://github.com/google/timesketch/pull/2929
* Fix #2908 tagger bug by @jkppr in https://github.com/google/timesketch/pull/2935
* Adjusting regular expressions for features extraction by @tomchop in https://github.com/google/timesketch/pull/2932
* Documentation - timesketch_client.TimesketchApi in api client documentation by @jaegeral in https://github.com/google/timesketch/pull/2938
* Improvements to the Yeti analyzer by @tomchop in https://github.com/google/timesketch/pull/2942
* Truncate timeline names in analyzer results by @jkppr in https://github.com/google/timesketch/pull/2945
* API client method to delete Sigma rule by @jaegeral in https://github.com/google/timesketch/pull/2924
* Fix missing sketchId in Search.vue by @jkppr in https://github.com/google/timesketch/pull/2955
* Copy saved search ID by @jkppr in https://github.com/google/timesketch/pull/2956
* Support emojis in new UI by @NightAcrobat777 in https://github.com/google/timesketch/pull/2951
* Instantiate side panel only once by @berggren in https://github.com/google/timesketch/pull/2949
* Unit test to ensure invalid timestamp conversions do not occur by @bwhelan212 in https://github.com/google/timesketch/pull/2954
* Sanitise HTML from Unfurl by @berggren in https://github.com/google/timesketch/pull/2959
* Context link backwards compatibility & sanitation by @jkppr in https://github.com/google/timesketch/pull/2958

### New Contributors
* @NightAcrobat777 made their first contribution in https://github.com/google/timesketch/pull/2951
* @fazledyn-or made their first contribution in https://github.com/google/timesketch/pull/2940
* @bwhelan212 made their first contribution in https://github.com/google/timesketch/pull/2954

**Full Changelog**: https://github.com/google/timesketch/compare/20230913...20231025

## Version 20230913
Released: 2023-09-13

### What's Changed
#### ✨ Features
* Timeline info to the tsctl by @jaegeral in https://github.com/google/timesketch/pull/2870
* Feature extraction for TI data in "Windows-Bits-Client" events by @jkppr in https://github.com/google/timesketch/pull/2873
* OpenSearch 2.x support by @berggren in https://github.com/google/timesketch/pull/2876
* Export query result to CSV by @berggren in https://github.com/google/timesketch/pull/2882
* Support overriding/extending Plaso formatter definitions by @berggren in https://github.com/google/timesketch/pull/2881
* Event attribute include / exclude filters by @jkppr in https://github.com/google/timesketch/pull/2888
* Adding tag filter chips to sigma rules by @jkppr in https://github.com/google/timesketch/pull/2890

#### 🐞 Fixes
* correct paramters in cli attributes method by @jaegeral in https://github.com/google/timesketch/pull/2863
* Update troubleshooting.md by @jaegeral in https://github.com/google/timesketch/pull/2866
* Update Date chip to support milliseconds by @sydp in https://github.com/google/timesketch/pull/2867
* Allow API port to listen on localhost by @tomchop in https://github.com/google/timesketch/pull/2875
* Loading indicator active analyzers by @Annoraaq in https://github.com/google/timesketch/pull/2855
* Bump cryptography from 41.0.2 to 41.0.3 by @dependabot in https://github.com/google/timesketch/pull/2858
* Add TTY check for providing missing config values by @ramo-j in https://github.com/google/timesketch/pull/2850
* Don't exit with error if user chooses not to start timesketch by @pemontto in https://github.com/google/timesketch/pull/2857
* Run analyzers only once per timeline by @jkppr in https://github.com/google/timesketch/pull/2883
* Tag list refactor & bug fixes by @jkppr in https://github.com/google/timesketch/pull/2886
* refactor verbose analyzer output by @jkppr in https://github.com/google/timesketch/pull/2885
* Analyzer Output UI update by @jkppr in https://github.com/google/timesketch/pull/2887
* Search History graph cleanup by @berggren in https://github.com/google/timesketch/pull/2891

---

## Version 20230721
Released: 2023-07-21

### What's Changed
#### ✨ Features
* Show selected event in context view by @berggren in https://github.com/google/timesketch/pull/2811
* Delete sketch and list archived sketches by @berggren in https://github.com/google/timesketch/pull/2817
* Add json and tab output to CLI client by @jaegeral in https://github.com/google/timesketch/pull/2818
* Add `output-format` as cli wide argument by @jaegeral in https://github.com/google/timesketch/pull/2819
* Add timesketch analyze results to the CLI client by @jaegeral in https://github.com/google/timesketch/pull/2846
* Manage sketch attributes in the CLI client by @jaegeral in https://github.com/google/timesketch/pull/2841
* Support OpenSearch queries in DFIQ by @berggren in https://github.com/google/timesketch/pull/2822
* Preserve user defined filters by @berggren in https://github.com/google/timesketch/pull/2840
* Support event list sorting (asc/desc) by @berggren in https://github.com/google/timesketch/pull/2843

#### 🐞 Fixes
* Consitent forms and cleaned up XML viewer by @berggren in https://github.com/google/timesketch/pull/2812
* Remove ports from e2e-tests by @berggren in https://github.com/google/timesketch/pull/2816
* Update Account Finder Analyzer by @jkppr in https://github.com/google/timesketch/pull/2803
* Adding hashR user documentation by @jkppr in https://github.com/google/timesketch/pull/2824
* Update tsdev.sh to add creation of api client and cli client by @jaegeral in https://github.com/google/timesketch/pull/2830
* fix mkdocs warnings by @jkppr in https://github.com/google/timesketch/pull/2832
* fix docs formatting by @jkppr in https://github.com/google/timesketch/pull/2833
* Add a test case for conditions with multiple words in a Sigma rule by @jaegeral in https://github.com/google/timesketch/pull/2835
* Always set active timelines by @berggren in https://github.com/google/timesketch/pull/2838
* Rework comments by @jkppr in https://github.com/google/timesketch/pull/2845
* Documentation updates for analyzers  by @jkppr in https://github.com/google/timesketch/pull/2851
* Update hashR analyzer by @jkppr in https://github.com/google/timesketch/pull/2820
* [CLI] refactor to use central output-format by @jaegeral in https://github.com/google/timesketch/pull/2821

#### 🏠 Internal
Dependency updates

* Upgrade to PyYAML 6.0.1 and NodeJS 18 by @berggren in https://github.com/google/timesketch/pull/2853
* Bump cryptography from 41.0.0 to 41.0.2 by @dependabot in https://github.com/google/timesketch/pull/2844

---

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
