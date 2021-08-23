<template>
  <div class="modal fade" id="editEmailModal" tabindex="-1" aria-labelledby="editEmailLabel" aria-hidden="true">
    <div class="modal-dialog">
      <div class="modal-content">
        <div class="block-title">
          <p class="sub-title">Изменить Email</p>
        </div>
        <form @submit.prevent="changeEmail()">
          <div class="mb-3">
            <label for="inputEmail" class="form-label d-none"></label>
            <input type="email" required class="form-control" name="email" id="inputEmail" v-model="user.email" placeholder="Email *" title="Email">
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
  name: "UserEmailChange",
  data() {
    return {
      user: {
        email: this.$auth.user.email
      },
    }
  },
  methods: {
    async changeEmail() {
      let data = {
        email: this.user.email,
      };
      await this.$axios
        .$patch("/api/auth/user/", data)
        .then(() => this.$toast.success('Email успешно изменен'))
        .catch((err) => {
          this.$toast.error(`Во время изменения Email произошла ошибка: ${err}`)
        })
    }
  }
}
</script>

<style scoped>
</style>
