<template>
  <div class="modal fade" id="editPasswordModal" tabindex="-1" aria-labelledby="editPasswordLabel" aria-hidden="true">
    <div class="modal-dialog">
      <div class="modal-content">
        <div class="block-title">
          <p class="sub-title">Изменить пароль</p>
        </div>
        <form @submit.prevent="changePassword()">
          <div class="mb-3">
            <label for="inputCurrentPassword" class="form-label d-none"></label>
            <input type="password" required class="form-control" name="current_password" id="inputCurrentPassword" v-model="password.current_password" placeholder="Текущий пароль *" title="Текущий пароль">
          </div>
          <div class="mb-3">
            <label for="inputNewPassword" class="form-label d-none"></label>
            <input type="password" required class="form-control" name="new_password" id="inputNewPassword" v-model="password.new_password1" placeholder="Новый пароль *" title="Новый пароль">
          </div>
          <div class="mb-3">
            <label for="inputConfirmPassword" class="form-label d-none"></label>
            <input type="password" required class="form-control" name="confirm_password" id="inputConfirmPassword" v-model="password.new_password2"  placeholder="Подтверждение пароля *" title="Подтверждение пароля">
          </div>
          <button type="submit" class="btn btn-primary">Изменить</button>
          <button type="reset" class="btn btn-secondary">Отменить</button>
        </form>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: "UserPasswordChange",
  data() {
    return {
      password: {
        current_password: '',
        new_password1: '',
        new_password2: '',
      },
    }
  },
  methods: {
    async changePassword() {
      let data = {
        old_password: this.password.current_password,
        new_password1: this.password.new_password1,
        new_password2: this.password.new_password2,
      };
      await this.$axios
        .$post("/api/auth/password/change/", data)
        .then(() => this.password.current_password = this.password.new_password1 = this.password.new_password2 = '')
        .then(() => this.$toast.success('Пароль успешно изменен'))
        .catch((err) => {
          this.$toast.error(`Во время изменения пароля произошла ошибка: ${err}`)
        })
    }
  }
}
</script>

<style scoped>

</style>
