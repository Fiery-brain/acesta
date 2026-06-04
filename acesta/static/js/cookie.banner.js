$(document).ready(function() {
  const cookieBanner = $('#cookieBanner');
  const cookieBannerButton = $('#cookieBannerButton');
  const cookieBannerAccepted = 'acesta_cookie_banner_accepted';

  if (!$.cookie(cookieBannerAccepted)) {
    cookieBanner.addClass('is-visible');
  }

  cookieBannerButton.on('click', function() {
    $.cookie(cookieBannerAccepted, '1', { path: '/' });
    cookieBanner.removeClass('is-visible');
  });
});
