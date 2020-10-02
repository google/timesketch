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
import App from './App.vue'

import Buefy from 'buefy'
import 'buefy/dist/buefy.css'

import VueScrollTo from 'vue-scrollto'
import Multiselect from 'vue-multiselect'

import router from './router'
import store from './store'

import { library } from '@fortawesome/fontawesome-svg-core'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import {
  faChevronUp,
  faChevronDown,
  faSave,
  faUserEdit,
  faAngleLeft,
  faAngleRight,
  faArrowUp,
  faArrowDown
} from '@fortawesome/free-solid-svg-icons'
library.add(
  faChevronUp,
  faChevronDown,
  faSave,
  faUserEdit,
  faAngleLeft,
  faAngleRight,
  faArrowUp,
  faArrowDown
)
Vue.component('font-awesome-icon', FontAwesomeIcon)

require('./assets/main.scss')
require('./utils/RegisterAppComponents')
require('./utils/RegisterAppFilters')

// Create global EventBus to use in certain situations where performance is
// important and props/events are not optimal. Use with caution to not add
// unnecessary complexity.
const EventBus = new Vue();
export default EventBus;

Vue.use(require('vue-moment'))

Vue.use(Buefy, {
  defaultIconComponent: 'font-awesome-icon',
  defaultIconPack: 'fas',
});

Vue.use(VueScrollTo)
Vue.component('multiselect', Multiselect)


// Disable warning during development
Vue.config.productionTip = false

new Vue({
  router,
  store,
  render: h => h(App)
}).$mount('#app')
