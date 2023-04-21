#!/bin/sh
# This script can be used to download all the necessary Timesketch configuration
# files locally to this machine. Please run when you'd like to make some more
# changes to the config file before deployment.
set -o posix
set -e

echo -n "* Fetching configuration files.." 
GITHUB_BASE_URL="https://raw.githubusercontent.com/google/timesketch/master"
# Fetch default Timesketch config files
wget $GITHUB_BASE_URL/data/timesketch.conf -O configs/timesketch.conf
wget $GITHUB_BASE_URL/data/tags.yaml -O configs/tags.yaml
wget $GITHUB_BASE_URL/data/plaso.mappings -O configs/plaso.mappings
wget $GITHUB_BASE_URL/data/generic.mappings -O configs/generic.mappings
wget $GITHUB_BASE_URL/data/features.yaml -O configs/features.yaml
wget $GITHUB_BASE_URL/data/ontology.yaml -O configs/ontology.yaml
wget $GITHUB_BASE_URL/data/sigma_rule_status.csv -O configs/sigma_rule_status.csv
wget $GITHUB_BASE_URL/data/intelligence_tag_metadata.yaml -O configs/intelligence_tag_metadata.yaml
wget $GITHUB_BASE_URL/data/sigma_config.yaml -O configs/sigma_config.yaml
wget $GITHUB_BASE_URL/data/sigma/rules/lnx_susp_zmap.yml -O configs/lnx_susp_zmap.yml
wget $GITHUB_BASE_URL/data/context_links.yaml -O configs/context_links.yaml
wget $GITHUB_BASE_URL/data/scenarios/facets.yaml -O configs/facets.yaml
wget $GITHUB_BASE_URL/data/scenarios/questions.yaml -O configs/questions.yaml
wget $GITHUB_BASE_URL/data/scenarios/scenarios.yaml -O configs/scenarios.yaml
echo "OK"