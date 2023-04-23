$(function () {
  $('#inputCity').select2({
    width: "100%",
    language:{"noResults":function(){return "Город не найден";}}
  });
})
