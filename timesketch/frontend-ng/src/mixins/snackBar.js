
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
import Vue from 'vue'

const defaultTimeout = 5000
const defaultSnackBar = {
    "message": "",
    "color": "info",
    "timeout": defaultTimeout
}

// These methids will be available to all components without any further imports.
Vue.mixin({
    methods: {
        successSnackBar(message) {
            let snackbar = defaultSnackBar
            snackbar.message = message
            snackbar.color = "success"
            this.$store.dispatch('setSnackBar', snackbar)
        },
        errorSnackBar(message) {
            let snackbar = defaultSnackBar
            snackbar.message = message
            snackbar.color = "error"
            this.$store.dispatch('setSnackBar', snackbar)
        },
        infoSnackBar(message) {
          let snackbar = defaultSnackBar
          snackbar.message = message
          snackbar.color = "info"
          snackbar.timeout = 2000
          this.$store.dispatch('setSnackBar', snackbar)
      },
    }
})
