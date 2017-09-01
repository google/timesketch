import 'font-awesome/css/font-awesome.css'
import * as $ from 'jquery'
(window as any).jQuery = $
import 'twitter-bootstrap-3.0.0/dist/css/bootstrap.css'
import 'twitter-bootstrap-3.0.0/dist/js/bootstrap.js'
import 'medium-editor/dist/css/medium-editor.css'
import 'medium-editor/dist/css/themes/default.css'

import 'zone.js'

import angular from 'angularjs-for-webpack'
import {downgradeModule} from '@angular/upgrade/static'

import 'css/ts.css'
import {tsAppModule, AppModule} from 'app.module'

angular.element(function () {
  // @ngtools/webpack should automatically convert AppModule to
  // AppModuleNgFactory. We are casting it through any to make TypeScript happy
  // https://github.com/angular/angular-cli/blob/4586abd226090521f2470fa47a27553241415426/packages/%40ngtools/webpack/src/loader.ts#L267
  // this code rewriting by @ngtools/webpack is one big hack :(
  // for example, changing from "downgradeModule as any" to "AppModule as any"
  // will break everything because of the way the code transformation looks for
  // the bootstrapping code
  angular.bootstrap(document.body, [
    tsAppModule.name, (downgradeModule as any)(AppModule),
  ])
})
