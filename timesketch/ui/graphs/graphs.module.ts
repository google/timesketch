/*
Copyright 2017 Google Inc. All rights reserved.

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
import angular from 'angularjs-for-webpack'
import {NgModule} from '@angular/core'
import {CommonModule} from '@angular/common'
import {FormsModule} from '@angular/forms'
import {downgradeComponent} from '@angular/upgrade/static'

import {CytoscapeComponent} from './cytoscape.component'
import {CypherQueryComponent} from './cypher-query.component'
import {GraphViewComponent} from './graph-view.component'
import {CytoscapeSettingsComponent} from './cytoscape-settings.component'
import {GraphActionsComponent} from './graph-actions.component'
import {EdgeDetailComponent} from './edge-detail.component'
import {NodeDetailComponent} from './node-detail.component'
import {MainComponent} from './main.component'
import {ApiModule} from '../api/api.module'

export const tsGraphsModule = angular.module('timesketch.graphs', [])
  .directive('tsGraphsMain', downgradeComponent({
      component: MainComponent, propagateDigest: false,
  }))

@NgModule({
  imports: [CommonModule, FormsModule, ApiModule],
  declarations: [
    CytoscapeComponent, CypherQueryComponent, GraphViewComponent,
    CytoscapeSettingsComponent, GraphActionsComponent, EdgeDetailComponent,
    NodeDetailComponent, MainComponent,
  ],
  entryComponents: [MainComponent],
})
export class GraphsModule {}
