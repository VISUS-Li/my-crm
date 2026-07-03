/** Shared filter/condition operator options with translated labels. */

export const typeCheck = ['Check']
export const typeLink = ['Link', 'Dynamic Link']
export const typeNumber = ['Float', 'Int', 'Currency', 'Percent']
export const typeSelect = ['Select']
export const typeString = ['Data', 'Long Text', 'Small Text', 'Text Editor', 'Text']
export const typeDate = ['Date', 'Datetime']
export const typeDuration = ['Duration']
export const typeRating = ['Rating']

function t(message) {
  if (typeof window !== 'undefined' && typeof window.__ === 'function') {
    return window.__(message)
  }
  return message
}

function op(label, value) {
  return { label: t(label), value }
}

const STRING_OPS = [
  ['Equals', 'equals'],
  ['Not equals', 'not equals'],
  ['Like', 'like'],
  ['Not like', 'not like'],
  ['In', 'in'],
  ['Not in', 'not in'],
  ['Is', 'is'],
]

const STRING_OPS_CONDITION = [
  ['Equals', '=='],
  ['Not equals', '!='],
  ['Like', 'like'],
  ['Not like', 'not like'],
  ['In', 'in'],
  ['Not in', 'not in'],
  ['Is', 'is'],
]

const ASSIGN_OPS = [
  ['Like', 'like'],
  ['Not like', 'not like'],
  ['Is', 'is'],
]

const NUMBER_OPS_EXTRA = [
  ['<', '<'],
  ['>', '>'],
  ['<=', '<='],
  ['>=', '>='],
]

const SELECT_OPS = [
  ['Equals', 'equals'],
  ['Not equals', 'not equals'],
  ['In', 'in'],
  ['Not in', 'not in'],
  ['Is', 'is'],
]

const SELECT_OPS_CONDITION = [
  ['Equals', '=='],
  ['Not equals', '!='],
  ['In', 'in'],
  ['Not in', 'not in'],
  ['Is', 'is'],
]

const DATE_OPS = [
  ['Equals', 'equals'],
  ['Not equals', 'not equals'],
  ['Is', 'is'],
  ['>', '>'],
  ['<', '<'],
  ['>=', '>='],
  ['<=', '<='],
  ['Between', 'between'],
  ['Timespan', 'timespan'],
]

const DATE_OPS_CONDITION = [
  ['Equals', '=='],
  ['Not equals', '!='],
  ['Is', 'is'],
  ['>', '>'],
  ['<', '<'],
  ['>=', '>='],
  ['<=', '<='],
  ['Between', 'between'],
]

const RATING_OPS = [
  ['Equals', 'equals'],
  ['Not equals', 'not equals'],
  ['Greater than', '>'],
  ['Less than', '<'],
  ['Greater than or equal to', '>='],
  ['Less than or equal to', '<='],
  ['Is', 'is'],
]

const RATING_OPS_CONDITION = [
  ['Equals', '=='],
  ['Not equals', '!='],
  ['Is', 'is'],
  ['>', '>'],
  ['<', '<'],
  ['>=', '>='],
  ['<=', '<='],
]

function buildOps(pairs) {
  return pairs.map(([label, value]) => op(label, value))
}

function buildOperators(fieldtype, fieldname, pairsByType) {
  let options = []
  const { string, number, select, link, check, duration, date, rating, assign } =
    pairsByType

  if (typeString.includes(fieldtype)) {
    options.push(...buildOps(string))
  }
  if (fieldname === '_assign') {
    return buildOps(assign)
  }
  if (typeNumber.includes(fieldtype)) {
    options.push(...buildOps(number))
  }
  if (typeSelect.includes(fieldtype)) {
    options.push(...buildOps(select))
  }
  if (typeLink.includes(fieldtype)) {
    options.push(...buildOps(link))
  }
  if (typeCheck.includes(fieldtype)) {
    options.push(...buildOps(check))
  }
  if (typeDuration.includes(fieldtype)) {
    options.push(...buildOps(duration))
  }
  if (typeDate.includes(fieldtype)) {
    options.push(...buildOps(date))
  }
  if (typeRating.includes(fieldtype)) {
    options.push(...buildOps(rating))
  }
  return options
}

/** Operators for list Filter.vue (word values: equals, not equals, …). */
export function getFilterOperators(fieldtype, fieldname) {
  return buildOperators(fieldtype, fieldname, {
    string: STRING_OPS,
    number: [...STRING_OPS, ...NUMBER_OPS_EXTRA],
    select: SELECT_OPS,
    link: STRING_OPS,
    check: [['Equals', 'equals']],
    duration: [
      ['Like', 'like'],
      ['Not like', 'not like'],
      ['In', 'in'],
      ['Not in', 'not in'],
      ['Is', 'is'],
    ],
    date: DATE_OPS,
    rating: RATING_OPS,
    assign: ASSIGN_OPS,
  })
}

/** Operators for ConditionsFilter (symbol values: ==, !=, …). */
export function getConditionOperators(fieldtype, fieldname) {
  return buildOperators(fieldtype, fieldname, {
    string: STRING_OPS_CONDITION,
    number: [...STRING_OPS_CONDITION, ...NUMBER_OPS_EXTRA],
    select: SELECT_OPS_CONDITION,
    link: STRING_OPS_CONDITION,
    check: [['Equals', '==']],
    duration: [
      ['Like', 'like'],
      ['Not like', 'not like'],
      ['In', 'in'],
      ['Not in', 'not in'],
      ['Is', 'is'],
    ],
    date: DATE_OPS_CONDITION,
    rating: RATING_OPS_CONDITION,
    assign: ASSIGN_OPS,
  })
}
