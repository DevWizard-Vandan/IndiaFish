/**
 * 临时存储待上传的文件和需求
 * 用于首页点击启动引擎后立即跳转，在Process页面再进行API调用
 */
import { reactive } from 'vue'

const state = reactive({
  files: [],
  simulationRequirement: '',
  seedMode: 'document',
  underlying: 'NIFTY',
  isPending: false
})

export function setPendingUpload(files, requirement, options = {}) {
  state.files = files
  state.simulationRequirement = requirement
  state.seedMode = options.seedMode || 'document'
  state.underlying = options.underlying || 'NIFTY'
  state.isPending = true
}

export function getPendingUpload() {
  return {
    files: state.files,
    simulationRequirement: state.simulationRequirement,
    seedMode: state.seedMode,
    underlying: state.underlying,
    isPending: state.isPending
  }
}

export function clearPendingUpload() {
  state.files = []
  state.simulationRequirement = ''
  state.seedMode = 'document'
  state.underlying = 'NIFTY'
  state.isPending = false
}

export default state
