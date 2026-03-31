<template>
  <div class="home-container">
    <nav class="navbar">
      <div class="nav-brand">INDIAFISH</div>
      <div class="nav-links">
        <a href="https://github.com/666ghj/MiroFish" target="_blank" class="github-link">
          View the project repository <span class="arrow">↗</span>
        </a>
      </div>
    </nav>

    <div class="main-content">
      <section class="hero-section">
        <div class="hero-left">
          <div class="tag-row">
            <span class="orange-tag">Indian F&O Swarm Simulator</span>
            <span class="version-text">/ preview build</span>
          </div>

          <h1 class="main-title">
            Simulate Indian markets<br>
            <span class="gradient-text">from a live seed</span>
          </h1>

          <div class="hero-desc">
            <p>
              <span class="highlight-bold">IndiaFish</span> turns a seed document or live market feed into a market intelligence graph, a swarm of realistic agents, and a forward simulation of how Indian F&O participants may react.
            </p>
            <p class="slogan-text">
              Simulate Indian Markets<span class="blinking-cursor">_</span>
            </p>
          </div>

          <div class="decoration-square"></div>
        </div>

        <div class="hero-right">
          <div class="logo-container">
            <img src="../assets/logo/MiroFish_logo_left.jpeg" alt="IndiaFish Logo" class="hero-logo" />
          </div>

          <button class="scroll-down-btn" @click="scrollToBottom">
            ↓
          </button>
        </div>
      </section>

      <section class="dashboard-section">
        <div class="left-panel">
          <div class="panel-header">
            <span class="status-dot">■</span> System Status
          </div>

          <h2 class="section-title">Ready to Run</h2>
          <p class="section-desc">
            Upload a market seed or switch to live Dhan mode to start the IndiaFish pipeline.
          </p>

          <div class="metrics-row">
            <div class="metric-card">
              <div class="metric-value">Fast</div>
              <div class="metric-label">Document to graph in one workflow</div>
            </div>
            <div class="metric-card">
              <div class="metric-value">Live</div>
              <div class="metric-label">Built for Indian F&O market seeds</div>
            </div>
          </div>

          <div class="steps-container">
            <div class="steps-header">
              <span class="diamond-icon">◇</span> Workflow
            </div>
            <div class="workflow-list">
              <div class="workflow-item">
                <span class="step-num">01</span>
                <div class="step-info">
                  <div class="step-title">Map Construction</div>
                  <div class="step-desc">Market intelligence extraction, memory injection, and GraphRAG build</div>
                </div>
              </div>
              <div class="workflow-item">
                <span class="step-num">02</span>
                <div class="step-info">
                  <div class="step-title">Environment Setup</div>
                  <div class="step-desc">Persona generation, scenario selection, and simulation configuration</div>
                </div>
              </div>
              <div class="workflow-item">
                <span class="step-num">03</span>
                <div class="step-info">
                  <div class="step-title">Run Simulation</div>
                  <div class="step-desc">Launch the swarm and monitor how agents react across the market graph</div>
                </div>
              </div>
              <div class="workflow-item">
                <span class="step-num">04</span>
                <div class="step-info">
                  <div class="step-title">Generate Report</div>
                  <div class="step-desc">Produce structured output, F&O signal panels, and scenario analysis</div>
                </div>
              </div>
              <div class="workflow-item">
                <span class="step-num">05</span>
                <div class="step-info">
                  <div class="step-title">Deep Interaction</div>
                  <div class="step-desc">Interrogate the simulated world, report agent, and graph memory</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="right-panel">
          <div class="console-box">
            <div class="console-section">
              <div class="console-header">
                <span class="console-label">01 / Seed Mode</span>
                <span class="console-meta">Choose how IndiaFish should start</span>
              </div>

              <div class="seed-mode-toggle" role="tablist" aria-label="Seed mode">
                <button
                  class="seed-mode-btn"
                  :class="{ active: seedMode === 'document' }"
                  @click="seedMode = 'document'"
                >
                  Upload Document
                </button>
                <button
                  class="seed-mode-btn"
                  :class="{ active: seedMode === 'dhan_live' }"
                  @click="seedMode = 'dhan_live'"
                >
                  Live Dhan Feed
                </button>
              </div>
            </div>

            <div v-if="seedMode === 'document'" class="console-section">
              <div class="console-header">
                <span class="console-label">02 / Reality Seed</span>
                <span class="console-meta">Supported: PDF, MD, TXT</span>
              </div>

              <div
                class="upload-zone"
                :class="{ 'drag-over': isDragOver, 'has-files': files.length > 0 }"
                @dragover.prevent="handleDragOver"
                @dragleave.prevent="handleDragLeave"
                @drop.prevent="handleDrop"
                @click="triggerFileInput"
              >
                <input
                  ref="fileInput"
                  type="file"
                  multiple
                  accept=".pdf,.md,.txt"
                  @change="handleFileSelect"
                  style="display: none"
                  :disabled="loading"
                />

                <div v-if="files.length === 0" class="upload-placeholder">
                  <div class="upload-icon">↑</div>
                  <div class="upload-title">Drop files here to upload</div>
                  <div class="upload-hint">or click to browse</div>
                </div>

                <div v-else class="file-list">
                  <div v-for="(file, index) in files" :key="index" class="file-item">
                    <span class="file-icon">📄</span>
                    <span class="file-name">{{ file.name }}</span>
                    <button @click.stop="removeFile(index)" class="remove-btn">×</button>
                  </div>
                </div>
              </div>
            </div>

            <div v-else class="console-section">
              <div class="console-header">
                <span class="console-label">02 / Live Feed</span>
                <span class="console-meta">Sends a Dhan live seed request</span>
              </div>

              <div class="live-form">
                <label class="field-label" for="underlying-select">Underlying</label>
                <select id="underlying-select" v-model="selectedUnderlying" class="field-input">
                  <option v-for="option in underlyingOptions" :key="option" :value="option">
                    {{ option }}
                  </option>
                </select>

                <label class="field-label" for="underlying-symbol">Underlying Symbol</label>
                <input
                  id="underlying-symbol"
                  v-model="underlyingSymbol"
                  type="text"
                  class="field-input"
                >

                <button type="button" class="fetch-btn" @click="syncUnderlyingFromInput">
                  Fetch Live Data
                </button>
              </div>
            </div>

            <div class="console-divider">
              <span>INPUT PARAMETERS</span>
            </div>

            <div class="console-section">
              <div class="console-header">
                <span class="console-label">03 / Simulation Prompt</span>
              </div>
              <div class="input-wrapper">
                <textarea
                  v-model="formData.simulationRequirement"
                  class="code-input"
                  placeholder="// Describe the market question you want to simulate"
                  rows="6"
                  :disabled="loading"
                ></textarea>
                <div class="model-badge">Engine: IndiaFish-V1.0</div>
              </div>
            </div>

            <div class="console-section btn-section">
              <button
                class="start-engine-btn"
                @click="startSimulation"
                :disabled="!canSubmit || loading"
              >
                <span v-if="!loading">Launch IndiaFish</span>
                <span v-else>Initializing...</span>
                <span class="btn-arrow">→</span>
              </button>
            </div>
          </div>
        </div>
      </section>

      <HistoryDatabase />
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import HistoryDatabase from '../components/HistoryDatabase.vue'

