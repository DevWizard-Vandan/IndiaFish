<template>
  <div class="main-view">
    <header class="app-header">
      <div class="header-left">
        <div class="brand" @click="router.push('/')">INDIAFISH</div>
      </div>

      <div class="header-center">
        <div class="view-switcher">
          <button
            v-for="mode in ['graph', 'split', 'workbench']"
            :key="mode"
            class="switch-btn"
            :class="{ active: viewMode === mode }"
            @click="viewMode = mode"
          >
            {{ { graph: 'Graph', split: 'Split', workbench: 'Workbench' }[mode] }}
          </button>
        </div>
      </div>

      <div class="header-right">
        <div class="workflow-step">
          <span class="step-num">Step 3/5</span>
          <span class="step-name">Run Simulation</span>
        </div>
        <div class="step-divider"></div>
        <span class="status-indicator" :class="statusClass">
          <span class="dot"></span>
          {{ statusText }}
        </span>
      </div>
    </header>

    <main class="content-area">
      <div class="panel-wrapper left" :style="leftPanelStyle">
        <GraphPanel
          :graphData="graphData"
          :loading="graphLoading"
          :currentPhase="3"
          :isSimulating="isSimulating"
          @refresh="refreshGraph"
          @toggle-maximize="toggleMaximize('graph')"
        />
      </div>

      <div class="panel-wrapper right" :style="rightPanelStyle">
        <Step3Simulation
          :simulationId="currentSimulationId"
          :maxRounds="maxRounds"
          :minutesPerRound="minutesPerRound"
          :projectData="projectData"
          :graphData="graphData"
          :systemLogs="systemLogs"
          @go-back="handleGoBack"
          @next-step="handleNextStep"
          @add-log="addLog"
          @update-status="updateStatus"
        />
      </div>
    </main>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import GraphPanel from '../components/GraphPanel.vue'
import Step3Simulation from '../components/Step3Simulation.vue'
import { getGraphData, getProject } from '../api/graph'
import { closeSimulationEnv, getEnvStatus, getSimulation, getSimulationConfig, stopSimulation } from '../api/simulation'

const route = useRoute()
const router = useRouter()

const viewMode = ref('split')
const currentSimulationId = ref(route.params.simulationId)
const maxRounds = ref(route.query.maxRounds ? parseInt(route.query.maxRounds, 10) : null)
const scenarioId = ref(route.query.scenarioId || '')
const customVariable = ref(route.query.customVariable || '')
const agentCount = ref(route.query.agentCount ? parseInt(route.query.agentCount, 10) : 200)
const minutesPerRound = ref(30)
const projectData = ref(null)
const graphData = ref(null)
const graphLoading = ref(false)
const systemLogs = ref([])
const currentStatus = ref('processing')

const leftPanelStyle = computed(() => {
  if (viewMode.value === 'graph') return { width: '100%', opacity: 1, transform: 'translateX(0)' }
  if (viewMode.value === 'workbench') return { width: '0%', opacity: 0, transform: 'translateX(-20px)' }
  return { width: '50%', opacity: 1, transform: 'translateX(0)' }
})

const rightPanelStyle = computed(() => {
  if (viewMode.value === 'workbench') return { width: '100%', opacity: 1, transform: 'translateX(0)' }
  if (viewMode.value === 'graph') return { width: '0%', opacity: 0, transform: 'translateX(20px)' }
  return { width: '50%', opacity: 1, transform: 'translateX(0)' }
})

const statusClass = computed(() => currentStatus.value)

const statusText = computed(() => {
  if (currentStatus.value === 'error') return 'Error'
  if (currentStatus.value === 'completed') return 'Completed'
  return 'Running'
})

const isSimulating = computed(() => currentStatus.value === 'processing')

const addLog = (msg) => {
  const time = new Date().toLocaleTimeString('en-US', {
    hour12: false,
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  }) + '.' + new Date().getMilliseconds().toString().padStart(3, '0')
  systemLogs.value.push({ time, msg })
  if (systemLogs.value.length > 200) {
    systemLogs.value.shift()
  }
}

const updateStatus = (status) => {
  currentStatus.value = status
}

const toggleMaximize = (target) => {
  if (viewMode.value === target) {
    viewMode.value = 'split'
  } else {
    viewMode.value = target
  }
}

const handleGoBack = async () => {
  addLog('Returning to Step 2. Closing any running simulation...')
  stopGraphRefresh()

  try {
    const envStatusRes = await getEnvStatus({ simulation_id: currentSimulationId.value })
    if (envStatusRes.success && envStatusRes.data?.env_alive) {
      try {
        await closeSimulationEnv({ simulation_id: currentSimulationId.value, timeout: 10 })
      } catch {
        await stopSimulation({ simulation_id: currentSimulationId.value })
      }
    } else if (isSimulating.value) {
      await stopSimulation({ simulation_id: currentSimulationId.value })
    }
  } catch (err) {
    addLog(`Simulation shutdown check failed: ${err.message}`)
  }

  router.push({
    name: 'Simulation',
    params: { simulationId: currentSimulationId.value }
  })
}

