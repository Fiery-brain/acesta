<template>
    <div class="border block mt-2 p-3">
      <div class="block-title">
        <p class="sub-title  yellow">
          <svg xmlns="http://www.w3.org/2000/svg" fill="#EFBE1B" width="30" viewBox="0 0 18 18">
            <path d="M9 0C4.038 0 0 4.038 0 9s4.038 9 9 9 9-4.038 9-9-4.038-9-9-9zm0 1.4c4.206 0 7.6 3.394 7.6 7.6 0 4.206-3.394 7.6-7.6 7.6A7.589 7.589 0 011.4 9c0-4.206 3.394-7.6 7.6-7.6zM3.516 5.3a.5.5 0 00-.358.17c-.725.821-.838 2.136-.806 3.456.03 1.32.259 2.628.574 3.451a.5.5 0 00.582.309c2.522-.602 4.106-1.65 4.451-1.891h2.082c.345.241 1.929 1.29 4.451 1.89a.5.5 0 00.582-.308c.315-.823.543-2.132.574-3.451.032-1.32-.08-2.635-.806-3.455a.5.5 0 00-.367-.17.5.5 0 00-.05.002c-.907.075-1.972.522-2.86.94a21.09 21.09 0 00-1.444.741H7.88a21.09 21.09 0 00-1.443-.742c-.889-.417-1.954-.864-2.862-.94a.5.5 0 00-.058-.001zm.334 1.12a9.945 9.945 0 012.16.728c.633.298.9.456 1.127.582-.042.09-.068.179-.102.268l-1.639-.27a.5.5 0 00-.058-.007.5.5 0 00-.516.42.5.5 0 00.412.574l1.588.262v.002l-.793.148a.5.5 0 00-.398.584.5.5 0 00.582.398l.83-.156c.034.047.066.088.11.156-.368.251-1.486.877-3.374 1.418-.197-.685-.403-1.603-.427-2.625-.026-1.087.206-1.991.498-2.482zm10.3 0c.292.49.524 1.395.498 2.482-.024 1.022-.23 1.94-.427 2.625-1.888-.541-3.006-1.167-3.373-1.418.043-.068.075-.11.109-.156l.83.156a.5.5 0 00.582-.398.5.5 0 00-.398-.584l-.793-.148v-.004l1.588-.26a.5.5 0 00.412-.574.5.5 0 00-.504-.42.5.5 0 00-.07.008l-1.64.269c-.033-.09-.059-.177-.1-.268.225-.126.493-.284 1.126-.582a9.945 9.945 0 012.16-.728zM8.053 7.984H9.947c.333.542.318.982.213 1.338-.06.202-.143.362-.213.473H8.053l-.002-.002a1.927 1.927 0 01-.211-.47c-.105-.357-.12-.797.213-1.339z" color="#000" />
          </svg> Управление подпиской</p>
      </div>
      <div v-if="user.is_vip_now">
        <p class="mb-0">VIP статус активирован до <b>{{ user.vip_end | fromISOtoLocaleString }}</b> для регионов:</p>
        <ul class="my-1">
          <li v-for="region in user.regions" :key="region.code" :value="region.code">{{ region.title }}</li>
        </ul>
        <nuxt-link to="/vip/" class="btn btn-vip mt-3">Продлить VIP статус</nuxt-link>
      </div>
      <div v-else>
        <p>Активируйте <nuxt-link to="/vip/" class="yellow">VIP статус</nuxt-link> для того, чтобы получить полный доступ к аналитике и приоритетной поддержке:</p>
