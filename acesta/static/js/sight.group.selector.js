$("#groupType").select2({
  width: "100%",
  language: {
    noResults: function () {
      return "Вид не найден";
    },
  },
  templateResult: function (group) {
    return $("<span class='option " + group.id + "'>" + group.text + "</span>");
  },
  templateSelection: function (group) {
    return $("<span class='option " + group.id + "'>" + group.text + "</span>");
  },
});

$("#groupType").on("change", function () {
  $("#groupSelector").submit();
});
