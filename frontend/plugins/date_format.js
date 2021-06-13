import Vue from 'vue'

// Vue filter for converting of
// a date in ISO-8601 format
// into a string according to a locale
Vue.filter('fromISOtoLocaleString', val => {
    const d = new Date (Date.parse(val));
    return d.toLocaleString(process.env.LOCALE)
  }
)
