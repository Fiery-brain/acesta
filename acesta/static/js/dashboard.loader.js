var target = document.querySelector("title");

var observer = new MutationObserver(function (mutations) {
  if ($(target).text().includes("...")) {
    $("#loader").css("display", "block");
  } else {
    $("#loader").css("display", "none");
  }
});

observer.observe(target, {
  attributes: true,
  childList: true,
  characterData: true,
});
