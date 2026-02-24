#' Clear the extraction cache
#'
#' @export
clear_cache <- function() {
  clear_cache_native()
}

#' Get cache statistics
#'
#' @return Named list with total_entries and total_size_bytes.
#' @export
cache_stats <- function() {
  cache_stats_native()
}
