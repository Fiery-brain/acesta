$.cookie("innerWidth", window.innerWidth, { path: "/" });
$.cookie("innerHeight", window.innerHeight, { path: "/" });
$(window).on("resize", function (e) {
  $.cookie("innerWidth", window.innerWidth, { path: "/" });
  $.cookie("innerHeight", window.innerHeight, { path: "/" });
});