const router = useRouter()

const formData = ref({
  simulationRequirement: ''
})

const files = ref([])
const loading = ref(false)
const isDragOver = ref(false)
const fileInput = ref(null)

const seedMode = ref('document')
const underlyingOptions = ['NIFTY', 'BANKNIFTY', 'FINNIFTY', 'MIDCPNIFTY']
const selectedUnderlying = ref('NIFTY')
const underlyingSymbol = ref('NIFTY')

watch(selectedUnderlying, (value) => {
  underlyingSymbol.value = value
})

const canSubmit = computed(() => {
  const hasPrompt = formData.value.simulationRequirement.trim() !== ''
  if (!hasPrompt) return false
  if (seedMode.value === 'document') {
    return files.value.length > 0
  }
  return underlyingSymbol.value.trim() !== ''
})

const triggerFileInput = () => {
  if (!loading.value && seedMode.value === 'document') {
    fileInput.value?.click()
  }
}

const addFiles = (newFiles) => {
  const validFiles = newFiles.filter((file) => {
    const ext = file.name.split('.').pop()?.toLowerCase()
    return ['pdf', 'md', 'txt'].includes(ext)
  })
  files.value.push(...validFiles)
}

const handleFileSelect = (event) => {
  addFiles(Array.from(event.target.files || []))
}

const handleDragOver = () => {
  if (!loading.value) {
    isDragOver.value = true
  }
}

const handleDragLeave = () => {
  isDragOver.value = false
}

const handleDrop = (event) => {
  isDragOver.value = false
  if (loading.value) return
  addFiles(Array.from(event.dataTransfer.files || []))
}

const removeFile = (index) => {
  files.value.splice(index, 1)
}

const scrollToBottom = () => {
  window.scrollTo({
    top: document.body.scrollHeight,
    behavior: 'smooth'
  })
}

