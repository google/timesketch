import 'font-awesome/css/font-awesome.css'
import * as $ from 'jquery'
(window as any).jQuery = $
import 'twitter-bootstrap-3.0.0/dist/css/bootstrap.css'
import 'twitter-bootstrap-3.0.0/dist/js/bootstrap.js'
import 'medium-editor/dist/css/medium-editor.css'
import 'medium-editor/dist/css/themes/default.css'

import 'zone.js/dist/zone'
import 'zone.js/dist/long-stack-trace-zone'
import 'zone.js/dist/async-test'
import 'zone.js/dist/fake-async-test'
import 'zone.js/dist/sync-test'
import 'zone.js/dist/proxy'
import 'zone.js/dist/jasmine-patch'

import angular from 'angularjs-for-webpack'
import {downgradeModule} from '@angular/upgrade/static'

import 'css/ts.css'
import {tsAppModule, AppModule} from 'app.module'

// require all modules ending in ".spec.ts" from the current directory and
// all subdirectories
const tests_context = (require as any).context(".", true, /\.spec\.ts$/)
tests_context.keys().forEach(tests_context)
