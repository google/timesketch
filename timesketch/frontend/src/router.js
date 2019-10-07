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

import Home from './components/Home'
import Sketch from './components/Sketch'
import SketchOverview from './components/SketchOverview'
import SketchExplore from './components/SketchExplore'
import SketchExploreSearch from './components/SketchExploreSearch'
import SketchExploreAggregation from './components/SketchExploreAggregation'
import SketchStory from './components/SketchStory'
import SketchStoryOverview from './components/SketchStoryOverview'
import SketchStoryContent from './components/SketchStoryContent'
import SketchTimelines from './components/SketchTimelines'
import SketchViews from './components/SketchViews'

Vue.use(VueRouter)

const routes = [
  {
    name: 'Home',
    path: '/',
    component: Home
  },
  {
    path: '/sketch/:sketchId',
    component: Sketch,
    props: true,
    children: [
      {
        path: '',
        name: 'SketchOverview',
        component: SketchOverview
      },
      {
        path: 'explore',
        component: SketchExplore,
        props: true,
        children: [
          {
            path: '',
            name: 'SketchExplore',
            component: SketchExploreSearch,
            props: true
          }
        ]
      },
      {
        path: 'timelines',
        name: 'SketchTimelines',
        component: SketchTimelines,
        props: true
      },
      {
        path: 'views',
        name: 'SketchViews',
        component: SketchViews,
        props: true
      },
      {
        path: 'story',
        component: SketchStory,
        props: true,
        children: [
          {
            path: '',
            name: 'SketchStory',
            component: SketchStoryOverview
          },
          {
            path: ':storyId',
            name: 'SketchStoryContent',
            component: SketchStoryContent,
            props: true
          }]
      }
    ]
  }
]

export default new VueRouter({
  mode: 'history',
  routes
})
