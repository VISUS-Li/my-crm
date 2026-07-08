<template>
  <div class="col-span-2 grid grid-cols-3 gap-4">
    <FormControl
      type="select"
      :label="__('Province')"
      :modelValue="province"
      :options="provinceOptions"
      :placeholder="__('Select province')"
      @update:modelValue="onProvinceChange"
    />
    <FormControl
      type="select"
      :label="__('City')"
      :modelValue="city"
      :options="cityOptions"
      :placeholder="__('Select city')"
      :disabled="!provinceAdcode"
      @update:modelValue="onCityChange"
    />
    <FormControl
      type="select"
      :label="__('District')"
      :modelValue="district"
      :options="districtOptions"
      :placeholder="__('Select district (optional)')"
      :disabled="!cityAdcode"
      @update:modelValue="onDistrictChange"
    />
  </div>
</template>

<script setup>
import { call, toast } from 'frappe-ui'
import { computed, onMounted, ref, watch } from 'vue'

const props = defineProps({
  province: { type: String, default: '' },
  city: { type: String, default: '' },
  district: { type: String, default: '' },
  adcode: { type: String, default: '' },
})

const emit = defineEmits(['update:province', 'update:city', 'update:district', 'update:adcode'])

const provinces = ref([])
const cities = ref([])
const districts = ref([])
const provinceAdcode = ref('')
const cityAdcode = ref('')
const districtAdcode = ref('')

const provinceOptions = computed(() =>
  provinces.value.map((item) => ({ label: item.name, value: item.name })),
)
const cityOptions = computed(() =>
  cities.value.map((item) => ({ label: item.name, value: item.name })),
)
const districtOptions = computed(() => [
  { label: __('All districts'), value: '' },
  ...districts.value.map((item) => ({ label: item.name, value: item.name })),
])

async function loadDistricts({ keywords = '', adcode = '' } = {}) {
  try {
    return await call('crm.amap.api.get_districts', {
      keywords,
      adcode,
      subdistrict: 1,
    })
  } catch (error) {
    const message =
      error.messages?.[0] ||
      error.message ||
      __('Unable to load region data. Check Amap settings or contact your administrator.')
    toast.error(message)
    return []
  }
}

async function loadProvinces() {
  provinces.value = (await loadDistricts()) || []
}

async function loadCities(adcode) {
  cities.value = adcode ? (await loadDistricts({ adcode })) || [] : []
}

async function loadDistrictList(adcode) {
  districts.value = adcode ? (await loadDistricts({ adcode })) || [] : []
}

function findAdcode(list, name) {
  return list.find((item) => item.name === name)?.adcode || ''
}

async function onProvinceChange(name) {
  provinceAdcode.value = findAdcode(provinces.value, name)
  cityAdcode.value = ''
  districtAdcode.value = ''
  emit('update:province', name)
  emit('update:city', '')
  emit('update:district', '')
  emit('update:adcode', provinceAdcode.value)
  await loadCities(provinceAdcode.value)
  districts.value = []
}

async function onCityChange(name) {
  cityAdcode.value = findAdcode(cities.value, name)
  districtAdcode.value = ''
  emit('update:city', name)
  emit('update:district', '')
  emit('update:adcode', cityAdcode.value)
  await loadDistrictList(cityAdcode.value)
}

function onDistrictChange(name) {
  districtAdcode.value = name ? findAdcode(districts.value, name) : ''
  emit('update:district', name)
  emit('update:adcode', districtAdcode.value || cityAdcode.value)
}

async function hydrateFromProps() {
  if (!props.province) return

  provinceAdcode.value = findAdcode(provinces.value, props.province)
  if (provinceAdcode.value) {
    await loadCities(provinceAdcode.value)
  }

  if (props.city) {
    cityAdcode.value = findAdcode(cities.value, props.city)
    if (cityAdcode.value) {
      await loadDistrictList(cityAdcode.value)
    }
  }

  if (props.district) {
    districtAdcode.value = findAdcode(districts.value, props.district)
  } else if (props.adcode) {
    districtAdcode.value = props.adcode
  }
}

onMounted(async () => {
  await loadProvinces()
  await hydrateFromProps()
})

watch(
  () => [props.province, props.city, props.district],
  () => {
    hydrateFromProps()
  },
)
</script>
