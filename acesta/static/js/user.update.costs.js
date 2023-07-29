$(function () {
  function update_costs() {
    $.ajax({
      url: costUrl,
      method: "POST",
      data: {
        period: $("#inputPeriod").val(),
        tourism_types: $("#inputTourismTypes").val(),
        regions: $("#inputRegions").val(),
        csrfmiddlewaretoken: csrfToken
      },
    }).done(function (data) {
      $("#cost").text($.number(data.cost, 0, ".", " "));
      $("#discount").text(data.discount);
      $("#total").text($.number(data.cost - data.discount_sum, 0, ".", " "));
    });
  }
  update_costs();
  $("#inputRegions, #inputPeriod, #inputTourismTypes").on("input change", update_costs)
})
