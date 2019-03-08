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
module.exports = {
  lintOnSave: false,
  publicPath: '/dist/',
  pages: {
    home: {
      entry: 'src/apps/home/main.js',
      template: 'src/assets/index.html',
      title: 'Home',
      chunks: ['chunk-vendors', 'chunk-common', 'home']
    },
    overview: {
      entry: 'src/apps/sketch/overview/main.js',
      template: 'src/assets/index.html',
      title: 'Overview',
      chunks: ['chunk-vendors', 'chunk-common', 'overview']
    },
    explore: {
      entry: 'src/apps/sketch/explore/main.js',
      template: 'src/assets/index.html',
      title: 'Explore',
      chunks: ['chunk-vendors', 'chunk-common', 'explore']
    }
  }
}
