<template>
<div>
  <DashboardHeader
      :title="title"
      path="M1.809 0C.819 0 0 .815 0 1.805v5.52C0 8.312.82 9.13 1.809 9.13h5.539a1.82 1.82 0 001.808-1.807v-5.52C9.156.816 8.336 0 7.348 0h-5.54zm9.677.947c-.815 0-1.494.676-1.494 1.492V6.4c0 .816.68 1.494 1.494 1.494h3.973c.815 0 1.496-.678 1.496-1.495V2.44c0-.816-.681-1.492-1.496-1.492h-3.973zM1.81 1.4h5.539a.39.39 0 01.408.405v5.52a.392.392 0 01-.408.405h-5.54a.392.392 0 01-.408-.406v-5.52A.39.39 0 011.81 1.4zm9.677.948h3.973c.066 0 .096.03.096.091V6.4c0 .062-.03.093-.096.093h-3.973c-.066 0-.093-.031-.093-.094V2.44c0-.062.027-.091.093-.091zm-.834 6.521a1.82 1.82 0 00-1.808 1.807v5.52c0 .989.82 1.804 1.808 1.804h5.54C17.18 18 18 17.185 18 16.195v-5.52c0-.988-.82-1.806-1.809-1.806h-5.539zm-8.111 1.238c-.815 0-1.496.678-1.496 1.495v3.959c0 .816.681 1.492 1.496 1.492h3.973c.815 0 1.494-.676 1.494-1.492V11.6c0-.816-.68-1.494-1.494-1.494H2.54zm8.111.163h5.54c.24 0 .408.17.408.406v5.52a.39.39 0 01-.409.404h-5.539a.39.39 0 01-.408-.405v-5.52c0-.234.168-.405.408-.405zm-8.111 1.238h3.973c.066 0 .093.031.093.094v3.959c0 .062-.027.091-.093.091H2.54c-.066 0-.096-.03-.096-.091V11.6c0-.062.03-.093.096-.093z"
  />
  <DashboardMainStats />
  <DashboardMainHeatMap />
  <div class="container-fluid">
    <div class="row">
      <DashboardMainGroups />
      <DashboardMainRating />
    </div>
  </div>
</div>
</template>

<script>
import DashboardHeader from "~/components/dashboard/DashboardHeader";
import DashboardMainStats from "~/components/dashboard/main/DashboardMainStats";
import DashboardMainHeatMap from "~/components/dashboard/main/DashboardMainHeatMap";
import DashboardMainGroups from "~/components/dashboard/main/DashboardMainGroups";
import DashboardMainRating from "~/components/dashboard/main/DashboardMainRating";
export default {
  data() {
    return {
      title: 'Обзор'
    }
  },
  head() {
    return {
      title: `${this.title}. `
    }
  },
  components: {
    DashboardHeader,
    DashboardMainHeatMap,
    DashboardMainStats,
    DashboardMainGroups,
    DashboardMainRating
  },
}
</script>

<style>
</style>
