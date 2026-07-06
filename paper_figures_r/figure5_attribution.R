# Figure 5: the attribution synthesis and the blinding check.
#
# Layout a | b: the attribution progression on the left, the blinding result on
# the right. Panel a splits the rank variance into analyst choice, dataset and
# benchmarker across three settings; the analyst-choice share rises as the
# dataset contribution is removed by design. Panel b shows that blinding the
# method names leaves the Duo ranking identical, with the seal fingerprint as the
# record that the pipeline was fixed before the labels were shown.
#
# The attribution fits an R model (lme4); build_figure5 stops when the R
# toolchain is absent so the driver skips the figure.

.attribution_report <- function() {
  rs <- duo_rank_sensitivity()
  duo_setting <- MCDA$setting_from_rank_sensitivity(rs, "Duo\n(within benchmark)")
  ib <- DS$load_integration_benchmarks()
  recs <- ib$mean_rank_records()
  sv <- HET$source_variance_decomposition(recs[[1]], recs[[2]], recs[[3]], recs[[4]])
  # No metric axis in the pooled mean-rank data, so the analyst-choice share is
  # not measurable and stays zero.
  pooled_setting <- MCDA$setting_from_source_variance(sv, 0.0, "pooled\n(cross-benchmark)")
  pc <- DS$load_pancreas_contrast()
  same_setting <- MCDA$setting_from_same_data_contrast(
    dict(Tran = pc$tran_mean_rank, scIB = pc$scib_mean_rank), "pancreas\n(same data)")
  MCDA$attribution_synthesis(list(duo_setting, pooled_setting, same_setting))
}

# Two rank columns, named and unblinded, coloured by whether they agree, with the
# seal fingerprint as the caption. Bespoke to the figure; drawn in ggplot2 so it
# matches the rbeam panels beside it.
.blinding_panel <- function() {
  d <- duo_run()
  scores <- BEAM$Scores(
    values = d$duo$tensor(DUO_METRICS), tool_names = d$duo$method_names,
    metric_ids = DUO_METRICS, dataset_names = d$duo$dataset_names, layout = "long")
  bl <- BEAM$blind(scores, seed = 0L)
  blinded <- bl[[1]]
  seal <- bl[[2]]
  blinded_run <- BEAM$rank(blinded, weights = "equal", method = "saw", seed = 0L, sensitivity = FALSE)
  unblinded_names <- as.character(py_to_r(seal$translate(blinded_run$tool_names)))

  named_names <- as.character(py_to_r(d$run$tool_names))
  named_order <- named_names[order(as.numeric(py_to_r(d$run$result$ranks)))]
  unblinded_order <- unblinded_names[order(as.numeric(py_to_r(blinded_run$result$ranks)))]

  n <- length(named_order)
  df <- data.frame(rank = seq_len(n), named = named_order, unblinded = unblinded_order,
                   agree = named_order == unblinded_order)
  df$y <- n - df$rank + 1L
  matches <- sum(df$agree)
  fingerprint <- as.character(py_to_r(seal$fingerprint))
  seed_val <- py_to_r(seal$seed)

  ggplot(df) +
    annotate("text", x = 0, y = n + 1, label = "named", hjust = 0, fontface = "bold", size = 2.6) +
    annotate("text", x = 1, y = n + 1, label = "unblinded", hjust = 0, fontface = "bold", size = 2.6) +
    geom_text(aes(x = 0, y = .data$y, label = sprintf("%2d. %s", .data$rank, .data$named)),
              hjust = 0, size = 2.2, family = "mono") +
    geom_text(aes(x = 1, y = .data$y, label = sprintf("%2d. %s", .data$rank, .data$unblinded),
                  colour = .data$agree), hjust = 0, size = 2.2, family = "mono") +
    scale_colour_manual(values = c(`TRUE` = "#228833", `FALSE` = "#cc3311"), guide = "none") +
    coord_cartesian(xlim = c(-0.05, 2.1), ylim = c(0, n + 1.6), clip = "off") +
    labs(title = "blinding leaves the ranking unchanged",
         caption = sprintf("orders identical %d/%d   seal sha256 %s...   seed %s",
                           matches, n, substr(fingerprint, 1, 16), seed_val)) +
    theme_void() +
    theme(plot.title = element_text(size = 7), plot.caption = element_text(size = 5, hjust = 0))
}

build_figure5 <- function() {
  if (!isTRUE(py_to_r(HET$r_available()))) {
    stop("figure 5 attribution needs the R toolchain (lme4)")
  }
  attribution <- panel_small(beam_plot(.attribution_report(), "attribution_progression"), "top")
  blinding <- .blinding_panel()
  fig <- (attribution | blinding) + plot_layout(widths = c(1.4, 1.0))
  label_figure(fig)
}

FIGURE5 <- list(build = build_figure5, file = "figure5_attribution.pdf", height_mm = 85.0)
