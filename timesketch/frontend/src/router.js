/*
Copyright 2019 Google Inc. All rights reserved.

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
import Vue from 'vue'
import VueRouter from 'vue-router'

import Home from './views/Home'
import Sketch from './views/Sketch'
import Overview from './views/Overview'
import Explore from './views/Explore'
import Graph from './views/Graph'
import GraphOverview from './views/GraphOverview'
import GraphExplore from './views/GraphExplore'
import Aggregate from './views/Aggregate'
import Analyze from './views/Analyze'
import Story from './views/Story'
import StoryOverview from './views/StoryOverview'
import StoryContent from './views/StoryContent'
import Attributes from './views/Attributes'
import Intelligence from './views/Intelligence'
import SavedSearches from './views/SavedSearches'
import Sigma from './views/Sigma'
import SigmaOverview from './views/SigmaOverview'


Vue.use(VueRouter)

const routes = [
  {
    name: 'Home',
    path: '/',
    component: Home,
  },
  {
    // Sketch
    path: '/sketch/:sketchId',
    component: Sketch,
    props: true,
    children: [
      {
        path: '',
        name: 'Overview',
        component: Overview,
      },
      {
        path: 'sigma',
        component: Sigma,
        props: true,
        children: [
          {
            path: '',
            name: 'SigmaOverview',
            component: SigmaOverview,
            props: true,
          },
        ],
      },
      {
        path: 'explore',
        name: 'Explore',
        component: Explore,
        props: true,
      },
      {
        path: 'graph',
        component: Graph,
        props: true,
        children: [
          {
            path: '',
            name: 'GraphOverview',
            component: GraphOverview,
          },
          {
            path: 'explore',
            name: 'GraphExplore',
            component: GraphExplore,
            props: true,
          },
        ],
      },
      {
        path: 'aggregate',
        name: 'Aggregate',
        component: Aggregate,
        props: true,
      },
      {
        path: 'analyzers',
        name: 'Analyze',
        component: Analyze,
        props: true,
      },
      {
        path: 'story',
        component: Story,
        props: true,
        children: [
          {
            path: '',
            name: 'StoryOverview',
            component: StoryOverview,
          },
          {
            path: ':storyId',
            name: 'StoryContent',
            component: StoryContent,
            props: true,
          },
        ],
      },
      {
        path: 'attributes',
        name: 'Attributes',
        component: Attributes,
        props: true,
      },
      {
        path: 'intelligence',
        name: 'Intelligence',
        component: Intelligence,
        props: true,
      },
      {
        path: 'savedsearches',
        name: 'SavedSearches',
        component: SavedSearches,
        props: true,
      },
    ],
  },
]

export default new VueRouter({
  mode: 'history',
  base: process.env.NODE_ENV === 'development' ? '/' : '/legacy/',
  routes,
})
