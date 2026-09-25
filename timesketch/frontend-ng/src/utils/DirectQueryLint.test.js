import { describe, it, expect } from 'vitest'
import { lintDirectQuery, LINT_ERROR, LINT_WARNING } from './DirectQueryLint.js'

function messages(language, query) {
  return lintDirectQuery(language, query).map((finding) => finding.message)
}

function severities(language, query) {
  return lintDirectQuery(language, query).map((finding) => finding.severity)
}

describe('lintDirectQuery', () => {
  it('says nothing about an empty query', () => {
    expect(lintDirectQuery('ppl', '')).toEqual([])
    expect(lintDirectQuery('ppl', '   ')).toEqual([])
  })

  it('accepts a well formed PPL pipeline', () => {
    expect(lintDirectQuery('ppl', 'stats count() as cnt by data_type | sort - cnt | head 10')).toEqual([])
  })

  it('accepts a well formed SQL statement', () => {
    const query = "SELECT data_type, COUNT(*) AS cnt WHERE hostname = 'srv1' GROUP BY data_type LIMIT 10"
    expect(lintDirectQuery('sql', query)).toEqual([])
  })
})

describe('PPL rules', () => {
  it('flags a leading pipe', () => {
    expect(messages('ppl', '| stats count()')).toContain('Query starts with a pipe.')
    expect(severities('ppl', '| stats count()')).toContain(LINT_ERROR)
  })

  it('warns about naming the source', () => {
    expect(messages('ppl', 'source=myindex | head 1')).toContain('Query names its own source.')
    expect(severities('ppl', 'source=myindex | head 1')).toContain(LINT_WARNING)
  })

  it('flags sorting on an aggregation call', () => {
    expect(messages('ppl', 'stats count() by host | sort - count()')).toContain(
      'Sorting on an aggregation call.'
    )
  })

  it('accepts sorting on an alias', () => {
    expect(messages('ppl', 'stats count() as cnt by host | sort - cnt')).toEqual([])
  })

  it('flags the by clause coming before the aggregation', () => {
    expect(messages('ppl', 'stats by hostname count() as cnt')).toContain(
      'The "by" clause comes before the aggregation.'
    )
  })

  it('flags LIMIT, which PPL does not have', () => {
    expect(messages('ppl', 'stats count() as cnt by host | sort - cnt | LIMIT 10')).toContain(
      'LIMIT is not a PPL command.'
    )
  })

  it('ignores keywords inside string literals', () => {
    // "limit" here is data, not a command.
    expect(messages('ppl', "where message like 'rate limit exceeded' | head 5")).toEqual([])
  })

})

describe('SQL rules', () => {
  it('warns about an explicit FROM clause', () => {
    expect(messages('sql', 'SELECT * FROM myindex LIMIT 1')).toContain(
      'Query includes its own FROM clause.'
    )
  })

  it('warns about ORDER BY without LIMIT', () => {
    expect(messages('sql', 'SELECT data_type ORDER BY data_type')).toContain(
      'ORDER BY without a LIMIT.'
    )
  })

  it('flags an unquoted number compared against a field that may be text', () => {
    expect(messages('sql', 'SELECT * WHERE event_identifier = 4624 LIMIT 5')).toContain(
      'Comparing event_identifier to an unquoted number.'
    )
  })

  it('only warns about an unquoted number, since the mapping decides', () => {
    expect(severities('sql', 'SELECT * WHERE event_identifier = 4624 LIMIT 5')).toEqual([LINT_WARNING])
  })

  it('allows an unquoted number on timestamp, which ingest always writes as an int', () => {
    expect(messages('sql', 'SELECT * WHERE timestamp = 1775520000000000 LIMIT 5')).toEqual([])
  })

  it('does not flag a number inside a string literal', () => {
    expect(messages('sql', "SELECT * WHERE message = '4624' LIMIT 5")).toEqual([])
  })
})

describe('shared rules', () => {
  it('warns about a double sided LIKE wildcard', () => {
    expect(messages('ppl', "where message like '%error%' | head 10")).toContain(
      'LIKE pattern is wildcarded on both sides.'
    )
  })

  it('accepts an anchored LIKE pattern', () => {
    expect(messages('ppl', "where message like 'UserLoginFailed%' | head 10")).toEqual([])
  })
})
