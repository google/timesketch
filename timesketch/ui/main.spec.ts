// needed for angular async magic in unit tests
import 'zone.js/dist/zone'
import 'zone.js/dist/long-stack-trace-zone'
import 'zone.js/dist/async-test'
import 'zone.js/dist/fake-async-test'
import 'zone.js/dist/sync-test'
import 'zone.js/dist/proxy'
import 'zone.js/dist/jasmine-patch'

import './app.module'

// require all modules ending in ".spec.ts" from the current directory and
// all subdirectories
const tests_context = (require as any).context('.', true, /\.spec\.ts$/)
tests_context.keys().forEach(tests_context)
