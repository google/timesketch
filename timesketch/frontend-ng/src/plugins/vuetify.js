import Vue from 'vue'
import Vuetify from 'vuetify'
import 'vuetify/dist/vuetify.min.css'

Vue.use(Vuetify, {
  options: {
    customProperties: true,
  },
})

const opts = { theme: { dark: false } }

export default new Vuetify(opts)
