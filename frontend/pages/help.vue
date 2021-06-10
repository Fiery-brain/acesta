<template>
<div>
  <DashboardHeader
      :title="title"
      path="M9 0C4.038 0 0 4.038 0 9s4.038 9 9 9 9-4.038 9-9-4.038-9-9-9zm0 1.4c4.206 0 7.6 3.394 7.6 7.6 0 4.206-3.394 7.6-7.6 7.6A7.589 7.589 0 011.4 9c0-4.206 3.394-7.6 7.6-7.6zm.16 2.368c-.695 0-1.294.143-1.8.427a2.397 2.397 0 00-1.08 1.201c-.063.14-.111.277-.145.413-.03.13-.043.273-.043.427 0 .189.048.336.144.442.102.101.245.152.428.152.164 0 .29-.04.377-.123.092-.082.168-.235.23-.457.121-.434.336-.766.645-.998.314-.236.71-.356 1.193-.356.357 0 .669.069.934.204.265.13.47.314.615.55.15.237.225.511.225.825 0 .246-.038.468-.115.666a1.58 1.58 0 01-.377.543c-.17.168-.392.34-.672.513a4.272 4.272 0 00-.819.623 2.223 2.223 0 00-.478.717 2.359 2.359 0 00-.152.875v.203c0 .208.05.383.152.528.106.144.27.216.492.216.227 0 .387-.069.479-.209a.983.983 0 00.144-.556c0-.256.034-.478.102-.666.072-.188.192-.366.361-.53.174-.164.413-.335.717-.513a3.45 3.45 0 001.1-1.02c.274-.4.413-.885.413-1.455 0-.516-.133-.973-.398-1.369-.26-.4-.623-.712-1.086-.934-.458-.226-.988-.34-1.586-.34zm-.252 8.945a.802.802 0 00-.588.24.78.78 0 00-.238.586c0 .232.08.427.238.586a.8.8 0 00.588.238.78.78 0 00.586-.238.796.796 0 00.238-.586.78.78 0 00-.238-.586.782.782 0 00-.586-.24z"
      :region="false"
  />
  <div class="container-fluid">
    <div class="row">
      <div class="col">
        <div class="border block mt-2 p-3 pb-0" style="min-height: 92vh;height: auto">
          <div class="d-md-flex align-items-start">
            <div class="nav flex-column nav-pills col-md-3 me-3" id="v-pills-tab" role="tablist" aria-orientation="vertical">
              <button class="nav-link active" id="v-pills-acesta-tab" data-bs-toggle="pill" data-bs-target="#v-pills-acesta" type="button" role="tab" aria-controls="v-pills-acesta" aria-selected="true">О сервисе</button>
              <button class="nav-link" id="v-pills-heat-maps-tab" data-bs-toggle="pill" data-bs-target="#v-pills-heat-maps" type="button" role="tab" aria-controls="v-pills-heat-map" aria-selected="false">Тепловые карты</button>
              <button class="nav-link" id="v-pills-target-groups-tab" data-bs-toggle="pill" data-bs-target="#v-pills-target-groups" type="button" role="tab" aria-controls="v-pills-target-groups" aria-selected="false">Целевые группы</button>
              <button class="nav-link" id="v-pills-rating-tab" data-bs-toggle="pill" data-bs-target="#v-pills-rating" type="button" role="tab" aria-controls="v-pills-rating" aria-selected="false">Рейтинги</button>
              <button class="nav-link" id="v-pills-vip-tab" data-bs-toggle="pill" data-bs-target="#v-pills-vip" type="button" role="tab" aria-controls="v-pills-vip" aria-selected="false">Статус VIP</button>
              <button class="nav-link" id="v-pills-profile-tab" data-bs-toggle="pill" data-bs-target="#v-pills-profile" type="button" role="tab" aria-controls="v-pills-profile" aria-selected="false">Профиль</button>
            </div>
            <div class="tab-content col-md-9 pt-4 pt-md-2 px-1 px-md-3" id="v-pills-tabContent">
              <div class="tab-pane fade show active" id="v-pills-acesta" role="tabpanel" aria-labelledby="v-pills-home-tab">
                <h3>О сервисе</h3>
                <p>Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.</p>
                <p>Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.</p>
                <p>Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.</p>
              </div>
              <div class="tab-pane fade" id="v-pills-heat-maps" role="tabpanel" aria-labelledby="v-pills-heat-maps-tab">
                <h3>Тепловые карты</h3>
                <p>Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.</p>
                <p>Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.</p>
                <p>Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.</p>
              </div>
              <div class="tab-pane fade" id="v-pills-target-groups" role="tabpanel" aria-labelledby="v-pills-target-groups-tab">
                <h3>Целевые группы</h3>
                <p>Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.</p>
                <p>Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.</p>
                <p>Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.</p>
              </div>
              <div class="tab-pane fade" id="v-pills-rating" role="tabpanel" aria-labelledby="v-pills-rating-tab">
                <h3>Рейтинги</h3>
                <p>Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.</p>
                <p>Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.</p>
                <p>Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.</p>
              </div>
              <div class="tab-pane fade" id="v-pills-vip" role="tabpanel" aria-labelledby="v-pills-target-vip">
                <h3>Статус VIP</h3>
                <p>Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.</p>
                <p>Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.</p>
                <p>Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.</p>
              </div>
              <div class="tab-pane fade" id="v-pills-profile" role="tabpanel" aria-labelledby="v-pills-profile-tab">
                <h3>Профиль пользователя</h3>
                <p>Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.</p>
                <p>Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.</p>
                <p>Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>
</template>

<script>
import DashboardHeader from "~/components/dashboard/DashboardHeader";

export default {
  auth: false,
  data() {
    return {
      title: 'Справка'
    }
  },
  head() {
    return {
      title: `${this.title}. `
    }
  },
  components: {
    DashboardHeader
  }
}
</script>

<style>
h3{margin-bottom:.7em}
.nav-pills .nav-link.active, .nav-pills .show>.nav-link{background-color:transparent;border:1px #2D4733 dotted;color:#2D4733;font-weight:bold;}
.nav-pills .nav-link{text-align:left;width:80%;color: #9bc782}
.tab-content{height:85vh}
</style>