<!--        <nuxt-link to="/vip/" class="btn btn-vip mt-3">Стать VIP</nuxt-link>-->
        <form @submit.prevent="createOrder()">
          <div class="mb-3">
            <label for="period">Период (месяцев):</label>
            <input type="number" required v-model="order.period" name="period" id="period" @change="recalculateCosts($event)">
          </div>
          <div class="mb-3">
            <input type="checkbox" v-model="order.all_regions" @change="recalculateCosts($event)">Все
          </div>
          <p>или</p>
          <div class="mb-3">
            <v-select multiple label="title" v-model="order.regions" tagged :options="regions" @input="recalculateCosts($event)">
              <template #search="{attributes, events}">
                <input
                    class="vs__search"
                    :required="!order.all_regions && order.regions.length === 0"
                    v-bind="attributes"
                    v-on="events"
                />
              </template>
              <div slot="no-options">Мы не нашли регион, измените запрос</div>

            </v-select>
          </div>
          <div class="mb-3">
            <p id="cost_block">Стоимость: <span id="cost">{{ costs.cost | numToLocaleString }}</span></p>
            <p id="discount_block">Скидка: <span id="discount">{{ costs.discount }}%</span></p>
            <p id="total_block">Итого: <span id="total">{{ costs.total | numToLocaleString }}</span></p>
          </div>

          <button type="submit" class="btn btn-vip">Стать VIP</button>
        </form>
        <div class="overflow-scroll" style="height:14em; min-height:14em">

          <table class="table table-striped table-hover table-responsive table-sm">
            <thead>
            <tr>
              <th>Номер</th>
              <th>Период</th>
              <th class="w-75">Регионы</th>
              <th>Статус</th>
            </tr>
            </thead>
            <tbody>
              <tr v-for="order in orders" :key="order.id">
                <td>{{ order.id }}</td>
                <td>{{ order.period }}</td>
                <td v-if="order.all_regions">все</td>
                <td v-else>
                  <span v-for="(region, index) in order.regions" >
                    {{ region.title }}<span v-if="index !== Object.keys(order.regions).length - 1">, </span>
                  </span>
                </td>
                <td>{{ order.state }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
</template>

<script>
import vSelect from "vue-select";
import {mapActions, mapGetters} from "vuex";

export default {
  name: "UserSubscriptionEdit",
  async fetch() {
    await this.$axios.
      $get('/api/user/order/')
      .then((response) => this.orders = response)
      .catch((err) => {
        this.$toast.error(`При получении заявок произошла ошибка ${err}`)
      })

    await this.$axios
      .$get('/api/geo/regions/')
      .then((response) => this.regions  = response)
      .catch((err) => {
        this.$toast.error(`При получении регионов произошла ошибка ${err}`)
      })
  },
  data() {
    return {
      user: {
        regions: this.$auth.user.regions,
        is_vip: this.$auth.user.is_vip,
        is_vip_now: this.$auth.user.is_vip_now,
        vip_end: this.$auth.user.vip_end,
      },
      regions: [],
      orders: [],
      order: {
        period: 6,
        regions: this.$auth.user.regions,
        all_regions: false
      },
      costs: {
        cost: 0,
        discount: 0,
        total: 0
      }
    }
  },
  async mounted() {
    this.loadPublicPrice()
    this.recalculateCosts()
  },
  computed: {
    ...mapGetters({
      public_price: 'public_price/getPublicPrice',
    })
  },
  methods: {
    ...mapActions({
      loadPublicPrice: 'public_price/loadPublicPrice'
    }),
    recalculateCosts() {
      if (this.order.all_regions === true) {
        this.costs.cost = this.order.period
            * this.public_price.all_regions

      } else {
        this.costs.cost = this.order.period * this.order.regions.length
            * this.public_price.one_region
      }

      if (this.order.period < 6) {
        this.costs.discount = 0
      } else {
        this.costs.discount = this.public_price.gt_6_discount
      }

      this.costs.total = this.costs.cost * ((100 - this.costs.discount) / 100)
    },

    async createOrder() {
      let data = {
        period: this.order.period,
        all_regions: this.order.all_regions || false,
        regions: this.order.regions
      };
      console.log(data)
      await this.$axios
        .post("/api/user/order/", data)
        .then(() => this.$toast.success('Спасибо! Мы получили вашу заявку.'))
        .catch((err) => {
          this.$toast.error(`При создании заявки произошла ошибка: ${err}`)
        })
      }
    },
  components: {
    vSelect
  }
}
</script>

<style scoped>

</style>
