<template>
  <div>
    <h1 v-if="error.statusCode === 404">Страница не найдена</h1>
    <h1 v-else-if="error.statusCode === 403">Доступ запрещен</h1>
    <h1 v-else>Ошибка</h1>
  </div>
</template>

<script>
export default {
  props: ['error']
}
</script>

<style scoped>

</style>