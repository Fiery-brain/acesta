var previousScroll = 0;
$(window).scroll(function (event) {
  var scroll = $(this).scrollTop();
  if (scroll > previousScroll) {
    $(".navbar").slideUp();
  } else {
    $(".navbar").slideDown();
  }
  previousScroll = scroll;
});