const syncUnderlyingFromInput = () => {
  const next = underlyingSymbol.value.trim().toUpperCase()
  if (!next) return
  underlyingSymbol.value = next
  if (underlyingOptions.includes(next)) {
    selectedUnderlying.value = next
  }
}

const startSimulation = () => {
  if (!canSubmit.value || loading.value) return

  import('../store/pendingUpload.js').then(({ setPendingUpload }) => {
    setPendingUpload(files.value, formData.value.simulationRequirement, {
      seedMode: seedMode.value,
      underlying: underlyingSymbol.value.trim().toUpperCase()
    })

    router.push({
      name: 'Process',
      params: { projectId: 'new' }
    })
  })
}
</script>

<style scoped>
:root {
  --black: #000000;
  --white: #ffffff;
  --orange: #ff4500;
  --gray-light: #f5f5f5;
  --gray-text: #666666;
  --border: #e5e5e5;
  --font-mono: 'JetBrains Mono', monospace;
  --font-sans: 'Space Grotesk', system-ui, sans-serif;
}

.home-container {
  min-height: 100vh;
  background: var(--white);
  font-family: var(--font-sans);
  color: var(--black);
}

.navbar {
  height: 60px;
  background: var(--black);
  color: var(--white);
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 40px;
}

.nav-brand {
  font-family: var(--font-mono);
  font-weight: 800;
  letter-spacing: 1px;
  font-size: 1.2rem;
}

.github-link {
  color: var(--white);
  text-decoration: none;
  font-family: var(--font-mono);
  font-size: 0.9rem;
  display: flex;
  align-items: center;
  gap: 8px;
}

.main-content {
  max-width: 1400px;
  margin: 0 auto;
  padding: 60px 40px;
}

.hero-section {
  display: flex;
  justify-content: space-between;
  margin-bottom: 80px;
}

.hero-left {
  flex: 1;
  padding-right: 60px;
}

.tag-row {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-bottom: 25px;
  font-family: var(--font-mono);
  font-size: 0.8rem;
}

.orange-tag {
  background: var(--orange);
  color: var(--white);
  padding: 4px 10px;
  font-weight: 700;
}

.version-text {
  color: #999;
}

.main-title {
  font-size: 4.5rem;
  line-height: 1.2;
  font-weight: 500;
  margin: 0 0 40px 0;
  letter-spacing: -2px;
}

