import '@mdi/font/css/materialdesignicons.css'
import {createVuetify} from 'vuetify'
import 'vuetify/dist/vuetify.min.css'


const opts = {
    customProperties: true,
  theme: { dark: false },
  icons: { iconfont: 'mdi' },
}

const vuetify = createVuetify({ opts })

export default vuetify;
