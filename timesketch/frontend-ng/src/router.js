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
import Canvas from './views/Canvas'
import Sketch from './views/Sketch'

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
        redirect: { name: 'Explore' },
      },
      {
        path: 'explore',
        name: 'Explore',
        component: Canvas,
        props: true,
      },
      {
        path: 'intelligence',
        name: 'Intelligence',
        component: Canvas,
        props: true,
      },
      {
        path: 'sigma',
        component: Canvas,
        props: true,
        children: [
          {
            path: 'new',
            name: 'SigmaNewRule',
            component: Canvas,
            props: true,
          },
          {
            path: 'edit/:ruleId',
            name: 'SigmaEditRule',
            component: Canvas,
            props: true,
          },

        ]
      },
      {
        path: 'sigma/edit',
        name: 'SigmaEdit',
        component: Canvas,
        props: true,
      },

      {
        path: 'graph',
        name: 'Graph',
        component: Canvas,
        props: true,
      },
      {
        path: 'story/:storyId',
        name: 'Story',
        component: Canvas,
        props: true,
      },
      {
        path: 'analyzers',
        name: 'Analyze',
        component: Canvas,
        props: true,
      },
    ],
  },
]

export default new VueRouter({
  mode: 'history',
  routes,
})
