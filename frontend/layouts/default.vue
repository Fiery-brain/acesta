<template>
  <div class="dashboard">
    <DashboardMenu />
    <Nuxt />
    <DashboardFooter />
  </div>
</template>

<script>
import DashboardMenu from "~/components/dashboard/DashboardMenu";
import DashboardFooter from "~/components/dashboard/DashboardFooter";
export default {
  components: {
    DashboardMenu,
    DashboardFooter
  }
}
</script>

<style>
.dashboard{background-color:#EAEBEA;min-height: 100vh}
a{color:#97D077}
a:hover{color:#a0de7d}
.block{background-color:#f8f8f8}
.sub-title{color:#BA4D6A;font-size:1.2em;font-weight:400}
.block .block-title{min-height:2.9em}
.block select{position:relative;bottom:.2em; right: .2em}
.block-help{float:right;position:relative;left:2px;bottom:10px}
.block-footer{font-size:.8em}
.block-footer p{margin: .2em 0 0 0}
.block-footer .updated{color:#999;white-space:nowrap;}
/*position:relative;top:.2em*/
.block-footer svg{position:relative;bottom:.1em;margin-left: 2px}
.block-12{padding:  0 .76em}
.block-main-stats{
  background-repeat: no-repeat;
  background-position: 90% 20%;
}
.yellow {color: #EFBE1B}
.bg-yellow{color:#634f11;background-color:#fcdc70}
hr {background-color: #ccc}
select{border:1px #ccc solid;font-size:.85em;color:#666;border-radius:.25em}
table{font-size: .83em}
.value-title{font-weight: 500}
.value{font-size: 2.2em;color: #666}
.dashboard .page-content {margin-top:0;min-height: 94vh;}
@media (min-width:1001px) {
  .dashboard{padding-left:12.0em}
}
@media (min-width:100px) and (max-width:400px), (min-width:767px) and (max-width:1250px) {
  .value-title{font-size: .65em}
  .block-footer{font-size: .61em}
  .tail {display: none}
  .block select{font-size: .60em}
  .sub-title{font-size:.8em}
}
@media (max-width:1000px) {
  .dashboard{padding-left:3.7em}
  .block{padding-right:1em }
}
</style>
