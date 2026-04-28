import { createApp } from "vue"
import App from "./App.vue"
import router from "./router"
import i18n from "./i18n"
import "./style.css"

const app = createApp(App)
app.use(router).use(i18n)

app.config.errorHandler = (err, instance, info) => {
  console.error("[Vue Error]", err)
  console.error("[Error Info]", info)
  console.error("[Component]", instance?.$options?.name ?? instance?.$options?.__name ?? "unknown")
}

app.mount("#app")
