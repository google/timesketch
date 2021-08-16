# Overview
 
This document will give a human readable view on the planned future for Timesketch.
The actual implementation of the dedicated feature is tracked and discussed in individual Github Issues.
 
# Fineprint
 
As much as we try to stick to the roadmap, the development of the project will remain fluid and drastic changes in resource allocation might happen, new ideas might pop up or old ideas might become obsolete.
 
# How to contribute to the roadmap
 
We invite users, developers from the entire community to provide feedback via e.g [Github issues] (https://github.com/google/timesketch/issues/new/choose), [Slack] (https://timesketch.org/community/resources/) or [Twitter](https://twitter.com/TimesketchProj)

To directly contribute to this roadmap create a PR and propose changes and explain the rationale behind your proposed changes.
 
## Sigma
 
[Sigma](https://github.com/SigmaHQ/sigma) has been a part of Timesketch since 2020 and the plan is to increase importance within Timesketch.
 
The vision for Sigma in Timesketch is to enable the Analyst to speed up the transition from an analyst's hypothesis to the actual forensic artifacts to support or invalidate the theory.
 
### 2021
- Provide UI to browse Sigma rules
- Provide UI to create / test new Sigma rules without require them to be stored on the server
- Timesketch Sigma analyzers performance tests / tuning (run 200 rules on 3 timelines with total 1m+ events)
- Improve the Sigma rule verifier tool and documentation to make it easier to filter out rules that are known to not work in Timesketch for various reasons.
### 2022
- Revisit storage of Sigma rules (file on disc vs. storing rules in database)
- Provide UI to cluster Sigma rules based on TTPs so analysts could start digging in data based on expected TTPs.
- UI functionality to enable / disable single Sigma rules
- Create special views based on Sigma analyzer hits e.g.:
    - persistence
    - logon events
### 2023 and beyond
- Enable analysts to create Sigma rules based on events
- Investigate if it would be possible and helpful if Sigma rules could be modified from the Timesketch UI.
 

