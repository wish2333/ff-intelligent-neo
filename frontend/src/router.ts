/**
 * Vue Router configuration (hash mode for pywebview compatibility).
 */

import { createRouter, createWebHashHistory } from "vue-router"

const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    {
      path: "/",
      redirect: "/task-queue",
    },
    {
      path: "/task-queue",
      name: "TaskQueue",
      component: () => import("./pages/TaskQueuePage.vue"),
    },
    {
      path: "/config",
      name: "CommandConfig",
      component: () => import("./pages/CommandConfigPage.vue"),
    },
    {
      path: "/audio-subtitle",
      name: "AudioSubtitle",
      component: () => import("./pages/AudioSubtitlePage.vue"),
    },
    {
      path: "/merge",
      name: "Merge",
      component: () => import("./pages/MergePage.vue"),
    },
    {
      path: "/custom-command",
      name: "CustomCommand",
      component: () => import("./pages/CustomCommandPage.vue"),
    },
    {
      path: "/settings",
      name: "Settings",
      component: () => import("./pages/SettingsPage.vue"),
    },
  ],
})

export default router
