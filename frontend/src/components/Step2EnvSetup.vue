<template>
  <div class="env-setup-panel">
    <div class="scroll-container">
      <div class="step-card" :class="{ active: phase === 0, completed: phase > 0 }">
        <div class="card-header">
          <div class="step-info">
            <span class="step-num">01</span>
            <span class="step-title">Simulation Instance</span>
          </div>
          <div class="step-status">
            <span v-if="phase > 0" class="badge success">Completed</span>
            <span v-else class="badge processing">Initializing</span>
          </div>
        </div>

        <div class="card-content">
          <p class="api-note">POST /api/simulation/prepare</p>
          <p class="description">Create the simulation environment and start agent/persona generation from the knowledge graph.</p>

          <div v-if="simulationId" class="info-card">
            <div class="info-row">
              <span class="info-label">Project ID</span>
              <span class="info-value mono">{{ projectData?.project_id }}</span>
            </div>
            <div class="info-row">
              <span class="info-label">Graph ID</span>
              <span class="info-value mono">{{ projectData?.graph_id }}</span>
            </div>
            <div class="info-row">
              <span class="info-label">Simulation ID</span>
              <span class="info-value mono">{{ simulationId }}</span>
            </div>
            <div class="info-row">
              <span class="info-label">Task ID</span>
              <span class="info-value mono">{{ taskId || 'ready' }}</span>
            </div>
          </div>
        </div>
      </div>

      <div class="step-card" :class="{ active: phase === 1, completed: phase > 1 }">
        <div class="card-header">
          <div class="step-info">
            <span class="step-num">02</span>
            <span class="step-title">Agent Population Setup</span>
          </div>
          <div class="step-status">
            <span v-if="phase > 1" class="badge success">Completed</span>
            <span v-else-if="phase === 1" class="badge processing">{{ prepareProgress }}%</span>
            <span v-else class="badge pending">Pending</span>
          </div>
        </div>

        <div class="card-content">
          <p class="description">IndiaFish is building personas from graph memory and live market context.</p>

          <div class="stats-grid">
            <div class="stat-card">
              <span class="stat-value">{{ profiles.length }}</span>
              <span class="stat-label">Profiles Ready</span>
            </div>
            <div class="stat-card">
              <span class="stat-value">{{ expectedTotal || '-' }}</span>
              <span class="stat-label">Expected Total</span>
            </div>
            <div class="stat-card">
              <span class="stat-value">{{ currentStage || 'Preparing' }}</span>
              <span class="stat-label">Current Stage</span>
            </div>
          </div>

          <div v-if="profiles.length" class="profiles-list">
            <div
              v-for="(profile, idx) in profiles.slice(0, 6)"
              :key="idx"
              class="profile-card"
            >
              <div class="profile-header">
                <span class="profile-name">{{ profile.username || profile.name || `agent_${idx}` }}</span>
                <span class="profile-profession">{{ profile.profession || profile.entity_type || 'Market participant' }}</span>
              </div>
              <p class="profile-bio">{{ truncateBio(profile.bio || profile.persona || 'Persona ready for simulation.') }}</p>
            </div>
          </div>
        </div>
      </div>

      <div class="step-card" :class="{ active: phase >= 2, completed: phase >= 2 }">
        <div class="card-header">
          <div class="step-info">
            <span class="step-num">03</span>
            <span class="step-title">Scenario Setup</span>
          </div>
          <div class="step-status">
            <span class="badge" :class="phase >= 2 ? 'accent' : 'pending'">
              {{ phase >= 2 ? 'Ready' : 'Waiting' }}
            </span>
          </div>
        </div>

        <div class="card-content">
          <p class="description">Choose the event shock, edit the injected variable, and set the IndiaFish swarm size.</p>

          <div class="scenario-grid">
            <div class="field-block">
              <label class="field-label">Scenario</label>
              <select v-model="selectedScenarioId" class="field-input">
                <option v-for="scenario in scenarios" :key="scenario.id" :value="scenario.id">
                  {{ scenario.name }} ({{ scenario.urgency }})
                </option>
              </select>
              <span v-if="selectedScenario" class="urgency-badge">{{ selectedScenario.urgency }}</span>
            </div>

            <div class="field-block field-block--full">
              <label class="field-label">Custom scenario variable</label>
              <textarea
                v-model="customScenarioVariable"
                rows="4"
                class="field-input field-textarea"
              ></textarea>
            </div>

            <div class="field-block field-block--full">
              <label class="field-label">Agent count</label>
              <div class="slider-row">
                <input v-model.number="agentCount" type="range" min="100" max="500" step="50" class="slider">
                <span class="slider-value mono">{{ agentCount }}</span>
              </div>
            </div>

            <div class="field-block field-block--full" v-if="simulationConfig && autoGeneratedRounds">
              <label class="field-label">Max rounds</label>
              <div class="switch-row">
                <label class="switch-label">
                  <input v-model="useCustomRounds" type="checkbox">
                  Use custom rounds
                </label>
                <span class="mono">Auto: {{ autoGeneratedRounds }}</span>
              </div>
              <div v-if="useCustomRounds" class="slider-row">
                <input v-model.number="customMaxRounds" type="range" min="10" :max="autoGeneratedRounds" step="5" class="slider">
                <span class="slider-value mono">{{ customMaxRounds }}</span>
              </div>
            </div>
          </div>

          <div class="action-row">
            <button class="secondary-btn" @click="$emit('go-back')">← Back to Map Construction</button>
            <button class="primary-btn" :disabled="phase < 2" @click="handleStartSimulation">
              Start Simulation →
            </button>
          </div>
        </div>
      </div>
    </div>

    <div class="system-logs">
      <div class="log-header">
        <span class="log-title">SYSTEM DASHBOARD</span>
        <span class="log-id">{{ simulationId || 'NO_SIMULATION' }}</span>
      </div>
      <div class="log-content" ref="logContent">
        <div class="log-line" v-for="(log, idx) in systemLogs" :key="idx">
          <span class="log-time">{{ log.time }}</span>
          <span class="log-msg">{{ log.msg }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { getScenarioVariableTemplate, listScenarios } from '../api/scenario'
import {
  getPrepareStatus,
  getSimulationConfigRealtime,
  getSimulationProfilesRealtime,
  prepareSimulation
} from '../api/simulation'

const props = defineProps({
  simulationId: String,
  projectData: Object,
  graphData: Object,
  systemLogs: Array
})

const emit = defineEmits(['go-back', 'next-step', 'add-log', 'update-status'])

const phase = ref(0)
const taskId = ref(null)
const prepareProgress = ref(0)
const currentStage = ref('')
const profiles = ref([])
const expectedTotal = ref(null)
const simulationConfig = ref(null)

const scenarios = ref([])
const selectedScenarioId = ref('rbi_rate_cut_50bps')
const customScenarioVariable = ref(getScenarioVariableTemplate('rbi_rate_cut_50bps'))
const agentCount = ref(200)
const useCustomRounds = ref(false)
const customMaxRounds = ref(40)

let pollTimer = null
let profilesTimer = null
let configTimer = null

const logContent = ref(null)

const selectedScenario = computed(() => {
  return scenarios.value.find((item) => item.id === selectedScenarioId.value) || null
})

const autoGeneratedRounds = computed(() => {
  if (!simulationConfig.value?.time_config) return null
  const totalHours = simulationConfig.value.time_config.total_simulation_hours
  const minutesPerRound = simulationConfig.value.time_config.minutes_per_round
  if (!totalHours || !minutesPerRound) return null
  return Math.max(Math.floor((totalHours * 60) / minutesPerRound), 40)
})

watch(selectedScenarioId, (value) => {
  customScenarioVariable.value = getScenarioVariableTemplate(value)
})

watch(() => props.systemLogs?.length, () => {
  nextTick(() => {
    if (logContent.value) {
      logContent.value.scrollTop = logContent.value.scrollHeight
    }
  })
})

const addLog = (msg) => {
  emit('add-log', msg)
}

const truncateBio = (bio) => {
  if (bio.length <= 110) return bio
  return bio.slice(0, 110) + '...'
}

const loadScenarios = async () => {
  try {
    const res = await listScenarios()
    if (res.success && Array.isArray(res.data)) {
      scenarios.value = res.data
      if (!scenarios.value.some((item) => item.id === selectedScenarioId.value)) {
        selectedScenarioId.value = scenarios.value[0]?.id || 'rbi_rate_cut_50bps'
      }
    }
  } catch (err) {
    addLog(`Failed to load scenarios: ${err.message}`)
  }
}

const handleStartSimulation = () => {
  const params = {
    scenarioId: selectedScenarioId.value,
    customVariable: customScenarioVariable.value.trim(),
    agentCount: agentCount.value
  }

  if (useCustomRounds.value) {
    params.maxRounds = customMaxRounds.value
    addLog(`Starting simulation with ${agentCount.value} agents and ${customMaxRounds.value} rounds`)
  } else {
    addLog(`Starting simulation with ${agentCount.value} agents and auto-configured rounds`)
  }

  emit('next-step', params)
}

const startPrepareSimulation = async () => {
  if (!props.simulationId) {
    addLog('Error: missing simulationId')
    emit('update-status', 'error')
    return
  }

  phase.value = 1
  addLog(`Simulation instance ready: ${props.simulationId}`)
  addLog('Preparing environment and personas...')
  emit('update-status', 'processing')

  try {
    const res = await prepareSimulation({
      simulation_id: props.simulationId,
      use_llm_for_profiles: true,
      parallel_profile_count: 5
    })

    if (!(res.success && res.data)) {
      addLog(`Prepare failed: ${res.error || 'Unknown error'}`)
      emit('update-status', 'error')
      return
    }

    taskId.value = res.data.task_id
    if (res.data.expected_entities_count) {
      expectedTotal.value = res.data.expected_entities_count
    }
    addLog('Preparation task started.')
    startPolling()
    startProfilesPolling()
  } catch (err) {
    addLog(`Prepare error: ${err.message}`)
    emit('update-status', 'error')
  }
}

const startPolling = () => {
  pollTimer = setInterval(pollPrepareStatus, 2000)
}

const startProfilesPolling = () => {
  profilesTimer = setInterval(fetchProfilesRealtime, 3000)
}

const startConfigPolling = () => {
  if (!configTimer) {
    configTimer = setInterval(fetchConfigRealtime, 2000)
  }
}

const stopPolling = () => {
  if (pollTimer) clearInterval(pollTimer)
  if (profilesTimer) clearInterval(profilesTimer)
  if (configTimer) clearInterval(configTimer)
  pollTimer = null
  profilesTimer = null
  configTimer = null
}

const pollPrepareStatus = async () => {
  try {
    const res = await getPrepareStatus({
      task_id: taskId.value,
      simulation_id: props.simulationId
    })

    if (!(res.success && res.data)) return

    const data = res.data
    prepareProgress.value = data.progress || 0
    currentStage.value = data.progress_detail?.current_stage_name || data.message || ''

    if (data.status === 'completed' || data.status === 'ready' || data.already_prepared) {
      phase.value = 2
      addLog('Environment preparation complete.')
      startConfigPolling()
    } else if (data.status === 'failed') {
      addLog(`Preparation failed: ${data.error || 'Unknown error'}`)
      emit('update-status', 'error')
      stopPolling()
    }
  } catch (err) {
    console.warn('Prepare polling failed:', err)
  }
}

const fetchProfilesRealtime = async () => {
  try {
    const res = await getSimulationProfilesRealtime(props.simulationId, 'reddit')
    if (res.success && res.data) {
      profiles.value = res.data.profiles || []
      if (res.data.total_expected) {
        expectedTotal.value = res.data.total_expected
      }
    }
  } catch (err) {
    console.warn('Profiles polling failed:', err)
  }
}

const fetchConfigRealtime = async () => {
  try {
    const res = await getSimulationConfigRealtime(props.simulationId)
    if (!(res.success && res.data)) return

    if (res.data.config_generated && res.data.config) {
      simulationConfig.value = res.data.config
      phase.value = 2
      emit('update-status', 'completed')
    }
  } catch (err) {
    console.warn('Config polling failed:', err)
  }
}

onMounted(() => {
  loadScenarios()
  if (props.simulationId) {
    addLog('Step 2 environment setup initialized')
    startPrepareSimulation()
  }
})

onUnmounted(() => {
  stopPolling()
})
</script>

<style scoped>
.env-setup-panel {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #fafafa;
  font-family: 'Space Grotesk', system-ui, sans-serif;
}

.scroll-container {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.step-card {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  border: 1px solid #eaeaea;
}

.step-card.active {
  border-color: #ff5722;
  box-shadow: 0 4px 12px rgba(255, 87, 34, 0.08);
}

.card-header,
.step-info,
.info-row,
.action-row,
.slider-row,
.switch-row,
.log-header,
.log-line,
.profile-header {
  display: flex;
  align-items: center;
}

.card-header,
.info-row,
.switch-row,
.log-header {
  justify-content: space-between;
}

.step-info {
  gap: 12px;
}

.step-num,
.mono,
.api-note {
  font-family: 'JetBrains Mono', monospace;
}

.step-num {
  font-size: 20px;
  font-weight: 700;
  color: #e0e0e0;
}

.step-card.active .step-num,
.step-card.completed .step-num {
  color: #000;
}

.step-title {
  font-weight: 600;
  font-size: 14px;
}

.badge {
  font-size: 10px;
  padding: 4px 8px;
  border-radius: 4px;
  font-weight: 600;
  text-transform: uppercase;
}

.badge.success { background: #e8f5e9; color: #2e7d32; }
.badge.processing { background: #ff5722; color: #fff; }
.badge.accent { background: #ff5722; color: #fff; }
.badge.pending { background: #f5f5f5; color: #999; }

.api-note {
  font-size: 10px;
  color: #999;
  margin-bottom: 8px;
}

.description {
  font-size: 12px;
  color: #666;
  line-height: 1.6;
  margin-bottom: 16px;
}

.info-card,
.profiles-list,
.stats-grid,
.scenario-grid {
  display: grid;
  gap: 12px;
}

.info-card {
  background: #f9fafb;
  padding: 14px;
  border-radius: 8px;
}

.info-label,
.field-label {
  font-size: 11px;
  color: #94a3b8;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.info-value {
  font-size: 12px;
  font-weight: 600;
  color: #1e293b;
}

.stats-grid {
  grid-template-columns: repeat(3, 1fr);
}

.stat-card {
  background: #f9f9f9;
  padding: 12px;
  border-radius: 8px;
  text-align: center;
}

.stat-value {
  display: block;
  font-size: 16px;
  font-weight: 700;
  color: #000;
}

.stat-label {
  font-size: 10px;
  color: #64748b;
  text-transform: uppercase;
}

.profiles-list {
  grid-template-columns: repeat(2, 1fr);
}

.profile-card {
  background: #f9f9f9;
  border: 1px solid #e5e5e5;
  border-radius: 8px;
  padding: 14px;
}

.profile-header {
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 8px;
}

.profile-name {
  font-size: 13px;
  font-weight: 700;
}

.profile-profession,
.profile-bio {
  font-size: 12px;
  color: #666;
}

.scenario-grid {
  grid-template-columns: repeat(2, 1fr);
}

.field-block {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.field-block--full {
  grid-column: 1 / -1;
}

.field-input {
  width: 100%;
  border: 1px solid #ddd;
  background: #fafafa;
  padding: 12px 14px;
  border-radius: 6px;
  font-size: 13px;
}

.field-textarea {
  min-height: 110px;
  resize: vertical;
}

.urgency-badge {
  width: fit-content;
  padding: 4px 8px;
  border-radius: 999px;
  background: #fff1f2;
  color: #be123c;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
}

.slider {
  flex: 1;
}

.slider-value {
  min-width: 40px;
  text-align: right;
  font-weight: 700;
}

.switch-label {
  font-size: 12px;
  color: #1e293b;
  display: flex;
  align-items: center;
  gap: 8px;
}

.action-row {
  justify-content: space-between;
  gap: 12px;
  margin-top: 20px;
}

.primary-btn,
.secondary-btn {
  border: none;
  padding: 14px 18px;
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
}

.primary-btn {
  background: #000;
  color: #fff;
}

.primary-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.secondary-btn {
  background: #f5f5f5;
  color: #111827;
}

.system-logs {
  background: #000;
  color: #ddd;
  padding: 16px;
  font-family: 'JetBrains Mono', monospace;
  border-top: 1px solid #222;
  flex-shrink: 0;
}

.log-header {
  border-bottom: 1px solid #333;
  padding-bottom: 8px;
  margin-bottom: 8px;
  font-size: 10px;
  color: #888;
}

.log-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
  height: 80px;
  overflow-y: auto;
}

.log-line {
  gap: 12px;
  font-size: 11px;
}

.log-time {
  color: #666;
  min-width: 75px;
}

.log-msg {
  color: #ccc;
  word-break: break-all;
}

@media (max-width: 1100px) {
  .stats-grid,
  .profiles-list,
  .scenario-grid {
    grid-template-columns: 1fr;
  }
}
</style>
