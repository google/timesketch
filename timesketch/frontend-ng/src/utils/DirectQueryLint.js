/*
Copyright 2026 Google Inc. All rights reserved.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
*/

/*
Static checks for PPL and SQL before a query is sent.

Every rule here encodes a failure seen against a real cluster. The point is to
answer at the keyboard rather than after a round trip, and to catch the case
that is worse than an error: a query that succeeds while quietly meaning
something else.

Rules never block a run. OpenSearch is the authority on its own syntax, and a
false positive that stopped a valid query would be worse than a stray warning.
*/

// Rows the analyst should fix before trusting the output.
const ERROR = 'error'
// Rows that will run, but may mislead or scan far more than intended.
const WARNING = 'warning'

// Timesketch maps only datetime and timesketch_label explicitly, so every
// other field takes whatever type OpenSearch infers from the data a timeline
// happens to carry. A field that looks numeric can therefore be text in one
// deployment and a number in the next. Only timestamp is certain, because
// ingest coerces it to an int before it is ever written.
const NUMERIC_FIELDS = ['timestamp']

// Aggregation calls that cannot be named directly in a PPL `sort`.
const PPL_AGGREGATIONS = 'count|sum|avg|min|max|stddev|var|percentile|distinct_count|dc'

/**
 * Blank out string literals so keyword and operator patterns cannot match
 * inside user text. Length is preserved to keep offsets meaningful.
 */
function maskLiterals(query) {
  return query.replace(/'[^']*'|"[^"]*"/g, (match) => match[0] + ' '.repeat(match.length - 2) + match[0])
}

function finding(severity, message, hint) {
  return { severity, message, hint }
}

function lintPpl(query, masked) {
  const findings = []

  if (/^\s*\|/.test(query)) {
    findings.push(
      finding(
        ERROR,
        'Query starts with a pipe.',
        'The index and a leading pipe are added for you. Start with the command itself, such as "stats count()".'
      )
    )
  }

  if (/^\s*source\s*=/i.test(query)) {
    findings.push(
      finding(
        WARNING,
        'Query names its own source.',
        'The sketch index is added automatically. A source pointing anywhere else is rejected.'
      )
    )
  }

  // `sort` takes field names and aliases only; a function call is a parse error.
  const sortStage = masked.match(/\|\s*sort\s+([^|]*)/i)
  if (sortStage && new RegExp(`\\b(${PPL_AGGREGATIONS})\\s*\\(`, 'i').test(sortStage[1])) {
    findings.push(
      finding(
        ERROR,
        'Sorting on an aggregation call.',
        'Alias the aggregation first, then sort on the alias: "stats count() as cnt by host | sort - cnt".'
      )
    )
  }

  // `stats` wants the aggregation expression before the `by` clause.
  if (/\bstats\s+by\b/i.test(masked)) {
    findings.push(
      finding(
        ERROR,
        'The "by" clause comes before the aggregation.',
        'Put the aggregation first: "stats count() as cnt by hostname".'
      )
    )
  }

  if (/\blimit\b/i.test(masked)) {
    findings.push(
      finding(ERROR, 'LIMIT is not a PPL command.', 'Use "head N" to cap the number of rows.')
    )
  }

  return findings
}

function lintSql(query, masked) {
  const findings = []

  if (/\bfrom\b/i.test(masked)) {
    findings.push(
      finding(
        WARNING,
        'Query includes its own FROM clause.',
        'The sketch index is added automatically. A FROM naming anything else is rejected.'
      )
    )
  }

  if (/\border\s+by\b/i.test(masked) && !/\blimit\b/i.test(masked)) {
    findings.push(
      finding(
        WARNING,
        'ORDER BY without a LIMIT.',
        'OpenSearch sorts the whole result set in memory and may return nothing. Add a LIMIT.'
      )
    )
  }

  // An unquoted number cannot match a field mapped as text, which numeric
  // looking fields commonly are. Only a warning: whether it holds depends on
  // the mapping of the timeline being queried, which this cannot see.
  const numericComparison = new RegExp(`\\b(?!(?:${NUMERIC_FIELDS.join('|')})\\b)(\\w+)\\s*(?:=|!=|<>)\\s*\\d+`, 'i')
  const match = masked.match(numericComparison)
  if (match) {
    findings.push(
      finding(
        WARNING,
        `Comparing ${match[1]} to an unquoted number.`,
        `Fields that look numeric are often mapped as text, where an unquoted number never matches. If this returns nothing, quote the value: ${match[1]} = '...'.`
      )
    )
  }

  return findings
}

/**
 * Checks that apply to both dialects.
 */
function lintShared(query, masked) {
  const findings = []

  // A leading wildcard cannot use the index and scans every value.
  if (/like\s+'%[^']*%'/i.test(query)) {
    findings.push(
      finding(
        WARNING,
        'LIKE pattern is wildcarded on both sides.',
        'Anchor one end where you can ("UserLoginFailed%" or "%@example.com"); a double-sided wildcard scans the whole field.'
      )
    )
  }

  return findings
}

/**
 * Return an array of {severity, message, hint} for a query.
 *
 * @param {string} language 'ppl' or 'sql'
 * @param {string} query the raw query text
 */
export function lintDirectQuery(language, query) {
  if (!query || !query.trim()) return []

  const masked = maskLiterals(query)
  const dialect = language === 'sql' ? lintSql(query, masked) : lintPpl(query, masked)
  return [...dialect, ...lintShared(query, masked)]
}

export const LINT_ERROR = ERROR
export const LINT_WARNING = WARNING
