<template>
  <div class="container page-content">
    <div class="row">
      <div class="col-md-6 offset-md-3 bg-white rounded text-center">
        <h3 class="my-4">{{ title }}</h3>
        <p>Введите email, с которым вы регистрировались.</p>

        <form @submit.prevent="changePassword()">
          <div class="form-floating">
            <input type="password" class="form-control" id="floatingPassword" v-model="user.password" required >
            <label for="floatingPassword">Пароль</label>
          </div>
          <div class="form-floating">
            <input type="password" class="form-control" id="floatingPasswordConfirmation" v-model="user.password_confirmation" required >
            <label for="floatingPasswordConfirmation">Подтверждение пароля</label>
          </div>
          <button class="btn btn-primary px-5 mt-3 mb-3" type="submit">Изменить</button>
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
      title: 'Изменение пароля',
      user: {
        password: '',
        password_confirmation: '',
      },
    }
  },
  head() {
    return {
      title: `${this.title}. `
    }
  },
  methods: {
    async changePassword() {
      let data = {
        uid: this.$route.params.uid,
        token: this.$route.params.token,
        new_password1: this.user.password,
        new_password2: this.user.password_confirmation
      };
      await this.$axios
          .post('/api/auth/password/reset/confirm/', data)
          .catch((err) => {
            this.$toast.error(`Во время смены пароля произошла ошибка: ${err}`)
          })
    }
  }
}
</script>

<style scoped>

</style>
