$("#sight-stats").bind("DOMSubtreeModified", function (e) {
  if ($(this).text().includes("...")) {
    $("#loader").css("display", "block");
  } else {
    $("#loader").css("display", "none");
  }
});
