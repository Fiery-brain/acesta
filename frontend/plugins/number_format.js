import Vue from 'vue'

// Vue filter for converting of a number
// into a string according to a locale
Vue.filter('numToLocaleString', val => {
    return val.toLocaleString(process.env.LOCALE)
  }
)
