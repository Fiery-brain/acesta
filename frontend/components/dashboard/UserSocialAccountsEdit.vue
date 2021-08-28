<template>
  <div class="modal fade" id="socialAccountsModal" tabindex="-1" aria-labelledby="socialAccountsLabel" aria-hidden="true">
    <div class="modal-dialog">
      <div class="modal-content">
        <div class="block-title">
          <p class="sub-title">Социальные сети</p>
        </div>
        <form>
          <div class="form-check form-switch">
            <input class="form-check-input" name="google" type="checkbox" id="google">
            <label class="form-check-label" for="google">Google</label>
          </div>
          <div class="form-check form-switch mt-3">
            <input class="form-check-input" name="facebook" type="checkbox" id="facebook">
            <label class="form-check-label" for="facebook">Facebook</label>
          </div>
          <div class="form-check form-switch mt-3">
            <input class="form-check-input" name="vk" type="checkbox" id="vk">
            <label class="form-check-label" for="vk">ВКонтакте</label>
          </div>
          <div class="form-check form-switch my-3">
            <input class="form-check-input" name="yandex" type="checkbox" id="yandex">
            <label class="form-check-label" for="yandex">Яндекс</label>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: "UserSocialAccountsEdit"
}
</script>

<style scoped>
.form-check-input:checked {
  background-color: #457450;
  border-color:#202f24;
}
</style>
