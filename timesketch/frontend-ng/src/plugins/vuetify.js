// import '@mdi/font/css/materialdesignicons.css'
import {createVuetify} from 'vuetify'
// import 'vuetify/dist/vuetify.min.css'
import 'vuetify/styles'

import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'


const opts = {
    // customProperties: true,
  // theme: { dark: false },
  // icons: { iconfont: 'mdi' },
  components,
  directives
}

const vuetify = createVuetify({ opts })

export default vuetify;
