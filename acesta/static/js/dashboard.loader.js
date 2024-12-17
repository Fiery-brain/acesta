// Select the target node.
var target = document.querySelector("title");

// Create an observer instance.
var observer = new MutationObserver(function (mutations) {
  console.log(target.innerText, $(target).text().includes("..."));
  if ($(target).text().includes("...")) {
    $("#loader").css("display", "block");
    console.log("123");
  } else {
    $("#loader").css("display", "none");
    console.log("321");
  }
});

// Pass in the target node, as well as the observer options.
observer.observe(target, {
  attributes: true,
  childList: true,
  characterData: true,
});
