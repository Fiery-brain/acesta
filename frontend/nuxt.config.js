require('dotenv').config()

export default {
  // Global page headers: https://go.nuxtjs.dev/config-head
  head: {
    titleTemplate: '%sАналитика для экспертов в сфере туризма — аsecta',
    htmlAttrs: {
      lang: 'ru'
    },
    meta: [
      { charset: 'utf-8' },
      { name: 'viewport', content: 'width=device-width, initial-scale=1' },
      { hid: 'description', name: 'description', content: 'Аналитический для экспертов в сфере туризма на основе цифрового следа в Интернет.' }
    ],
    link: [
      { rel: 'icon', type: 'image/x-icon', href: '/favicon.ico' },
      { rel: 'stylesheet', href: '/css/bootstrap.min.css' },
      // { rel: 'stylesheet', href: 'https://cdnjs.cloudflare.com/ajax/libs/mdb-ui-kit/3.6.0/mdb.min.css' }
    ],
    script: [
      { src: '/js/bootstrap.bundle.min.js' },
      // { src: "https://cdnjs.cloudflare.com/ajax/libs/mdb-ui-kit/3.6.0/mdb.min.js", type: "text/javascript" }
    ]
  },

  // Global CSS: https://go.nuxtjs.dev/config-css
  css: [
  ],

  // Plugins to run before rendering page: https://go.nuxtjs.dev/config-plugins
  plugins: [
    '~plugins/date_format.js',
    '~plugins/number_format.js',
    '~plugins/axios.js',
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

  // Loading config: https://nuxtjs.org/docs/2.x/features/loading
  loading: {
    continuous: true,
    color: 'LightGreen',
    failedColor: 'IndianRed'
  },

  // Modules: https://go.nuxtjs.dev/config-modules
  modules: [
    '@nuxtjs/axios',
    '@nuxtjs/proxy',
    '@nuxtjs/auth-next',
    '@nuxtjs/toast',
    '@nuxtjs/sentry',
    '@nuxtjs/yandex-metrika'
  ],

  // Router config: https://nuxtjs.org/docs/2.x/configuration-glossary/configuration-router
  router: {
    middleware: [
        'auth'
    ],
    linkExactActiveClass: 'menu-item-active'
  },

  // Axios config: https://axios.nuxtjs.org/options
  axios: {
    baseURL: process.env.BASE_URL,
    proxy: true,
    credentials: true,
    retry: {
      retries: 3
    },
    debug: true
  },

  proxy: {
  //   //'http://example.com:8000/api/books/*/**.json',
  //   //`{{ process.env.API_URL }}/api/*`,
    '/api/': { target: process.env.API_URL, pathRewrite: {'^/api/': ''} } //, changeOrigin: true
  },

  auth: {
    redirect: {
      login: '/login/',
      logout: '/',
      callback: '/login/',
      home: '/dashboard/'
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
          property: '',
        },
        endpoints: {
          login: { url: '/api/auth/login/', method: 'post' },
          refresh: { url: '/api/auth/token/refresh/', method: 'post' },
          user: { url: '/api/auth/user/', method: 'get' },
          logout: { url: '/api/auth/logout/', method: 'post' },
        },
        //tokenRequired: true,
        tokenType: 'bearer'
      },
      // cookie: {
      //   cookie: {
      //     // (optional) If set we check this cookie exsistence for loggedIn check
      //     name: 'XSRF-TOKEN',
      //   },
      //   endpoints: {
      //     // (optional) If set, we send a get request to this endpoint before login
      //     csrf: {
      //       url: ''
      //     }
      //   }
      // },
      google: {
        clientId: process.env.GOOGLE_CLIENT_ID,
        scope: ['profile', 'email'],
        codeChallengeMethod: ""
      },
      facebook: {
        endpoints: {
          userInfo: 'https://graph.facebook.com/v6.0/me?fields=id,name,picture{url}'
        },
        clientId: process.env.FACEBOOK_CLIENT_ID,
        scope: ['public_profile', 'email']
      },
      vk: {scheme: '~/schemes/vk', },
      yandex: {
        scheme: 'oauth2',
        endpoints: {
          authorization: process.env.YANDEX_CLIENT_URL,
          token: undefined,
          logout: '/logout'
        },
        token: {
          property: 'access_token',
          type: 'Bearer',
          maxAge: 1800
        },
        refreshToken: {
          property: 'refresh_token',
          maxAge: 60 * 60 * 24 * 30
        },
        responseType: 'token',
        grantType: 'authorization_code',
        accessType: undefined,
        //redirectUri: undefined,
        logoutRedirectUri: '/',
        clientId: process.env.YANDEX_CLIENT_ID,
        scope: ['profile', 'email'],
        state: 'UNIQUE_AND_NON_GUESSABLE',
        codeChallengeMethod: '',
        responseMode: '',
        acrValues: '',
        // autoLogout: false
      },
    }
  },

  toast: {
    position: 'top-right',
    duration: 5000
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
    LOCALE: "ru-RU"
  }
}