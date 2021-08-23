<template>
  <div class="container page-content">
    <div class="row">
      <div class="col-md-6 offset-md-3 bg-white rounded text-center">
        <h3 class="my-4">{{ title }}</h3>
        <p>Введите ключ подтверждения.</p>
        <form @submit.prevent="verifyEmail()">
          <div class="form-floating">
            <input type="text" class="form-control" id="floatingInput" v-model="key" required >
            <label for="floatingInput">Ключ</label>
          </div>
          <button class="btn btn-primary px-5 mt-3 mb-3" type="submit">Подтвердить</button>
          <nuxt-link to="/login/">Войти</nuxt-link>
        </form>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  layout: 'landing',
  auth: false,
  data() {
    return {
      title: 'Подтверждение email',
        key: this.$route.params.key,
    }
  },
  head() {
    return {
      title: `${this.title}. `
    }
  },
  methods: {
    async verifyEmail() {
      let data = {
        key: this.key,
      };
      await this.$axios
          .post('/api/auth/registration/verify-email/', data)
          .then(() => this.$router.replace(
              localStorage.getItem('auth.redirect') || this.$auth.redirect('home')))
          .catch((err) => {
            this.$toast.error(`Во время подтверждения email произошла ошибка: ${err}`)
          })
    }
  }
}
</script>

<style scoped>

</style>
