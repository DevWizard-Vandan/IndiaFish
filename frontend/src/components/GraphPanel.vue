<template>
  <div class="graph-panel">
    <div class="panel-header">
      <span class="panel-title">Graph Relationship Visualization</span>
      <div class="header-tools">
        <button class="tool-btn" @click="$emit('refresh')" :disabled="loading" title="Refresh graph">
          <span class="icon-refresh" :class="{ spinning: loading }">↻</span>
          <span class="btn-text">Refresh</span>
        </button>
        <button class="tool-btn" @click="$emit('toggle-maximize')" title="Maximize or restore">
          <span class="icon-maximize">⛶</span>
        </button>
      </div>
    </div>

    <div class="graph-container">
      <div v-if="graphData" class="graph-view">
        <div class="graph-stage-banner" v-if="currentPhase === 1 || isSimulating">
          {{ isSimulating ? 'GraphRAG long and short-term memory updating live' : 'Knowledge graph updating live...' }}
        </div>

        <div class="graph-summary">
          <div class="summary-card">
            <span class="summary-label">Nodes</span>
            <strong class="summary-value">{{ nodeCount }}</strong>
          </div>
          <div class="summary-card">
            <span class="summary-label">Edges</span>
            <strong class="summary-value">{{ edgeCount }}</strong>
          </div>
          <div class="summary-card">
            <span class="summary-label">Entity Types</span>
            <strong class="summary-value">{{ entityTypes.length }}</strong>
          </div>
        </div>

        <div class="graph-preview">
          <svg viewBox="0 0 600 280" class="graph-svg">
            <line
              v-for="(edge, index) in previewEdges"
              :key="`edge-${index}`"
              :x1="edge.x1"
              :y1="edge.y1"
              :x2="edge.x2"
              :y2="edge.y2"
              stroke="#d1d5db"
              stroke-width="2"
            />
            <g v-for="(node, index) in previewNodes" :key="`node-${index}`">
              <circle :cx="node.x" :cy="node.y" r="18" :fill="node.color" />
              <text :x="node.x" :y="node.y + 34" text-anchor="middle" class="node-label">
                {{ node.label }}
              </text>
            </g>
          </svg>
        </div>

        <div v-if="entityTypes.length" class="graph-legend">
          <span class="legend-title">Entity Types</span>
          <div class="legend-items">
            <div class="legend-item" v-for="type in entityTypes" :key="type.name">
              <span class="legend-dot" :style="{ background: type.color }"></span>
              <span class="legend-label">{{ type.name }}</span>
            </div>
          </div>
        </div>
      </div>

      <div v-else-if="loading" class="graph-state">
        <div class="loading-spinner"></div>
        <p>Loading graph data...</p>
      </div>

      <div v-else class="graph-state">
        <div class="empty-icon">✦</div>
        <p class="empty-text">Waiting for market intelligence extraction...</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  graphData: Object,
  loading: Boolean,
  currentPhase: Number,
  isSimulating: Boolean
})

defineEmits(['refresh', 'toggle-maximize'])

const fallbackPalette = ['#0f172a', '#ff4500', '#0ea5e9', '#16a34a', '#9333ea', '#f59e0b']

const entityTypes = computed(() => {
  const fromSchema = props.graphData?.entity_types || props.graphData?.legend || []
  if (Array.isArray(fromSchema) && fromSchema.length) {
    return fromSchema.map((item, index) => ({
      name: item.name || item.label || `Type ${index + 1}`,
      color: item.color || fallbackPalette[index % fallbackPalette.length]
    }))
  }

  const nodes = props.graphData?.nodes || []
  const unique = [...new Set(nodes.map((node) => node.type || node.entity_type).filter(Boolean))]
  return unique.map((name, index) => ({
    name,
    color: fallbackPalette[index % fallbackPalette.length]
  }))
})

const nodeCount = computed(() => props.graphData?.node_count || props.graphData?.nodes?.length || 0)
const edgeCount = computed(() => props.graphData?.edge_count || props.graphData?.edges?.length || 0)

const previewNodes = computed(() => {
  const rawNodes = (props.graphData?.nodes || []).slice(0, 6)
  const radius = 90
  const centerX = 300
  const centerY = 120

  if (!rawNodes.length) {
    return entityTypes.value.slice(0, 4).map((type, index) => ({
      label: type.name,
      color: type.color,
      x: 120 + index * 120,
      y: 110 + (index % 2) * 40
    }))
  }

  return rawNodes.map((node, index) => {
    const angle = (Math.PI * 2 * index) / rawNodes.length
    const typeName = node.type || node.entity_type
    const matched = entityTypes.value.find((item) => item.name === typeName)
    return {
      label: (node.name || node.label || `Node ${index + 1}`).slice(0, 12),
      color: matched?.color || fallbackPalette[index % fallbackPalette.length],
      x: centerX + Math.cos(angle) * radius,
      y: centerY + Math.sin(angle) * radius
    }
  })
})

const previewEdges = computed(() => {
  if (previewNodes.value.length < 2) return []
  return previewNodes.value.map((node, index) => {
    const next = previewNodes.value[(index + 1) % previewNodes.value.length]
    return {
      x1: node.x,
      y1: node.y,
      x2: next.x,
      y2: next.y
    }
  })
})
</script>

<style scoped>
.graph-panel {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #fff;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #e5e7eb;
}

.panel-title {
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.header-tools {
  display: flex;
  gap: 10px;
}

.tool-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  border: 1px solid #e5e7eb;
  background: #fff;
  padding: 8px 10px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 12px;
}

.tool-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.icon-refresh.spinning {
  animation: spin 1s linear infinite;
}

.graph-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 20px;
  overflow: auto;
}

.graph-view {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.graph-stage-banner {
  padding: 10px 14px;
  border-radius: 10px;
  background: #fff7ed;
  color: #c2410c;
  font-size: 12px;
  font-weight: 600;
}

.graph-summary {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.summary-card {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 14px;
}

.summary-label {
  display: block;
  font-size: 11px;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  margin-bottom: 6px;
}

.summary-value {
  font-family: 'JetBrains Mono', monospace;
  font-size: 24px;
}

.graph-preview {
  border: 1px solid #e5e7eb;
  border-radius: 16px;
  background: radial-gradient(circle at top, #f8fafc, #ffffff 70%);
  padding: 20px;
}

.graph-svg {
  width: 100%;
  height: 280px;
}

.node-label {
  font-size: 11px;
  fill: #0f172a;
  font-weight: 600;
}

.graph-legend {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.legend-title {
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: #64748b;
}

.legend-items {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.legend-item {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  background: #f8fafc;
  border-radius: 999px;
  font-size: 12px;
}

.legend-dot {
  width: 10px;
  height: 10px;
  border-radius: 999px;
}

.graph-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  color: #64748b;
}

.loading-spinner {
  width: 34px;
  height: 34px;
  border-radius: 999px;
  border: 3px solid #e2e8f0;
  border-top-color: #ff4500;
  animation: spin 1s linear infinite;
}

.empty-icon {
  font-size: 30px;
  color: #ff4500;
}

.empty-text {
  font-size: 14px;
  font-weight: 500;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@media (max-width: 960px) {
  .graph-summary {
    grid-template-columns: 1fr;
  }
}
</style>
