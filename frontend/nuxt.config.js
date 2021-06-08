require('dotenv').config()

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
    '@nuxtjs/dotenv'
  ],

  dotenv: {
    systemvars: true
  },

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

  axios: {
    proxy: true,
    credentials: true,
    retry: {
      retries: 3
    }
  },

  proxy: {
    '/api/': { target: process.env.API_URL, pathRewrite: {'^/api/': ''}, changeOrigin: true }
  },

  auth: {
    redirect: {
      login: '/login',
      logout: '/',
      callback: '/login',
      home: '/'
    },
    strategies: {
      local: {
        scheme: 'refresh',
          token: {
            property: 'access_token',
                maxAge: 1800,
                global: true,
          },
          refreshToken: {
            property: 'refresh_token',
                data: 'refresh_token',
                maxAge: 60 * 60 * 24 * 30
          },
          user: {
            property: 'user',
            // autoFetch: true
          },
          endpoints: {
            login: { url: '/api/auth/login', method: 'post' },
            refresh: { url: '/api/auth/refresh', method: 'post' },
            user: { url: '/api/user', method: 'get' },
            logout: { url: '/api/auth/logout', method: 'post' }

          },
          tokenType: 'Token',
          tokenName: 'Authorization',
          // autoLogout: false
      },
      google: {clientId: process.env.GOOGLE_CLIENT_ID},
      facebook: {
        endpoints: {
          userInfo: 'https://graph.facebook.com/v6.0/me?fields=id,name,picture{url}'
        },
        clientId: process.env.FACEBOOK_CLIENT_ID,
            scope: ['public_profile', 'email']
      },
      vk: {scheme: '~/schemes/vk', },
      yandex: {scheme: '~/schemes/yandex', },
    }
  },

  sentry: {
    dsn: process.env.SENTRY_DSN,
    maxBreadcrumbs: 50,
    debug: true,
  },

  yandexMetrika: {
    id: process.env.YANDEX_METRIKA_ID,
    clickmap: true,
    trackLinks: true,
    accurateTrackBounce: true,
    webvisor: true
  },

  // Build Configuration: https://go.nuxtjs.dev/config-build
  build: {
  },

  env: {
  }
}
