#!/usr/bin/env bash

set -e

# Add web user
if ! tsctl list-users | grep -q "${TIMESKETCH_USER}"; then
  tsctl create-user --password "${TIMESKETCH_PASSWORD}" "${TIMESKETCH_USER}"
fi

# Add Sigma rules
if [ -d "/usr/local/src/sigma/.git" ]; then
  git -C /usr/local/src/sigma fetch --depth=1
  git -C /usr/local/src/sigma reset --hard "$(git -C /usr/local/src/sigma rev-parse --abbrev-ref --symbolic-full-name @{u})"
else
  git clone --depth 1 https://github.com/SigmaHQ/sigma /usr/local/src/sigma
fi

aggregated_rules_dir="$(mktemp -d)"

# Create symbolic links to the rule files specified in sigma_rules.txt
while IFS= read -r rule_file_path; do
  if [ -f "${rule_file_path}" ]; then
    ln -s "${rule_file_path}" "${aggregated_rules_dir}/"
  else
    echo "Skipping non existing Sigma rule: ${rule_file_path}"
  fi
done < "${TIMESKETCH_CONF_DIR}/sigma_rules.txt"

# Loading all sigma rules at once
tsctl import-sigma-rules "${aggregated_rules_dir}"
rm -rf "${aggregated_rules_dir}"
