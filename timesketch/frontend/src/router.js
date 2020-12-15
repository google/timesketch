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
import SketchOverview from './views/SketchOverview'
import SketchManage from './views/SketchManage'
import SketchManageViews from "./views/SketchManageViews"
import SketchManageTimelines from "./views/SketchManageTimelines"
import SketchExplore from './views/SketchExplore'
import SketchGraph from './views/SketchGraph'
import SketchGraphOverview from './views/SketchGraphOverview'
import SketchGraphExplore from './views/SketchGraphExplore'
import SketchStory from './views/SketchStory'
import SketchStoryOverview from './views/SketchStoryOverview'
import SketchStoryContent from './views/SketchStoryContent'

Vue.use(VueRouter)

const routes = [
  {
    name: 'Home',
    path: '/',
    component: Home
  },
  {
    // Sketch
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
        name: 'SketchExplore',
        component: SketchExplore,
        props: true
      },
      {
        path: 'graph',
        component: SketchGraph,
        props: true,
        children: [
          {
            path: '',
            name: 'SketchGraphOverview',
            component: SketchGraphOverview
          },
          {
            path: 'explore',
            name: 'SketchGraphExplore',
            component: SketchGraphExplore,
            props: true
          }]
      },
      {
        path: 'story',
        component: SketchStory,
        props: true,
        children: [
          {
            path: '',
            name: 'SketchStoryOverview',
            component: SketchStoryOverview
          },
          {
            path: ':storyId',
            name: 'SketchStoryContent',
            component: SketchStoryContent,
            props: true
          }]
      },
      {
        path: 'manage',
        component: SketchManage,
        props: true,
        children: [
          {
            path: 'views',
            name: 'SketchManageViews',
            component: SketchManageViews
          },
          {
            path: 'timelines',
            name: 'SketchManageTimelines',
            component: SketchManageTimelines
          }]
      }
    ]
  }
]

export default new VueRouter({
  mode: 'history',
  routes
})
