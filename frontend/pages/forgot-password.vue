<template>
  <div class="container page-content">
    <div class="row">
      <div class="col-md-6 offset-md-3 bg-white rounded text-center">
        <h3 class="my-4">{{ title }}</h3>
        <p>Введите email, с которым вы регистрировались.</p>
        <form @submit.prevent="passwordReset()">
          <div class="form-floating">
            <input type="email" class="form-control" id="floatingInput" v-model="user.email" placeholder="name@domain.com" required >
            <label for="floatingInput">Email</label>
          </div>
          <button class="btn btn-primary px-5 mt-3 mb-3" type="submit">Восстановить</button>
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
      title: 'Восстановление пароля',
      user: {
        email: '',
      },
    }
  },
  head() {
    return {
      title: `${this.title}. `
    }
  },
  methods: {
    async passwordReset() {
      let data = {
        email: this.user.email,
      };
      await this.$axios
          .post('/api/auth/password/reset/', data)
          .then(() => this.$router.replace(
              localStorage.getItem('auth.redirect') || this.$auth.redirect('home')))
          .catch((err) => {
            this.$toast.error(`Во время восстановления пароля произошла ошибка: ${err}`)
          })
    }
  }
}
</script>

<style scoped>

</style>
