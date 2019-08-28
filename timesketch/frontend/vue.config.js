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
  configureWebpack: config => {
    config.watchOptions = {
      aggregateTimeout: 500,
      ignored: /node_modules/
    }
  },
  pages: {
    index: {
      // entry for the page
      entry: 'src/main.js',
      // the source template
      template: 'public/index.html',
      // output as dist/index.html
      filename: 'index.html'
    },
    login: {
      // entry for the page
      entry: 'src/main.js',
      // the source template
      template: 'public/login.html',
      // output as dist/index.html
      filename: 'login.html'
    }
  }
}
