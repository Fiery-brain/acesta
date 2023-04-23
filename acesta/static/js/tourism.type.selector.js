$("#inputTourismType").select2({
  width: "100%",
  language: {
    noResults: function () {
      return "Вид не найден";
    },
  },
  templateResult: function (tourism_type) {
    return $(
      "<span class='option bg-" +
        tourism_type.id +
        "'>" +
        tourism_type.text +
        "</span>"
    );
  },
  templateSelection: function (tourism_type) {
    return $(
      "<span class='option bg-" +
        tourism_type.id +
        "'>" +
        tourism_type.text +
        "</span>"
    );
  },
});

$("#inputTourismType").on("change", function () {
  $("#tourism-type").submit();
});
