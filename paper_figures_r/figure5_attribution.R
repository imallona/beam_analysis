# Figure 5: the rank variance split into analyst choices, datasets and benchmark
# in three settings.
#
# One stacked bar per setting. The attribution fits an R model (lme4);
# build_figure5 stops when the R toolchain is absent so the driver skips the
# figure.

.attribution_report <- function() {
  rs <- duo_rank_sensitivity()
  duo_setting <- MCDA$setting_from_rank_sensitivity(rs, "Duo clustering\n(one benchmark)")
  ib <- DS$load_integration_benchmarks()
  recs <- ib$mean_rank_records()
  sv <- HET$source_variance_decomposition(recs[[1]], recs[[2]], recs[[3]], recs[[4]])
  # No metric axis in the pooled mean-rank data, so the analyst-choice share is
  # not measurable and stays zero.
  pooled_setting <- MCDA$setting_from_source_variance(sv, 0.0, "integration\n(five benchmarks)")
  pc <- DS$load_pancreas_contrast()
  same_setting <- MCDA$setting_from_same_data_contrast(
    dict(Tran = pc$tran_mean_rank, scIB = pc$scib_mean_rank), "pancreas\n(Tran and scIB,\nby definition)")
  MCDA$attribution_synthesis(list(duo_setting, pooled_setting, same_setting))
}

build_figure5 <- function() {
  if (!isTRUE(py_to_r(HET$r_available()))) {
    stop("figure 5 attribution needs the R toolchain (lme4)")
  }
  panel_small(beam_plot(.attribution_report(), "attribution_progression"), "top")
}

FIGURE5 <- list(build = build_figure5, file = "figure5_attribution.pdf",
                width_mm = 85.0, height_mm = 60.0)
