<template>
  <div class="content-grid">
    <section class="menu-area">
      <div class="toolbar">
        <div class="filter-row">
          <label class="filter-label">供应日期</label>
          <input v-model="filters.available_date" type="date" />
        </div>
        <div class="filter-group">
          <span class="filter-label">餐段</span>
          <button
            v-for="option in mealOptions"
            :key="option.value"
            :class="{ selected: filters.meal_period === option.value }"
            type="button"
            @click="filters.meal_period = option.value"
          >
            {{ option.label }}
          </button>
        </div>
        <div class="filter-group">
          <span class="filter-label">分类</span>
          <select v-model="filters.category">
            <option value="">全部分类</option>
            <option v-for="category in categories" :key="category.id" :value="category.id">
              {{ category.name }}
            </option>
          </select>
        </div>
        <div class="filter-group">
          <span class="filter-label">推荐</span>
          <button
            :class="{ selected: filters.recommended === '1' }"
            type="button"
            @click="filters.recommended = filters.recommended === '1' ? '' : '1'"
          >
            仅推荐
          </button>
        </div>
        <div class="filter-group">
          <span class="filter-label">库存</span>
          <button
            v-for="option in stockOptions"
            :key="option.value"
            :class="{ selected: filters.in_stock === option.value }"
            type="button"
            @click="filters.in_stock = option.value"
          >
            {{ option.label }}
          </button>
        </div>
      </div>

      <div v-if="loading" class="loading">菜品加载中...</div>
      <div v-else class="dish-grid">
        <DishCard v-for="dish in dishes" :key="dish.id" :dish="dish" @add="addToCart" />
      </div>
    </section>

    <aside class="side-stack">
      <OrderPanel
        :cart="cart"
        @created="handleOrderCreated"
        @increase="addToCart"
        @decrease="decreaseCart"
      />
      <NutritionPanel :dish-ids="cartDishIds" :filters="nutritionFilters" />
    </aside>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { fetchCategories, fetchDishes } from '../api/canteen'
import DishCard from '../components/DishCard.vue'
import NutritionPanel from '../components/NutritionPanel.vue'
import OrderPanel from '../components/OrderPanel.vue'

const props = defineProps({
  reloadKey: {
    type: Number,
    default: 0,
  },
})

const categories = ref([])
const dishes = ref([])
const cart = ref([])
const loading = ref(false)
const filters = reactive({
  meal_period: '',
  category: '',
  available_date: new Date().toISOString().slice(0, 10),
  recommended: '',
  in_stock: '',
})

const mealOptions = [
  { value: '', label: '全部' },
  { value: 'breakfast', label: '早餐' },
  { value: 'lunch', label: '午餐' },
  { value: 'dinner', label: '晚餐' },
]

const stockOptions = [
  { value: '', label: '全部' },
  { value: '1', label: '有库存' },
  { value: '0', label: '已售罄' },
]

const cartDishIds = computed(() => cart.value.map((item) => item.dish.id))

const availableDishIds = computed(() => new Set(dishes.value.map((d) => d.id)))

const nutritionFilters = computed(() => ({
  available_date: filters.available_date,
  meal_period: filters.meal_period,
}))

async function loadData() {
  loading.value = true
  try {
    const [categoryData, dishData] = await Promise.all([
      fetchCategories(),
      fetchDishes({
        meal_period: filters.meal_period,
        category: filters.category,
        available_date: filters.available_date,
        recommended: filters.recommended,
        in_stock: filters.in_stock,
      }),
    ])
    categories.value = categoryData
    dishes.value = dishData
    cleanupCart()
  } finally {
    loading.value = false
  }
}

function cleanupCart() {
  cart.value = cart.value.filter((item) => {
    const dish = dishes.value.find((d) => d.id === item.dish.id)
    if (!dish) return false
    if (dish.stock === 0) return false
    item.dish.stock = dish.stock
    if (item.quantity > dish.stock) {
      item.quantity = dish.stock
    }
    return true
  })
}

function addToCart(dish) {
  if (!availableDishIds.value.has(dish.id)) {
    alert(`${dish.name} 不在当前可选范围内，请调整筛选条件。`)
    return
  }
  const liveDish = dishes.value.find((d) => d.id === dish.id)
  if (!liveDish || liveDish.stock === 0) {
    alert(`${dish.name} 已售罄，无法加入餐盘。`)
    return
  }
  const existing = cart.value.find((item) => item.dish.id === dish.id)
  if (existing) {
    if (existing.quantity < liveDish.stock) {
      existing.quantity += 1
    } else {
      alert(`${dish.name} 库存不足。`)
    }
  } else {
    cart.value.push({ dish: { ...liveDish }, quantity: 1 })
  }
}

function decreaseCart(dishId) {
  const existing = cart.value.find((item) => item.dish.id === dishId)
  if (!existing) return
  existing.quantity -= 1
  if (existing.quantity <= 0) {
    cart.value = cart.value.filter((item) => item.dish.id !== dishId)
  }
}

function handleOrderCreated() {
  cart.value = []
  loadData()
}

onMounted(loadData)
watch(
  () => [
    filters.meal_period,
    filters.category,
    filters.available_date,
    filters.recommended,
    filters.in_stock,
    props.reloadKey,
  ],
  loadData,
)
</script>