const handleNextStep = () => {
  addLog('Entering Step 4: Report Generation')
}

const loadSimulationData = async () => {
  try {
    addLog(`Loading simulation data: ${currentSimulationId.value}`)
    const simRes = await getSimulation(currentSimulationId.value)
    if (!(simRes.success && simRes.data)) return

    try {
      const configRes = await getSimulationConfig(currentSimulationId.value)
      if (configRes.success && configRes.data?.time_config?.minutes_per_round) {
        minutesPerRound.value = configRes.data.time_config.minutes_per_round
      }
    } catch {
      addLog(`Using default round duration: ${minutesPerRound.value} minutes`)
    }

    if (simRes.data.project_id) {
      const projRes = await getProject(simRes.data.project_id)
      if (projRes.success && projRes.data) {
        projectData.value = projRes.data
        addLog(`Project loaded: ${projRes.data.project_id}`)
        if (projRes.data.graph_id) {
          await loadGraph(projRes.data.graph_id)
        }
      }
    }
  } catch (err) {
    addLog(`Load error: ${err.message}`)
  }
}

const loadGraph = async (graphId) => {
  if (!isSimulating.value) {
    graphLoading.value = true
  }
  try {
    const res = await getGraphData(graphId)
    if (res.success) {
      graphData.value = res.data
    }
  } catch (err) {
    addLog(`Graph load failed: ${err.message}`)
  } finally {
    graphLoading.value = false
  }
}

const refreshGraph = () => {
  if (projectData.value?.graph_id) {
    loadGraph(projectData.value.graph_id)
  }
}

let graphRefreshTimer = null

const startGraphRefresh = () => {
  if (graphRefreshTimer) return
  addLog('Starting live graph refresh (30s)')
  graphRefreshTimer = setInterval(refreshGraph, 30000)
}

const stopGraphRefresh = () => {
  if (graphRefreshTimer) {
    clearInterval(graphRefreshTimer)
    graphRefreshTimer = null
    addLog('Stopped live graph refresh')
  }
}

watch(isSimulating, (value) => {
  if (value) {
    startGraphRefresh()
  } else {
    stopGraphRefresh()
  }
}, { immediate: true })

watch(() => route.params.simulationId, (value) => {
  currentSimulationId.value = value
})

onMounted(() => {
  addLog('SimulationRunView initialized')
  if (maxRounds.value) addLog(`Custom max rounds: ${maxRounds.value}`)
  if (scenarioId.value) addLog(`Scenario: ${scenarioId.value}`)
  if (customVariable.value) addLog(`Scenario variable injected`)
  addLog(`Agent count target: ${agentCount.value}`)
  loadSimulationData()
})

onUnmounted(() => {
  stopGraphRefresh()
})
</script>

<style scoped>
.main-view {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #fff;
  overflow: hidden;
  font-family: 'Space Grotesk', system-ui, sans-serif;
}

.app-header {
  height: 60px;
  border-bottom: 1px solid #eaeaea;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  background: #fff;
  position: relative;
}

.header-center {
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
}

.brand {
  font-family: 'JetBrains Mono', monospace;
  font-weight: 800;
  font-size: 18px;
  letter-spacing: 1px;
  cursor: pointer;
}

.view-switcher {
  display: flex;
  background: #f5f5f5;
  padding: 4px;
  border-radius: 6px;
  gap: 4px;
}

.switch-btn {
  border: none;
  background: transparent;
  padding: 6px 16px;
  font-size: 12px;
  font-weight: 600;
  color: #666;
  border-radius: 4px;
  cursor: pointer;
}

.switch-btn.active {
  background: #fff;
  color: #000;
}

.header-right,
.workflow-step,
.status-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
}

.header-right {
  gap: 16px;
}

.step-num {
  font-family: 'JetBrains Mono', monospace;
  font-weight: 700;
  color: #999;
}

.step-name {
  font-weight: 700;
}

.step-divider {
  width: 1px;
  height: 14px;
  background-color: #e0e0e0;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #ccc;
}

.status-indicator.processing .dot { background: #ff5722; animation: pulse 1s infinite; }
.status-indicator.completed .dot { background: #4caf50; }
.status-indicator.error .dot { background: #f44336; }

@keyframes pulse { 50% { opacity: 0.5; } }

.content-area {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.panel-wrapper {
  height: 100%;
  overflow: hidden;
  transition: width 0.4s cubic-bezier(0.25, 0.8, 0.25, 1), opacity 0.3s ease, transform 0.3s ease;
}

.panel-wrapper.left {
  border-right: 1px solid #eaeaea;
}
</style>
