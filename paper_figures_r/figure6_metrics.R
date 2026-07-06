# Figure 6: the scIB biological and batch metrics are not independent criteria.
#
# Layout a | (b / c): the oriented metric correlation heatmap on the left, the
# reliability-if-dropped bars over the dimensionality scree on the right. The
# bio/batch split is the right axis but its two sides differ: the biological
# group is one reliable two-factor scale, the batch group a weaker one-factor
# collection, so weighting the metrics as separate criteria double counts. Pure
# Python and R; no heterogeneity toolchain needed.

build_figure6 <- function() {
  q <- openproblems_metric_quality()
  corr <- panel_small(beam_plot(q$validity, "metric_correlation", title = "metric correlation"),
                      "right")
  rel <- panel_small(beam_plot(q$reliability, "metric_reliability_dropped",
                               title = "reliability if dropped"), "top")
  scree <- panel_small(beam_plot(q$dimensionality, "metric_dimensionality_scree",
                                 title = "dimensionality scree"), "top")
  fig <- (corr | (rel / scree)) + plot_layout(widths = c(1.0, 1.05))
  label_figure(fig)
}

FIGURE6 <- list(build = build_figure6, file = "figure6_metrics.pdf", height_mm = 130.0)
