export default {
  // Global page headers: https://go.nuxtjs.dev/config-head
  head: {
    title: 'Аналитический сервис для развития внутреннего туризма — аsecta',
    htmlAttrs: {
      lang: 'ru'
    },
    meta: [
      { charset: 'utf-8' },
      { name: 'viewport', content: 'width=device-width, initial-scale=1' },
      { hid: 'description', name: 'description', content: 'Аналитический сервис для развития внутреннего туризма на основе цифрового следа в сети Интернет.' }
    ],
    link: [
      { rel: 'icon', type: 'image/x-icon', href: '/favicon.ico' },
      { rel: 'stylesheet', href: '/css/bootstrap.min.css' }
    ],
    script: [
      { src: '/js/bootstrap.bundle.min.js' }
    ]
  },

  // Global CSS: https://go.nuxtjs.dev/config-css
  css: [
  ],

  // Plugins to run before rendering page: https://go.nuxtjs.dev/config-plugins
  plugins: [
  ],

  // Auto import components: https://go.nuxtjs.dev/config-components
  //components: true,

  // Modules for dev and build (recommended): https://go.nuxtjs.dev/config-modules
  buildModules: [
  ],

  loading: {
    continuous: true,
    color: 'LightGreen',
    failedColor: 'IndianRed'
  },

  // Modules: https://go.nuxtjs.dev/config-modules
  modules: [
    '@nuxtjs/axios',
    '@nuxtjs/auth-next',
    '@nuxtjs/sentry',
    '@nuxtjs/yandex-metrika'
  ],

  // Build Configuration: https://go.nuxtjs.dev/config-build
  build: {
  },

  env: {
    //test: '123'
  }
}