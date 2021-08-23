<template>
  <div class="border block mt-2 p-3">
    <div class="block-title">
      <p class="sub-title">Ваши данные</p>
    </div>
    <p>Это важно. Введите актуальные данные, мы будем использовать их для того, чтобы настроить систему для вас и предоставить наиболее подходящие отчеты.</p>
    <form @submit.prevent="saveUser()">
      <div class="mb-3 form-floating">
        <input type="text" required class="form-control" id="inputLastName" v-model="user.last_name" />
        <label class="form-label" for="inputLastName">Фамилия</label>
      </div>
<!--      <div class="form-outline">-->
<!--        <input type="text" id="form1" class="form-control" value="wee"/>-->
<!--        <label class="form-label" for="form1">Фамилия</label>-->
<!--      </div>-->
      <div class="mb-3">
        <label for="inputFirstName" class="form-label d-none"></label>
        <input type="text" required class="form-control" name="first_name" id="inputFirstName" v-model="user.first_name" placeholder="Имя *" title="Имя">
      </div>
      <div class="mb-3">
        <label for="inputMiddleName" class="form-label d-none"></label>
        <input type="text" required class="form-control" name="middle_name" id="inputMiddleName" v-model="user.middle_name" placeholder="Отчество *" title="Отчество">
      </div>
      <div class="mb-3">
        <label for="inputCompany" class="form-label d-none"></label>
        <input type="text" required class="form-control" name="company" id="inputCompany" v-model="user.company" placeholder="Место работы *" title="Место работы">
      </div>
      <div class="mb-3">
        <label for="inputPosition" class="form-label d-none"></label>
        <input type="text" required class="form-control" name="position" id="inputPosition" v-model="user.position" placeholder="Должность *" title="Должность">
      </div>
      <div class="mb-3">
        <label for="inputPhone" class="form-label d-none"></label>
        <the-mask required class="form-control" name="phone" id="inputPhone" v-model="user.phone" mask="+# (###) ###-##-##" placeholder="Телефон *" title="Телефон" />
      </div>
      <div class="mb-3">
        <v-select label="title" v-model="user.city" tagged :options="cities">
          <template #search="{attributes, events}">
            <input
                class="vs__search"
                :required="!user.city"
                v-bind="attributes"
                v-on="events"
            />
          </template>
          <div slot="no-options">Мы не нашли город, измените запрос</div>
        </v-select>
      </div>
      <button type="submit" class="btn btn-primary">Сохранить</button>
      <button type="reset" class="btn btn-secondary">Отменить</button>
    </form>
    <div class="row mt-5">
      <div class="col text-center"><a href="#" data-bs-toggle="modal" data-bs-target="#editEmailModal" class="btn btn-secondary">email</a></div>
      <div class="col text-center"><a href="#" data-bs-toggle="modal" data-bs-target="#editPasswordModal" class="btn btn-secondary">пароль</a></div>
      <div class="col text-center"><a href="#" data-bs-toggle="modal" data-bs-target="#socialAccountsModal" class="btn btn-secondary">соц</a></div>
    </div>
  </div>
</template>

<script>
import {TheMask} from "vue-the-mask";
//import 'vue-select/dist/vue-select.css';
import vSelect from "vue-select";

export default {
  name: "UserDataEdit",
  async fetch() {
    await this.$axios
      .$get('/api/geo/cities/')
      .then((response) => this.cities = response)
      .catch((err) => {
        this.$toast.error(`При получении городов произошла ошибка ${err}`)
      })
  },
  data() {
    return {
      title: 'Профиль пользователя',
      user:{
        first_name: this.$auth.user.first_name,
        middle_name: this.$auth.user.middle_name,
        last_name: this.$auth.user.last_name,
        company: this.$auth.user.company,
        position: this.$auth.user.position,
        //email: this.$auth.user.email,
        phone: this.$auth.user.phone,
        //regions: this.$auth.user.regions,
        city: this.$auth.user.city,
      },
      //regions: [],
      cities: [],
    }
  },

  methods: {
    async saveUser() {
      console.log(this.user.city)
      console.log(this.user.regions, typeof(this.user.regions))
      let data = {
        first_name: this.user.first_name,
        middle_name: this.user.middle_name,
        last_name: this.user.last_name,
        company: this.user.company,
        position: this.user.position,
        //email: this.user.email,
        phone: this.user.phone,
        city: this.user.city,
        //regions: this.user.regions,
      };
      await this.$axios
        .$patch("/api/auth/user/", data)
        .then(() => this.$toast.success('Данные успешно сохранены'))
        .then(() => {
          const updatedUser = {...this.$auth.user}

          updatedUser.first_name = this.user.first_name
          updatedUser.middle_name = this.user.middle_name
          updatedUser.last_name = this.user.last_name
          updatedUser.company =  this.user.company
          updatedUser.position =  this.user.position
          //updatedUser.email =  this.user.email
          updatedUser.phone  =  this.user.phone
          updatedUser.city = this.user.city;
          //updatedUser.regions = this.user.regions;

          this.$auth.setUser(updatedUser)
        })
        .catch((err) => {
          this.$toast.error(`Во время сохранения данных пользователя произошла ошибка: ${err}`)
        })
    },
  },
  components: {
    TheMask,
    vSelect,
  }
}
</script>

<style scoped>

</style>
