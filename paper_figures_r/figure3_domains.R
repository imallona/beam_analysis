# Figure 3: M4 forecasting and GPTCelltype cell type annotation.
#
# Layout (a | b) / (c | d): the M4 rank variance decomposition and specification
# curve on top, the GPTCelltype mean agreement and critical difference diagram
# below.

GPT_HEAD <- c("GPT-4", "GPT-3.5", "CellMarker2.0", "SingleR", "ScType")
GPT_CLASSICAL <- c("CellMarker2.0", "SingleR", "ScType")

.m4_rank_sensitivity <- function() {
  m4 <- DS$load_m4()
  ctx <- MCDA$registry_context(m4$metric_ids, "saw")
  MCDA$rank_sensitivity(
    m4$tensor(), ctx$polarity, normalization = ctx$normalization, bounds = ctx$bounds,
    baselines = ctx$baselines, targets = ctx$targets,
    tool_names = m4$method_names, dataset_names = m4$frequency_names)
}

# The head block: the five methods Hou and Ji compare directly, scored on the
# datasets where all five were run, so the composite bar and the
# critical-difference panel read off one set of methods and datasets.
.gpt_block <- function() {
  g <- DS$load_gptcelltype()
  mn <- as.character(py_to_r(g$method_names))
  idx <- match(GPT_HEAD, mn)
  sub <- py_to_r(g$scores)[idx, , , drop = FALSE]
  complete <- !apply(is.na(sub[, , 1]), 2, any)
  list(agreement = sub[, complete, 1, drop = FALSE][, , 1], block = sub[, complete, , drop = FALSE])
}

.gpt_composite_bar <- function(agreement) {
  mean_agreement <- rowMeans(agreement)
  ord <- order(-mean_agreement)
  df <- data.frame(
    method = factor(GPT_HEAD[ord], levels = GPT_HEAD[ord]),
    value = mean_agreement[ord],
    kind = ifelse(GPT_HEAD[ord] %in% GPT_CLASSICAL, "classical", "language model"))
  ggplot(df, aes(.data$method, .data$value, fill = .data$kind)) +
    geom_col(show.legend = FALSE) +
    scale_fill_manual(values = c(classical = "#888888",
                                 `language model` = unname(ROLE["data"]))) +
    labs(x = NULL, y = "mean agreement (higher is better)") +
    beam_theme() +
    theme(axis.text.x = element_text(angle = 30, hjust = 1))
}

build_figure3 <- function() {
  rs_m4 <- .m4_rank_sensitivity()
  curve <- MCDA$specification_curve(rs_m4)
  gpt <- .gpt_block()
  cd <- MCDA$critical_difference(gpt$block[, , 1], "higher_is_better", tool_names = GPT_HEAD)

  a <- panel_small(beam_plot(rs_m4, "rank_sensitivity"))
  b <- panel_small(beam_plot(curve, "specification_curve"), "bottom") &
    guides(fill = guide_legend(nrow = 2, byrow = TRUE))
  c <- panel_small(.gpt_composite_bar(gpt$agreement))
  d <- panel_small(beam_plot(cd, "critical_difference"))

  top <- (a | wrap_elements(full = b)) + plot_layout(widths = c(1.0, 1.4))
  bottom <- (c | d) + plot_layout(widths = c(1.0, 1.4))
  label_figure(top / bottom + plot_layout(heights = c(1.35, 1.0)))
}

FIGURE3 <- list(build = build_figure3, file = "figure3_domains.pdf", height_mm = 170.0)
