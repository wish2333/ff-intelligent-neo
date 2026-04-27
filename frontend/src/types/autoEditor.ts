export interface AeStatus {
  available: boolean
  compatible: boolean
  version: string
  path: string
}

export interface AdvancedOptions {
  cutOutRanges: string[]
  addInRange: string[]
  setActionRanges: string[]
  frameRate: string
  sampleRate: string
  resolution: string
  vn: boolean
  an: boolean
  sn: boolean
  dn: boolean
  videoCodec: string
  audioCodec: string
  videoBitrate: string
  audioBitrate: string
  crf: string
  audioLayout: string
  audioNormalize: string
  noCache: boolean
  open: boolean
  faststart: boolean
  fragmented: boolean
  outputExtension: string
}

export interface EncoderLists {
  video: string[]
  audio: string[]
  subtitle: string[]
  other: string[]
}
