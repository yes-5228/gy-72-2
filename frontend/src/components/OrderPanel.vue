<template>
  <section class="panel order-panel">
    <div class="panel-title">
      <h2>当前餐盘</h2>
      <span>{{ cart.length }} 类菜品</span>
    </div>

    <div v-if="cart.length === 0" class="empty-state">从菜品列表选择餐品后可提交提前订餐。</div>
    <div v-else class="cart-list">
      <div v-for="item in cart" :key="item.dish.id" :class="['cart-item', { 'cart-item--invalid': dishIssues[item.dish.id] }]">
        <div>
          <div class="cart-item-head">
            <strong>{{ item.dish.name }}</strong>
            <button v-if="dishIssues[item.dish.id]" class="remove-btn" type="button" @click="$emit('remove', item.dish.id)" title="移除">
              ×
            </button>
          </div>
          <small>￥{{ item.dish.price }} / 份</small>
          <p v-if="dishIssues[item.dish.id]" class="issue-text">{{ dishIssues[item.dish.id] }}</p>
        </div>
        <div class="stepper">
          <button type="button" :disabled="dishIssues[item.dish.id]" @click="$emit('decrease', item.dish.id)">-</button>
          <span>{{ item.quantity }}</span>
          <button type="button" :disabled="dishIssues[item.dish.id]" @click="$emit('increase', item.dish)">+</button>
        </div>
      </div>
    </div>

    <form class="order-form" @submit.prevent="submitOrder">
      <label>
        学生姓名
        <input v-model="form.student_name" required placeholder="如：张同学" />
      </label>
      <label>
        学号
        <input v-model="form.student_no" required placeholder="如：S2026008" />
      </label>
      <label>
        联系电话
        <input v-model="form.phone" required placeholder="用于配送联系" />
      </label>
      <label>
        配送地址
        <input v-model="form.delivery_address" required placeholder="教学楼 / 宿舍 / 班级" />
      </label>
      <label>
        预约送达
        <input v-model="form.pickup_time" required type="datetime-local" />
      </label>
      <label>
        备注
        <textarea v-model="form.note" rows="3" placeholder="少辣、不要香菜等"></textarea>
      </label>

      <div class="total-row">
        <span>合计</span>
        <div class="total-col">
          <strong>￥{{ totalAmount }}</strong>
          <small v-if="invalidItems.length > 0" class="excluded-note">
            已排除 {{ invalidItems.length }} 道有问题的菜品
          </small>
        </div>
      </div>
      <button class="primary-button" type="submit" :disabled="!canSubmit">
        {{ submitting ? '提交中...' : invalidItems.length > 0 ? '请先移除有问题的菜品' : '提交订单' }}
      </button>
      <p v-if="message" :class="['form-message', { 'form-message--error': invalidItems.length > 0 }]">{{ message }}</p>
    </form>
  </section>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { createOrder } from '../api/canteen'

const props = defineProps({
  cart: {
    type: Array,
    required: true,
  },
  dishIssues: {
    type: Object,
    default: () => ({}),
  },
})

const emit = defineEmits(['created', 'increase', 'decrease', 'remove'])
const submitting = ref(false)
const message = ref('')

const plusHours = new Date(Date.now() + 2 * 60 * 60 * 1000)
const form = reactive({
  student_name: '',
  student_no: '',
  phone: '',
  delivery_address: '',
  pickup_time: plusHours.toISOString().slice(0, 16),
  note: '',
})

const validItems = computed(() =>
  props.cart.filter((item) => !props.dishIssues[item.dish.id]),
)

const invalidItems = computed(() =>
  props.cart.filter((item) => props.dishIssues[item.dish.id]),
)

const totalAmount = computed(() =>
  validItems.value.reduce((sum, item) => sum + Number(item.dish.price) * item.quantity, 0).toFixed(2),
)

const invalidItemNames = computed(() =>
  invalidItems.value.map((item) => `「${item.dish.name}」`).join('、'),
)

const canSubmit = computed(() =>
  validItems.value.length > 0 && invalidItems.value.length === 0 && !submitting.value,
)

async function submitOrder() {
  if (invalidItems.value.length > 0) {
    message.value = `请先移除有问题的菜品：${invalidItemNames.value}`
    return
  }
  submitting.value = true
  message.value = ''
  try {
    const payload = {
      ...form,
      pickup_time: new Date(form.pickup_time).toISOString(),
      items: validItems.value.map((item) => ({ dish: item.dish.id, quantity: item.quantity })),
    }
    const order = await createOrder(payload)
    message.value = `订单 #${order.id} 已提交，金额 ￥${order.total_amount}`
    emit('created', order)
  } catch (error) {
    message.value = error.message
  } finally {
    submitting.value = false
  }
}

watch(
  () => invalidItems.value.length,
  (newLen, oldLen) => {
    if (newLen === 0 && oldLen > 0 && message.value.includes('请先移除有问题的菜品')) {
      message.value = ''
    }
  },
)
</script>
