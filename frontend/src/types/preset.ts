/** Preset type definitions. */

import type { TaskConfigDTO } from "./config"

export interface PresetDTO {
  id: string
  name: string
  description: string
  config: TaskConfigDTO
  is_default: boolean
}
