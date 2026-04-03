$(function () {
  $("#inputSegment").select2({
    width: "100%",
    language: {
      noResults: function () {
        return "Сегмент не найден";
      },
    },
  });
})
