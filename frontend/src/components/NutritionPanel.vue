<template>
  <section class="panel">
    <div class="panel-title">
      <h2>营养成分分析</h2>
      <button class="ghost-button small" type="button" :disabled="dishIds.length === 0" @click="runAnalysis">
        重新分析
      </button>
    </div>

    <div v-if="error" :class="['nutrition-error', { 'fade-out': errorFading }]" @click="dismissError">
      <span>{{ error }}</span>
      <small>点击关闭</small>
    </div>
    <div v-else-if="!analysis" class="empty-state">餐盘中有菜品后可查看总热量、蛋白质、脂肪、碳水和钠含量。</div>
    <template v-else>
      <div class="macro-grid">
        <div v-for="item in macroItems" :key="item.label">
          <span>{{ item.label }}</span>
          <strong>{{ item.value }}</strong>
        </div>
      </div>
      <ul class="advice-list">
        <li v-for="advice in analysis.advice" :key="advice">{{ advice }}</li>
      </ul>
    </template>
  </section>
</template>

<script setup>
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { analyzeNutrition } from '../api/canteen'

const props = defineProps({
  dishIds: {
    type: Array,
    required: true,
  },
  filters: {
    type: Object,
    default: () => ({}),
  },
})

const analysis = ref(null)
const error = ref('')
const errorFading = ref(false)
let errorTimer = null
let errorFadeTimer = null

function clearErrorTimers() {
  clearTimeout(errorTimer)
  clearTimeout(errorFadeTimer)
}

function showError(msg) {
  clearErrorTimers()
  errorFading.value = false
  error.value = msg
  errorTimer = setTimeout(() => {
    dismissError()
  }, 5000)
}

function dismissError() {
  clearErrorTimers()
  if (!error.value) return
  errorFading.value = true
  errorFadeTimer = setTimeout(() => {
    error.value = ''
    errorFading.value = false
  }, 500)
}

onBeforeUnmount(() => {
  clearErrorTimers()
})

const macroItems = computed(() => {
  if (!analysis.value) return []
  const totals = analysis.value.totals
  return [
    { label: '热量', value: `${totals.calories} kcal` },
    { label: '蛋白质', value: `${totals.protein} g` },
    { label: '脂肪', value: `${totals.fat} g` },
    { label: '碳水', value: `${totals.carbohydrate} g` },
    { label: '钠', value: `${totals.sodium} mg` },
  ]
})

async function runAnalysis() {
  if (props.dishIds.length === 0) {
    analysis.value = null
    clearErrorTimers()
    error.value = ''
    errorFading.value = false
    return
  }
  clearErrorTimers()
  error.value = ''
  errorFading.value = false
  try {
    analysis.value = await analyzeNutrition(props.dishIds, props.filters)
  } catch (err) {
    analysis.value = null
    showError(err.message || '营养分析失败，请检查餐盘中的菜品是否符合当前筛选条件。')
  }
}

watch(
  () => [props.dishIds.join(','), JSON.stringify(props.filters)],
  runAnalysis,
  { immediate: true },
)
</script>
