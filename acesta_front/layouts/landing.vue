<template>
  <div>
    <LandingNavigation />
    <Nuxt />
    <LandingFooter />
  </div>
</template>

<script>
import LandingNavigation from "../components/LandingNavigation";
import LandingFooter from "../components/LandingFooter";
export default {
  components: {LandingNavigation, LandingFooter}
}
</script>

<style>
@import url('https://fonts.googleapis.com/css2?family=Nunito:ital,wght@0,200;0,300;0,400;0,600;0,700;0,800;1,200;1,300;1,400;1,600;1,700&family=Open+Sans:ital,wght@0,300;0,400;0,600;0,700;0,800;1,300;1,400;1,600;1,700;1,800&display=swap');      html, body{min-width:320px;width:100%}
html, body{min-width:320px;width:100%}
body{font-family:'Nunito',sans-serif;background-color:#F8F9F8}
.w-40{width:40%}
.w-65{width:65%}
.screen-block{min-height:94vh;display:flex;align-items:center}
h2{font-weight:700}
h3{color:#BA4D6A}
.btn, footer li a{font-weight:500}
.btn svg, a svg{position:relative;bottom:2px}
.btn-primary{color:#f8f8f8; background-color:#BA4D6A; border-color:#b44b67}
.btn-primary:hover{color:#f8f8f8;background-color:#d55174;border-color:#b44b67}
.btn-primary:focus{color:#f8f8f8;background-color:#d55174;border-color:#b44b67}
.btn-vip{color:#634f11; background-color:#EFBE1B;border-color:#c9a016}
.btn-vip:hover{color:#634f11;background-color:#f6c931;border-color:#c9a016}
.btn-vip:focus{color:#634f11;background-color:#f6c931;border-color:#c9a016}
.red-l{color:#e45f83!important}
.red-l:hover{color:#f67598!important}
/*.bg-yellow{color:#634f11;background-color:#fcdc70}*/
/*.bg-green{background-color:#9bc782}*/
.yellow{color:#EFBE1B!important}
.yellow:hover{color:#f6c931!important}
.lh-1d8{position:relative;bottom:.15em;line-height:1.804}
@media (max-width:500px){
  .btn{font-size:.8em;}
}
</style>
