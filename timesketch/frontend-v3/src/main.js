/**
 * main.js
 *
 * Bootstraps Vuetify and other plugins then mounts the App`
 */

// Plugins
import { registerPlugins } from "@/plugins";

// Components
import App from "./App.vue";
import {
  initialLetter,
  shortDateTime,
  timeSince,
  compactBytes,
  compactNumber,
  formatTimestamp,
  toISO8601,
  formatSeconds,
  formatLabelText,
} from "./filters.js";
import { snackBarMixin } from "./mixins.js";
import { setupCalendar } from "v-calendar";

// Composables
import { createApp } from "vue";

const app = createApp(App);

app.use(setupCalendar, {});

registerPlugins(app);

app.mount("#app");
app.mixin(snackBarMixin);

app.config.globalProperties.$filters = {
  initialLetter,
  shortDateTime,
  timeSince,
  compactNumber,
  formatTimestamp,
  toISO8601,
  formatSeconds,
  formatLabelText,
  compactBytes,
};
