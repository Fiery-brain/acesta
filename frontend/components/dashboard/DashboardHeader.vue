<template>
  <div class="container-fluid pt-2">
    <div class="row">
      <div class="col-md-6">
        <p class="title">
          <svg xmlns="http://www.w3.org/2000/svg" fill="#2D4733" width="24" viewBox="0 0 18 18" class="me-1">
            <path :d="path" color="#000" />
          </svg> {{ title }}
        </p>
      </div>
      <div class="col-md-6">
        <select
            v-if="region"
            name="region"
            v-on:change="setRegionCode($event.target.value)"
            class="w-100 mt-2 float-md-end region-chooser"
            title="Домашний регион">
          <option
              v-for="region in regions"
              :key="region.code"
              :value="region.code"
              :selected="region.code === $auth.user.last_region"
          >{{ region.title }}</option>
        </select>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: "DashboardHeader",
  computed: {
    regions: function () {
      if (this.$auth.loggedIn) {
        return this.$auth.user.regions
      } else {
        return []
      }
    }
  },
  // data() {
  //   return {
  //     regions: []
  //   }
  // },
  props: {
    title: {
      type: String,
      required: true
    },
    path: {
      type: String,
      required: true
    },
    region: {
      type: Boolean,
      default: true
    },
  },
  methods: {
    setRegionCode(code) {
      this.$axios
        .patch('/api/auth/user/', {'last_region': code})
        .then(() => this.$store.dispatch('main_stats/loadMainStats', true))
        .then(() => this.$nuxt.refresh())
        .catch((err) => {
            this.$toast.error(`Во время сохранения текущего региона произошла ошибка: ${err}`)
        })
    }
  }
}
</script>

<style scoped>
.title{margin-top:.2em;margin-bottom:0;color:#2D4733;font-size:1.3em;font-weight:500}
.title svg, .sub-title svg{position:relative;bottom:3px}
.region-chooser{padding:.25em}
</style>
