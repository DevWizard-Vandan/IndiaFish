<template>
  <div class="workbench-panel">
    <div class="scroll-container">
      <div class="step-card" :class="{ active: currentPhase === 0, completed: currentPhase > 0 }">
        <div class="card-header">
          <div class="step-info">
            <span class="step-num">01</span>
            <span class="step-title">Market Intelligence Extraction</span>
          </div>
          <div class="step-status">
            <span v-if="currentPhase > 0" class="badge success">Completed</span>
            <span v-else-if="currentPhase === 0" class="badge processing">Running</span>
            <span v-else class="badge pending">Pending</span>
          </div>
        </div>

        <div class="card-content">
          <p class="api-note">POST /api/graph/ontology/generate</p>
          <p class="description">
            LLM analyses the seed document and extracts market entities — stocks, sectors, key levels, participants, and events.
          </p>

          <div v-if="currentPhase === 0 && ontologyProgress" class="progress-section">
            <div class="spinner-sm"></div>
            <span>{{ ontologyProgress.message || 'Analysing the seed...' }}</span>
          </div>

          <div v-if="projectData?.ontology?.entity_types" class="tags-container">
            <span class="tag-label">GENERATED ENTITY TYPES</span>
            <div class="tags-list">
              <span
                v-for="entity in projectData.ontology.entity_types"
                :key="entity.name"
                class="entity-tag"
              >
                {{ entity.name }}
              </span>
            </div>
          </div>

          <div v-if="projectData?.ontology?.edge_types" class="tags-container">
            <span class="tag-label">GENERATED RELATION TYPES</span>
            <div class="tags-list">
              <span
                v-for="rel in projectData.ontology.edge_types"
                :key="rel.name"
                class="entity-tag"
              >
                {{ rel.name }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <div class="step-card" :class="{ active: currentPhase === 1, completed: currentPhase > 1 }">
        <div class="card-header">
          <div class="step-info">
            <span class="step-num">02</span>
            <span class="step-title">Knowledge Graph Build</span>
          </div>
          <div class="step-status">
            <span v-if="currentPhase > 1" class="badge success">Completed</span>
            <span v-else-if="currentPhase === 1" class="badge processing">{{ buildProgress?.progress || 0 }}%</span>
            <span v-else class="badge pending">Pending</span>
          </div>
        </div>

        <div class="card-content">
          <p class="api-note">POST /api/graph/build</p>
          <p class="description">
            GraphRAG segments the market data and builds a knowledge graph using Zep — extracting entity relationships and temporal memory.
          </p>

          <div class="stats-grid">
            <div class="stat-card">
              <span class="stat-value">{{ graphStats.nodes }}</span>
              <span class="stat-label">Nodes</span>
            </div>
            <div class="stat-card">
              <span class="stat-value">{{ graphStats.edges }}</span>
              <span class="stat-label">Edges</span>
            </div>
            <div class="stat-card">
              <span class="stat-value">{{ graphStats.types }}</span>
              <span class="stat-label">Schema Types</span>
            </div>
          </div>
        </div>
      </div>

      <div class="step-card" :class="{ active: currentPhase === 2, completed: currentPhase >= 2 }">
        <div class="card-header">
          <div class="step-info">
            <span class="step-num">03</span>
            <span class="step-title">Build Complete</span>
          </div>
          <div class="step-status">
            <span v-if="currentPhase >= 2" class="badge accent">Ready</span>
          </div>
        </div>

        <div class="card-content">
          <p class="api-note">POST /api/simulation/create</p>
          <p class="description">Map construction complete. Proceeding to agent population setup.</p>
          <button
            class="action-btn"
            :disabled="currentPhase < 2 || creatingSimulation"
            @click="handleEnterEnvSetup"
          >
            <span v-if="creatingSimulation" class="spinner-sm"></span>
            {{ creatingSimulation ? 'Creating simulation...' : 'Enter Environment Setup ➝' }}
          </button>
        </div>
      </div>
    </div>

    <div class="system-logs">
      <div class="log-header">
        <span class="log-title">SYSTEM DASHBOARD</span>
        <span class="log-id">{{ projectData?.project_id || 'NO_PROJECT' }}</span>
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
import { computed, nextTick, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { createSimulation } from '../api/simulation'

const router = useRouter()

const props = defineProps({
  currentPhase: { type: Number, default: 0 },
  projectData: Object,
  ontologyProgress: Object,
  buildProgress: Object,
  graphData: Object,
  systemLogs: { type: Array, default: () => [] }
})

defineEmits(['next-step'])

const logContent = ref(null)
const creatingSimulation = ref(false)

const handleEnterEnvSetup = async () => {
  if (!props.projectData?.project_id || !props.projectData?.graph_id) {
    console.error('Missing project or graph information')
    return
  }

  creatingSimulation.value = true
  try {
    const res = await createSimulation({
      project_id: props.projectData.project_id,
      graph_id: props.projectData.graph_id,
      enable_twitter: true,
      enable_reddit: true
    })

    if (res.success && res.data?.simulation_id) {
      router.push({
        name: 'Simulation',
        params: { simulationId: res.data.simulation_id }
      })
    } else {
      alert('Failed to create simulation: ' + (res.error || 'Unknown error'))
    }
  } catch (err) {
    alert('Simulation creation error: ' + err.message)
  } finally {
    creatingSimulation.value = false
  }
}

const graphStats = computed(() => {
  const nodes = props.graphData?.node_count || props.graphData?.nodes?.length || 0
  const edges = props.graphData?.edge_count || props.graphData?.edges?.length || 0
  const types = props.projectData?.ontology?.entity_types?.length || 0
  return { nodes, edges, types }
})

watch(() => props.systemLogs.length, () => {
  nextTick(() => {
    if (logContent.value) {
      logContent.value.scrollTop = logContent.value.scrollHeight
    }
  })
})
</script>

<style scoped>
.workbench-panel {
  height: 100%;
  background-color: #fafafa;
  display: flex;
  flex-direction: column;
  overflow: hidden;
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
.log-header,
.log-line,
.progress-section {
  display: flex;
  align-items: center;
}

.card-header {
  justify-content: space-between;
  margin-bottom: 16px;
}

.step-info {
  gap: 12px;
}

.step-num {
  font-family: 'JetBrains Mono', monospace;
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
  letter-spacing: 0.5px;
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
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
  color: #999;
  margin-bottom: 8px;
}

.description {
  font-size: 12px;
  color: #666;
  line-height: 1.5;
  margin-bottom: 16px;
}

.progress-section {
  gap: 10px;
  font-size: 12px;
  color: #ff5722;
  margin-bottom: 12px;
}

.tags-container {
  margin-top: 12px;
}

.tag-label {
  display: block;
  font-size: 10px;
  color: #aaa;
  margin-bottom: 8px;
  font-weight: 600;
}

.tags-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.entity-tag {
  background: #f5f5f5;
  border: 1px solid #eee;
  padding: 4px 10px;
  border-radius: 4px;
  font-size: 11px;
  color: #333;
  font-family: 'JetBrains Mono', monospace;
}

.stats-grid {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 12px;
  background: #f9f9f9;
  padding: 16px;
  border-radius: 6px;
}

.stat-card {
  text-align: center;
}

.stat-value {
  display: block;
  font-size: 20px;
  font-weight: 700;
  color: #000;
  font-family: 'JetBrains Mono', monospace;
}

.stat-label {
  font-size: 9px;
  color: #999;
  text-transform: uppercase;
}

.action-btn {
  width: 100%;
  background: #000;
  color: #fff;
  border: none;
  padding: 14px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
}

.action-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.spinner-sm {
  width: 14px;
  height: 14px;
  border: 2px solid #ffccbc;
  border-top-color: #ff5722;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin { to { transform: rotate(360deg); } }

.system-logs {
  background: #000;
  color: #ddd;
  padding: 16px;
  font-family: 'JetBrains Mono', monospace;
  border-top: 1px solid #222;
  flex-shrink: 0;
}

.log-header {
  justify-content: space-between;
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
</style>
