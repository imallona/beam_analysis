# Figure 2: a stable leading method over an unstable lower order (Duo 2018).
#
# Layout a / (b | c): the funky heatmap on top, the specification curve and the
# rank-variance decomposition below. Seurat stays first across the analyst's
# choices while the lower order does not, and most of the rank movement comes
# from the dataset, not the choices.

build_figure2 <- function() {
  d <- duo_run()
  rs <- duo_rank_sensitivity()
  curve <- MCDA$specification_curve(rs)

  funky <- panel_small(beam_funky_heatmap(d$run, show_smaa = FALSE,
                                          show_aggregation = TRUE), "bottom") &
    theme(axis.text.x.top = element_text(angle = 90, hjust = 0, vjust = 0.5, size = 5.5),
          axis.title.x = element_text(size = 6))
  spec <- panel_small(beam_plot(curve, "specification_curve"), "bottom") &
    guides(fill = guide_legend(nrow = 3, byrow = TRUE))
  varbars <- panel_small(beam_plot(rs, "rank_sensitivity"))

  bottom <- (wrap_elements(full = spec) | varbars) + plot_layout(widths = c(1.9, 1.0))
  fig <- wrap_elements(full = funky) / bottom + plot_layout(heights = c(1.4, 1.1))
  label_figure(fig)
}

FIGURE2 <- list(build = build_figure2, file = "figure2_duo.pdf", height_mm = 195.0)
