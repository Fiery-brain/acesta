$(function () {
  $("#inputRegions").select2({
    width: "100%",
    multiple: true,
    language: {
      noResults: function () {
        return "Регион не найден";
      },
    },
  });
})
