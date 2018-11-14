import {PredefinedQuery} from './models';

export const predefinedQueries: PredefinedQuery[] = [
  {
    name: 'Interactive logins',
    query: 'MATCH (user:WindowsADUser)-[r1:ACCESS]->(m1:WindowsMachine) WHERE r1.method = "Interactive"',
  },
  {
    name: 'Entire graph',
    query: 'MATCH (a)-[e]->(b)',
  },
  {
    name: 'Network logins in 20 minutes after interactive logins',
    query: `MATCH (user:WindowsADUser)-[r1:ACCESS]->(m1:WindowsMachine)-[r2:ACCESS]->(m2:WindowsMachine)
      WHERE r1.method IN ["Interactive", "CachedInteractive", "Unlock"]
      AND r1.timestamp < r2.timestamp < r1.timestamp + 60 * 20
    `,
  },
  {
    name: 'Services started in 20 minutes after interactive logins',
    query: `MATCH (user:WindowsADUser)-[r1:ACCESS]->(m1:WindowsMachine)<-[r2:START]-(s:WindowsService)-[h:HAS]->(i)
      WHERE r1.method IN ["Interactive", "CachedInteractive", "Unlock"]
      AND r1.timestamp < r2.timestamp < r1.timestamp + 60 * 20
    `,
  },
];
