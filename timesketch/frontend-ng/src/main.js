/*
Copyright 2022 Google Inc. All rights reserved.

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
import App from './App.vue'
import { h , createApp } from 'vue'

import router from './router.js'
import store from './store.js'

import snackBar from '@/mixins/snackBar'
// import appComponents from './utils/RegisterAppComponents'

import $filters from './utils/GlobalFilters.js';


import {createVuetify} from 'vuetify'
// import 'vuetify/dist/vuetify.min.css'
import 'vuetify/styles'

import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'

require('./assets/main.scss')
require('./assets/markdown.scss')


const app = createApp({
  render: () => h(App),
})
// const opts = {
//     // customProperties: true,
//   // theme: { dark: false },
//   // icons: { iconfont: 'mdi' },
//   components,
//   directives
// }
app.use(store)
app.use(router)

const vuetify = createVuetify({
  components,
  directives
})
app.use(vuetify)

// app.mixin(snackBar)
// appComponents.forEach(([name, config]) => app.component(name, config))

// Third party
// app.use(require('vue-moment'))

// Disable warning during development
// Vue.config.productionTip = false
app.config.globalProperties.$filters = $filters;

app.config.globalProperties.$vuetify = vuetify;
app.mount('#app')

// new Vue({
//   router,
//   store,
//   vuetify,
//   render: (h) => h(App),
// }).$mount('#app')

