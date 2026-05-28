dnl Configuration for Rust-based PHP extension via ext-php-rs.
dnl Allows phpize to recognize this extension during source compilation (PIE fallback).

PHP_ARG_ENABLE([kreuzberg],
  [whether to enable the kreuzberg extension],
  [AS_HELP_STRING([--enable-kreuzberg],
    [Enable kreuzberg extension support])],
  [yes])

if test "$PHP_KREUZBERG_ENABLED" = "yes"; then
  dnl Recognize the extension directory for phpize/make
  PHP_NEW_EXTENSION(kreuzberg, [], $ext_shared)
fi
