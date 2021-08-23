<template>
<div>
  <DashboardHeader
      :title="title"
      path="M9 0C4.038 0 0 4.038 0 9c0 2.338.904 4.464 2.371 6.066a.7.7 0 00.233.256A8.97 8.97 0 009 18c4.962 0 9-4.038 9-9s-4.038-9-9-9zm0 1.4c4.206 0 7.6 3.394 7.6 7.6a7.57 7.57 0 01-1.276 4.219 2.995 2.995 0 00-.543-.928c-.65-.752-1.622-.91-2.492-1.135-.435-.112-.845-.213-1.135-.308-.21-.07-.338-.179-.347-.164.014.025.015.038.039.074-.033-.05-.043-.07-.04-.074-.06-.106-.072-.16-.054-.256.022-.12.133-.366.371-.723.67-1.003 1.077-2.644.81-4.129-.268-1.66-1.645-2.612-2.994-2.607-1.349.004-2.735.94-3.066 2.586a.7.7 0 00-.006.029c-.224 1.444.13 3.097.815 4.121.238.357.349.602.37.723.019.097.007.15-.054.256.004.005-.007.024-.039.074.023-.036.024-.049.039-.074-.01-.015-.137.094-.348.164-.29.095-.7.196-1.134.308-.87.224-1.843.383-2.493 1.135-.207.24-.35.491-.46.74A7.564 7.564 0 011.4 9c0-4.206 3.394-7.6 7.6-7.6zm-.057 2.97c.75-.003 1.443.384 1.612 1.433a.7.7 0 00.002.013c.177.979-.236 2.57-.598 3.112-.278.416-.499.793-.582 1.246-.084.452.036.95.293 1.346.307.473.668.533 1.045.658.377.124.802.225 1.224.334.846.218 1.682.575 1.784.693.473.548.411 1.29.4 1.402A7.565 7.565 0 019 16.6a7.572 7.572 0 01-5.318-2.17 1.67 1.67 0 01.4-1.225c.102-.118.938-.475 1.783-.693.423-.11.848-.21 1.225-.334.377-.125.738-.185 1.045-.658.256-.396.376-.894.293-1.346-.084-.453-.304-.83-.582-1.246-.348-.52-.735-2.139-.59-3.114.214-1.022.943-1.442 1.687-1.445z"
      :region="false"
  />
  <UserPasswordChange />
  <UserSocialAccountsEdit />
  <UserEmailChange />
  <div class="container-fluid  page-content">
    <div class="row">
      <div class="col-md-6">
        <UserSubscriptionEdit />
      </div>
      <div class="col-md-6 ps-md-0">
        <UserDataEdit />
      </div>
    </div>
  </div>
</div>
</template>

<script>
import 'vue-select/dist/vue-select.css';

import DashboardHeader from "../components/dashboard/DashboardHeader";
import UserDataEdit from "../components/dashboard/user/UserDataEdit";
import UserSubscriptionEdit from "../components/dashboard/user/UserSubscriptionEdit";
import UserPasswordChange from "../components/dashboard/user/UserPasswordChange";
import UserSocialAccountsEdit from "../components/dashboard/user/UserSocialAccountsEdit";
import UserEmailChange from "../components/dashboard/user/UserEmailChange";

export default {
  data() {
    return {
      title: 'Страница пользователя', //this.$auth.user.first_name//
    }
  },
  head() {
    return {
      title: `${this.title}. `
    }
  },
  components: {
    // Modals
    UserEmailChange,
    UserPasswordChange,
    UserSocialAccountsEdit,

    DashboardHeader,
    UserDataEdit,
    UserSubscriptionEdit
  }
}
</script>

<style scoped>
</style>
