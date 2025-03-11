/**
 * main.js
 *
 * Bootstraps Vuetify and other plugins then mounts the App`
 */

// Plugins
import { registerPlugins } from "@/plugins";

// Components
import App from "./App.vue";
import {initialLetter, shortDateTime, timeSince} from "./filters.js";
import {snackBarMixin} from "./mixins.js";

// Composables
import { createApp } from "vue";

const app = createApp(App);

registerPlugins(app);

app.mount("#app");
app.mixin(snackBarMixin)

app.config.globalProperties.$filters = {
  initialLetter,
  shortDateTime,
  timeSince,
}
