import {PredefinedQuery} from './models'

export const predefinedQueries: PredefinedQuery[] = [
  {
    name: 'Interactive logins',
    query: 'MATCH (user:WindowsADUser)-[r1:ACCESS]->(m1:WindowsMachine) WHERE r1.method = "Interactive" RETURN *',
  },
  {
    name: 'Entire graph',
    query: 'MATCH (a)-[e]->(b) RETURN *',
  },
]