.gradient-text {
  background: linear-gradient(90deg, #000000 0%, #444444 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.hero-desc {
  font-size: 1.05rem;
  line-height: 1.8;
  color: var(--gray-text);
  max-width: 640px;
  margin-bottom: 50px;
}

.highlight-bold {
  color: var(--black);
  font-weight: 700;
}

.highlight-orange {
  color: var(--orange);
  font-weight: 700;
  font-family: var(--font-mono);
}

.highlight-code {
  background: rgba(0, 0, 0, 0.05);
  padding: 2px 6px;
  border-radius: 2px;
  font-family: var(--font-mono);
}

.slogan-text {
  font-size: 1.2rem;
  font-weight: 520;
  color: var(--black);
  border-left: 3px solid var(--orange);
  padding-left: 15px;
}

.blinking-cursor {
  color: var(--orange);
  animation: blink 1s step-end infinite;
  font-weight: 700;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

.decoration-square {
  width: 16px;
  height: 16px;
  background: var(--orange);
}

.hero-right {
  flex: 0.8;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  align-items: flex-end;
}

.logo-container {
  width: 100%;
  display: flex;
  justify-content: flex-end;
  padding-right: 40px;
}

.hero-logo {
  max-width: 500px;
  width: 100%;
}

.scroll-down-btn {
  width: 40px;
  height: 40px;
  border: 1px solid var(--border);
  background: transparent;
  cursor: pointer;
  color: var(--orange);
  font-size: 1.2rem;
}

.dashboard-section {
  display: flex;
  gap: 60px;
  border-top: 1px solid var(--border);
  padding-top: 60px;
  align-items: flex-start;
}

.left-panel {
  flex: 0.8;
}

.right-panel {
  flex: 1.2;
}

.panel-header,
.steps-header,
.console-header,
.console-divider span,
.metric-value,
.step-num,
.model-badge,
.console-label {
  font-family: var(--font-mono);
}

.panel-header {
  font-size: 0.8rem;
  color: #999;
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 20px;
}

.status-dot {
  color: var(--orange);
}

.section-title {
  font-size: 2rem;
  font-weight: 520;
  margin: 0 0 15px 0;
}

.section-desc {
  color: var(--gray-text);
  margin-bottom: 25px;
  line-height: 1.6;
}

.metrics-row {
  display: flex;
  gap: 20px;
  margin-bottom: 15px;
}

.metric-card {
  border: 1px solid var(--border);
  padding: 20px 30px;
  min-width: 150px;
}

.metric-value {
  font-size: 1.8rem;
  font-weight: 520;
}

.metric-label {
  font-size: 0.85rem;
  color: #999;
}

.steps-container {
  border: 1px solid var(--border);
  padding: 30px;
}

.steps-header {
  font-size: 0.8rem;
  color: #999;
  margin-bottom: 25px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.workflow-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.workflow-item {
  display: flex;
  align-items: flex-start;
  gap: 20px;
}

.step-title {
  font-weight: 520;
  font-size: 1rem;
  margin-bottom: 4px;
}

.step-desc {
  font-size: 0.85rem;
  color: var(--gray-text);
}

.console-box {
  border: 1px solid #ccc;
  padding: 8px;
}

.console-section {
  padding: 20px;
}

.console-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 15px;
  font-size: 0.75rem;
  color: #666;
}

.console-meta {
  color: #999;
}

.seed-mode-toggle {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
}

.seed-mode-btn,
.fetch-btn {
  border: 1px solid #d7d7d7;
  background: #fff;
  padding: 12px 14px;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.seed-mode-btn.active,
.fetch-btn {
  background: #000;
  border-color: #000;
  color: #fff;
}

.upload-zone {
  border: 1px dashed #ccc;
  height: 200px;
  overflow-y: auto;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s;
  background: #fafafa;
}

.upload-zone.has-files {
  align-items: flex-start;
}

.upload-zone:hover {
  background: #f0f0f0;
}

.upload-placeholder {
  text-align: center;
}

.upload-icon {
  width: 40px;
  height: 40px;
  border: 1px solid #ddd;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 15px;
  color: #999;
}

.upload-title {
  font-weight: 500;
  font-size: 0.9rem;
  margin-bottom: 5px;
}

.upload-hint {
  font-family: var(--font-mono);
  font-size: 0.75rem;
  color: #999;
}

.file-list {
  width: 100%;
  padding: 15px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.file-item {
  display: flex;
  align-items: center;
  background: var(--white);
  padding: 8px 12px;
  border: 1px solid #eee;
  font-family: var(--font-mono);
  font-size: 0.85rem;
}

.file-name {
  flex: 1;
  margin: 0 10px;
}

.remove-btn {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 1.2rem;
  color: #999;
}

.live-form {
  display: grid;
  gap: 12px;
}

.field-label {
  font-size: 0.78rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: #666;
}

.field-input {
  width: 100%;
  padding: 12px 14px;
  border: 1px solid #ddd;
  background: #fafafa;
  font-size: 0.95rem;
}

.console-divider {
  display: flex;
  align-items: center;
  margin: 10px 0;
}

.console-divider::before,
.console-divider::after {
  content: '';
  flex: 1;
  height: 1px;
  background: #eee;
}

.console-divider span {
  padding: 0 15px;
  font-size: 0.7rem;
  color: #bbb;
  letter-spacing: 1px;
}

.input-wrapper {
  position: relative;
  border: 1px solid #ddd;
  background: #fafafa;
}

.code-input {
  width: 100%;
  border: none;
  background: transparent;
  padding: 20px;
  font-family: var(--font-mono);
  font-size: 0.9rem;
  line-height: 1.6;
  resize: vertical;
  outline: none;
  min-height: 150px;
}

.model-badge {
  position: absolute;
  bottom: 10px;
  right: 15px;
  font-size: 0.7rem;
  color: #aaa;
}

.btn-section {
  padding-top: 0;
}

.start-engine-btn {
  width: 100%;
  background: var(--black);
  color: var(--white);
  border: none;
  padding: 20px;
  font-family: var(--font-mono);
  font-weight: 700;
  font-size: 1.1rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  transition: all 0.3s ease;
}

.start-engine-btn:hover:not(:disabled) {
  background: var(--orange);
}

.start-engine-btn:disabled {
  background: #e5e5e5;
  color: #999;
  cursor: not-allowed;
}

@media (max-width: 1024px) {
  .dashboard-section,
  .hero-section {
    flex-direction: column;
  }

  .hero-left {
    padding-right: 0;
    margin-bottom: 40px;
  }

  .hero-logo {
    max-width: 220px;
  }

  .seed-mode-toggle,
  .metrics-row {
    grid-template-columns: 1fr;
    flex-direction: column;
  }
}
</style>
