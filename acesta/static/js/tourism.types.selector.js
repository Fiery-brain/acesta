$(function () {
  $("#inputTourismTypes").select2({
  placeholder: "  все",
    width: "100%",
    multiple: true,
    maximumSelectionLength: 3,
    language: {
      noResults: function () {
        return "Тип не найден";
      },
      maximumSelected: function() {
        return "Выберите до 3 типов";
      }
    },
  });
})
