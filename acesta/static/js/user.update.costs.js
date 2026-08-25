$(function () {

  function setRegions() {
    if ($("#inputDistrict").val()) {
      $("#inputRegions")
        .val(federalDistricts[$("#inputDistrict").val()])
        .trigger("change");
    }
  }

  const districtSets = new Map(
    Object.entries(federalDistricts).map(([name, regions]) => [
      name,
      new Set(regions),
    ])
  );

  function findMatchingFederalDistrictFast(selectedRegions, selectedSet) {
    for (const [districtName, districtSet] of districtSets) {
      if (
        selectedRegions.length === districtSet.size &&
        [...selectedSet].every((region) => districtSet.has(region))
      ) {
        return districtName;
      }
    }

    return null;
  }

  function updateSelectedDistrict() {
    const selectedRegions = $("#inputRegions").val() || [];
    const selectedSet = new Set(selectedRegions);

    const district = findMatchingFederalDistrictFast(
      selectedRegions,
      selectedSet
    );

    $("#inputDistrict").val(district || "");
  }

  function update_costs() {
    $.ajax({
      url: costUrl,
      method: "POST",
      data: {
        federal_district: $("#inputDistrict").val(),
        period: $("#inputPeriod").val(),
        tourism_types: $("#inputTourismTypes").val(),
        regions: $("#inputRegions").val(),
        csrfmiddlewaretoken: csrfToken,
      },
    }).done(function (data) {
      $("#cost").text($.number(data.cost, 0, ".", " "));
      const discounts = [data.discount, data.promotion_discount]
        .filter((discount) => discount)
        .map((discount) => `${discount}%`);
      $("#discount").text(discounts.join(" + ") || "0%");
      $("#total").text($.number(data.total, 0, ".", " "));
      if (!$("#inputPromo").val() && data.promo_code) {
        $("#inputPromo").val(data.promo_code);
      }
    });
  }

  setRegions();
  update_costs();
  $("#inputRegions, #inputPeriod, #inputTourismTypes").on(
    "change",
    function (e) {
      if (e.target.id == "inputRegions") {
        updateSelectedDistrict();
      } update_costs();
    }
  );

  $("#inputDistrict").on("change", function (e) {
    setRegions();
  });
})
