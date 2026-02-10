export function getPriorityFromLabels(labels) {
  if (!labels || !Array.isArray(labels)) {
    return null
  }
  const priorityPrefix = '__ts_priority_'
  const priorityLabel = labels.find((label) => label.name.startsWith(priorityPrefix))
  return priorityLabel ? priorityLabel.name.replace(priorityPrefix, '') : null
}
