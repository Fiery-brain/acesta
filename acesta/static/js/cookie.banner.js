$(document).ready(function() {
  const cookieBanner = $('#cookieBanner');
  const cookieBannerButton = $('#cookieBannerButton');
  const cookieBannerAccepted = 'acesta_cookie_banner_accepted';
  const cookieBannerExpires = 90;

  if (!$.cookie(cookieBannerAccepted)) {
    cookieBanner.addClass('is-visible');
  }

  cookieBannerButton.on('click', function() {
    $.cookie(cookieBannerAccepted, '1', {
      expires: cookieBannerExpires,
      path: '/',
    });
    cookieBanner.removeClass('is-visible');
  });
});
