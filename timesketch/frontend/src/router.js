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
import Overview from './components/Sketch/Overview'
import Manage from './components/Sketch/Manage'
import ManageViews from "./components/Sketch/Manage/ManageViews"
import ManageTimelines from "./components/Sketch/Manage/ManageTimelines"
import Explore from './components/Sketch/Explore'
import Story from './components/Sketch/Story'
import StoryOverview from './components/Sketch/Story/StoryOverview'
import StoryContent from './components/Sketch/Story/StoryContent'

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
        name: 'Overview',
        component: Overview
      },
      {
        path: 'explore',
        name: 'Explore',
        component: Explore,
        props: true
      },
      {
        path: 'story',
        component: Story,
        props: true,
        children: [
          {
            path: '',
            name: 'StoryOverview',
            component: StoryOverview
          },
          {
            path: ':storyId',
            name: 'StoryContent',
            component: StoryContent,
            props: true
          }]
      },
      {
        path: 'manage',
        component: Manage,
        props: true,
        children: [
          {
            path: 'views',
            name: 'ViewsPage',
            component: ManageViews
          },
          {
            path: 'timelines',
            name: 'TimelinesPage',
            component: ManageTimelines
          }]
      }
    ]
  }
]

export default new VueRouter({
  mode: 'history',
  routes
})
