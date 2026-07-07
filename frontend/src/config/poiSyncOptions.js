/** Preset keywords and POI types for Amap sync job form. */

export const POI_VALUE_DELIMITER = '|'

export const POI_KEYWORD_PRESETS = [
  {
    group: 'Food & Beverage',
    categoryKeyword: '餐饮',
    items: [
      '餐厅',
      '饭店',
      '火锅',
      '烧烤',
      '快餐',
      '奶茶',
      '咖啡',
      '茶饮',
      '甜品',
      '面包',
      '蛋糕',
      '小吃',
      '面馆',
      '川菜',
      '湘菜',
      '粤菜',
      '日料',
      '韩餐',
      '西餐',
      '自助餐',
      '外卖',
      '食堂',
    ],
  },
  {
    group: 'Beauty & Wellness',
    categoryKeyword: '美容',
    items: [
      '美发',
      '美甲',
      'spa',
      '养生',
      '按摩',
      '足浴',
      '洗浴',
      '护肤',
      '纹绣',
      '减肥',
      '产后修复',
    ],
  },
  {
    group: 'Retail & Shopping',
    categoryKeyword: '零售',
    items: [
      '超市',
      '便利店',
      '水果店',
      '生鲜',
      '药店',
      '五金',
      '建材',
      '家居',
      '家具',
      '家电',
      '服装',
      '鞋店',
      '母婴',
      '文具',
      '花店',
      '宠物店',
    ],
  },
  {
    group: 'Education & Training',
    categoryKeyword: '培训',
    items: [
      '教育',
      '幼儿园',
      '托管',
      '早教',
      '艺术培训',
      '英语培训',
      '舞蹈',
      '书法',
      '驾校',
      '留学',
    ],
  },
  {
    group: 'Healthcare',
    categoryKeyword: '医疗',
    items: [
      '诊所',
      '口腔',
      '牙科',
      '眼科',
      '中医',
      '康复',
      '体检',
      '医美',
      '药店',
      '母婴护理',
    ],
  },
  {
    group: 'Fitness & Leisure',
    categoryKeyword: '休闲',
    items: [
      '健身',
      '瑜伽',
      '游泳',
      '球馆',
      '台球',
      'KTV',
      '酒吧',
      '网咖',
      '影院',
      '酒店',
      '民宿',
      '宾馆',
    ],
  },
  {
    group: 'Auto & Services',
    categoryKeyword: '生活服务',
    items: [
      '汽修',
      '洗车',
      '汽车美容',
      '4S店',
      '轮胎',
      '加油站',
      '家政',
      '保洁',
      '搬家',
      '维修',
      '图文',
      '打印',
      '摄影',
      '婚庆',
      '律所',
      '会计',
    ],
  },
  {
    group: 'Real Estate & Office',
    categoryKeyword: '房产',
    items: [
      '中介',
      '物业',
      '写字楼',
      '园区',
      '工厂',
      '仓库',
      '物流',
    ],
  },
]

/** Amap POI type codes grouped for cascading multi-select. Empty selection = no filter. */
export const POI_TYPE_GROUPS = [
  {
    group: 'Food & Beverage',
    categoryValue: '050000',
    items: [
      { label: 'Restaurant (detail)', value: '050100' },
      { label: 'Fast Food', value: '050300' },
      { label: 'Coffee & Tea', value: '050700' },
    ],
  },
  {
    group: 'Shopping',
    categoryValue: '060000',
    items: [
      { label: 'Convenience Store', value: '060200' },
      { label: 'Supermarket', value: '060400' },
    ],
  },
  {
    group: 'Life Services',
    categoryValue: '070000',
    items: [
      { label: 'Beauty Salon', value: '071100' },
      { label: 'Hair Salon', value: '071200' },
    ],
  },
  {
    group: 'Sports & Leisure',
    categoryValue: '080000',
    items: [{ label: 'Fitness Center', value: '080111' }],
  },
  {
    group: 'Healthcare',
    categoryValue: '090000',
    items: [
      { label: 'Clinic', value: '090300' },
      { label: 'Pharmacy', value: '090601' },
    ],
  },
  {
    group: 'Accommodation',
    categoryValue: '100000',
    items: [{ label: 'Hotel', value: '100100' }],
  },
  {
    group: 'Scenic Spots',
    categoryValue: '110000',
    items: [],
  },
  {
    group: 'Business & Residential',
    categoryValue: '120000',
    items: [],
  },
  {
    group: 'Government',
    categoryValue: '130000',
    items: [],
  },
  {
    group: 'Education & Culture',
    categoryValue: '140000',
    items: [
      { label: 'Training School', value: '141200' },
      { label: 'Kindergarten', value: '141204' },
    ],
  },
  {
    group: 'Transportation',
    categoryValue: '150000',
    items: [],
  },
  {
    group: 'Finance & Insurance',
    categoryValue: '160000',
    items: [],
  },
  {
    group: 'Companies',
    categoryValue: '170000',
    items: [],
  },
  {
    group: 'Auto Services',
    categoryValue: '030000',
    items: [],
  },
  {
    group: 'Public Facilities',
    categoryValue: '200000',
    items: [],
  },
]

/** @deprecated Use POI_TYPE_GROUPS */
export const POI_TYPE_PRESETS = POI_TYPE_GROUPS.flatMap((group) => [
  { label: group.group, value: group.categoryValue },
  ...group.items,
])

export function flattenKeywordPresets() {
  return POI_KEYWORD_PRESETS.flatMap((group) => [
    group.categoryKeyword,
    ...group.items,
  ]).filter(Boolean)
}

export function buildKeywordPickerGroups() {
  return POI_KEYWORD_PRESETS.map((group) => ({
    group: group.group,
    categoryValue: group.categoryKeyword,
    items: group.items.map((item) => ({ label: item, value: item })),
  }))
}

export function buildPoiTypePickerGroups() {
  return POI_TYPE_GROUPS
}
