import { createApp } from "vue"
import App from "./App.vue"
import router from "./router"
import i18n from "./i18n"
import "./style.css"

// Debug: intercept setAttribute to catch the exact call site of invalid attr name
const origSetAttribute = Element.prototype.setAttribute
Element.prototype.setAttribute = function (name: string, value: string) {
  if (name === '"') {
    console.trace("[DEBUG] setAttribute called with '\"' as name", { value, element: this.tagName })
    return
  }
  return origSetAttribute.call(this, name, value)
}

const app = createApp(App)
app.use(router).use(i18n)

app.config.errorHandler = (err, instance, info) => {
  console.error("[Vue Error]", err)
  console.error("[Error Info]", info)
  console.error("[Component]", instance?.$options?.name ?? instance?.$options?.__name ?? "unknown")
}

app.mount("#app")
