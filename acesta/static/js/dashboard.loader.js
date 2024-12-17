var title = document.querySelector("title");

var titleObserver = new MutationObserver(function () {
  if ($(title).text().includes("...")) {
    $("#loader").css("display", "block");
  } else {
    $("#loader").css("display", "none");
  }
});

titleObserver.observe(title, {
  attributes: true,
  childList: true,
  characterData: true,
});
