import * as $ from 'jquery'
import angular from 'angularjs-for-webpack'
import {downgradeModule} from '@angular/upgrade/static'

import {tsAppModule, AppModule} from 'app.module'

$(function () {

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
