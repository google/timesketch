/**
 * router/index.ts
 *
 * Automatic routes for `./src/pages/*.vue`
 */

// Composables
import { createRouter, createWebHistory } from "vue-router/auto";

// Import the default layout that wraps all other views with an AppBar etc.
import Default from "@/layouts/Default";

// Import App views
import Home from "@/views/Home.vue";
import Sketch from "@/views/Sketch.vue";
import Canvas from "@/components/Canvas.vue";

// Routes
const routes = [
  {
    path: "/",
    component: Default,
    children: [
      {
        path: "",
        name: "home",
        component: Home,
        props: true,
      },
    ]
  },
  {
    path: '/sketch/:sketchId',
    component: Sketch,
    props: true,
    children: [
      {
        path: 'explore',
        name: 'Explore',
        component: Canvas,
        props: true,
      },
      {
        path: 'example',
        name: 'Example',
        component: Canvas,
        props: true,
      },

    ]
  },
];

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
});

// Workaround for https://github.com/vitejs/vite/issues/11804
router.onError((err, to) => {
  if (err?.message?.includes?.("Failed to fetch dynamically imported module")) {
    if (!localStorage.getItem("vuetify:dynamic-reload")) {
      console.log("Reloading page to fix dynamic import error");
      localStorage.setItem("vuetify:dynamic-reload", "true");
      location.assign(to.fullPath);
    } else {
      console.error("Dynamic import error, reloading page did not fix it", err);
    }
  } else {
    console.error(err);
  }
});

router.isReady().then(() => {
  localStorage.removeItem("vuetify:dynamic-reload");
});

export default router;
