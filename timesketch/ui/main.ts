import 'font-awesome/css/font-awesome.css'
import * as $ from 'jquery'
(window as any).jQuery = $
import 'twitter-bootstrap-3.0.0/dist/css/bootstrap.css'
import 'twitter-bootstrap-3.0.0/dist/js/bootstrap.js'
import 'medium-editor/dist/css/medium-editor.css'
import 'medium-editor/dist/css/themes/default.css'

import angular from 'angularjs-for-webpack'

import 'css/ts.css'
import {tsAppModule} from 'app.module'

angular.element(function() {
  angular.bootstrap(document.body, [tsAppModule.name])
})
