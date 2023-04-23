$(function () {
  $("#inputRegion").select2({
    width: "100%",
    language: {
      noResults: function () {
        return "Регион не найден";
      },
    },
  });
})
