$("#consultationInputGroupChannel,#presentationInputGroupChannel").select2({
  minimumResultsForSearch: -1,
  language: {
    noResults: function () {
      return "Канал не найден";
    },
  },
  templateResult: function (channel) {
    return $(
      "<span class='option bg-" + channel.id + "'>" + channel.text + "</span>"
    );
  },
  templateSelection: function (channel) {
    return $(
      "<span class='option bg-" + channel.id + "'>" + channel.text + "</span>"
    );
  },
});
$("#consultationInputGroupChannel,#presentationInputGroupChannel").on(
  "select2:select",
  function (e) {
    var data = e.params.data;
    if (data.id === "telegram") {
      $("#consultationInputChannel,#presentationInputChannel")
        .attr("placeholder", "@your_telegram_name")
        .attr("pattern", "[^\\s]+")
        .unmask();
    } else {
      $("#consultationInputChannel,#presentationInputChannel")
        .attr("placeholder", "+7(333) 222-11-00")
        .attr("pattern", "\\+[0-9]\\([0-9]{3}\\) [0-9]{3}-[0-9]{2}-[0-9]{2}")
        .mask("+0(000) 000-00-00");
    }
  }
);
