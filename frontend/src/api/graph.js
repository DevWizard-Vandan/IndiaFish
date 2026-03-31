import service, { requestWithRetry } from './index'

const logOntologyRequest = (payload) => {
  if (payload instanceof FormData) {
    const body = {}
    payload.forEach((value, key) => {
      body[key] = value instanceof File ? `[File:${value.name}]` : value
    })
    console.info('Ontology API call', {
      method: 'POST',
      url: 'http://localhost:5001/api/graph/ontology/generate',
      body
    })
    return
  }

  console.info('Ontology API call', {
    method: 'POST',
    url: 'http://localhost:5001/api/graph/ontology/generate',
    body: payload
  })
}

/**
 * Generate ontology from either document upload or live market seed input.
 * The backend currently expects multipart/form-data, so live mode is also sent
 * as FormData to match graph.py.
 */
export function generateOntology(payload) {
  logOntologyRequest(payload)

  if (payload instanceof FormData) {
    return requestWithRetry(() =>
      service({
        url: '/api/graph/ontology/generate',
        method: 'post',
        data: payload,
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })
    )
  }

  return requestWithRetry(() =>
    service({
      url: '/api/graph/ontology/generate',
      method: 'post',
      data: payload
    })
  )
}

/**
 * 构建图谱
 * @param {Object} data - 包含project_id, graph_name等
 * @returns {Promise}
 */
export function buildGraph(data) {
  return requestWithRetry(() =>
    service({
      url: '/api/graph/build',
      method: 'post',
      data
    })
  )
}

/**
 * 查询任务状态
 * @param {String} taskId - 任务ID
 * @returns {Promise}
 */
export function getTaskStatus(taskId) {
  return service({
    url: `/api/graph/task/${taskId}`,
    method: 'get'
  })
}

/**
 * 获取图谱数据
 * @param {String} graphId - 图谱ID
 * @returns {Promise}
 */
export function getGraphData(graphId) {
  return service({
    url: `/api/graph/data/${graphId}`,
    method: 'get'
  })
}

/**
 * 获取项目信息
 * @param {String} projectId - 项目ID
 * @returns {Promise}
 */
export function getProject(projectId) {
  return service({
    url: `/api/graph/project/${projectId}`,
    method: 'get'
  })
}
