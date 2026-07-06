# Figure 4: integration benchmarks disagree, and a same-data contrast separates
# the analyst's choices from the data.
#
# Layout (a | b) / (c | d): the reported rankings and the beam consensus, the
# cross-source variance decomposition, the network meta-analysis forest, and the
# pancreas same-data contrast. Independent integration benchmarks rank shared
# methods differently, much of the spread is the method-by-benchmark interaction
# rather than the method, and holding the data constant leaves the analysts'
# choices as the remaining disagreement.
#
# Panels b and c fit R models (lme4, netmeta); build_figure4 stops when the R
# toolchain is absent so the driver skips the figure.

CANON <- c("combat", "harmony", "fastmnn", "scanorama", "liger")
BENCH <- c("Tran", "scIB", "OpenProblems")
THREE_SOURCES <- c("Tran", "scIB", "OpenProblems")
FOUR_SOURCES <- c(THREE_SOURCES, "Tyler")
FIVE_SOURCES <- c(FOUR_SOURCES, "BatchBench")

# The three reported rank columns plus the beam consensus, as a rank matrix. The
# consensus pools beam's per-benchmark mean ranks over the four shared metrics.
.consensus_ranks <- function(ib, published) {
  bm <- as.character(py_to_r(ib$benchmark))
  me <- as.character(py_to_r(ib$method))
  rk <- as.numeric(py_to_r(ib$rank))
  cell_mean <- function(b, m) mean(rk[bm == b & me == m])
  mean_over_bench <- vapply(CANON, function(m) mean(vapply(BENCH, cell_mean, numeric(1), m = m)),
                            numeric(1))
  consensus <- rank(mean_over_bench, ties.method = "first")
  pub <- py_to_r(published)
  ranks <- t(vapply(CANON, function(m)
    c(vapply(BENCH, function(b) as.numeric(pub[[b]][[m]]), numeric(1)), consensus[[m]]),
    numeric(length(BENCH) + 1)))
  columns <- c(paste0(BENCH, "\n(reported)"), "beam\nconsensus")
  list(columns = columns, ranks = ranks)
}

.mean_rank_records <- function(ib) {
  recs <- ib$mean_rank_records()
  list(methods = as.character(py_to_r(recs[[1]])),
       datasets = as.character(py_to_r(recs[[2]])),
       benchmarks = as.character(py_to_r(recs[[3]])),
       scores = as.numeric(py_to_r(recs[[4]])))
}

.source_variance <- function(recs, keep) {
  idx <- which(recs$benchmarks %in% keep)
  HET$source_variance_decomposition(
    as.list(recs$methods[idx]), as.list(recs$datasets[idx]),
    as.list(recs$benchmarks[idx]), as.list(recs$scores[idx]))
}

.safe_share <- function(recs, keep) {
  tryCatch(as.numeric(py_to_r(.source_variance(recs, keep)$method_benchmark_share)),
           error = function(e) NA_real_)
}

build_figure4 <- function() {
  if (!(isTRUE(py_to_r(HET$r_available())) && isTRUE(py_to_r(HET$netmeta_available())))) {
    stop("figure 4 needs the R toolchain (lme4 and netmeta); provision it with envs/figures-r.yml")
  }
  ib <- DS$load_integration_benchmarks()
  published <- DS$load_integration_published_ranks()
  cr <- .consensus_ranks(ib, published)
  recs <- .mean_rank_records(ib)

  bump <- beam_rank_bump(CANON, cr$columns, cr$ranks, divider_after = 2)

  sv <- .source_variance(recs, FIVE_SOURCES)
  s3 <- .safe_share(recs, THREE_SOURCES)
  s4 <- .safe_share(recs, FOUR_SOURCES)
  s5 <- as.numeric(py_to_r(sv$method_benchmark_share))
  ann <- sprintf("method:benchmark share\n%.2f / %.2f / %.2f (3 / 4 / 5 sources)", s3, s4, s5)
  variance <- beam_plot(sv, "variance_components", highlight = "method:benchmark",
                        annotation = ann, title = "cross-source variance")

  arms <- ib$network_arms()
  nma <- HET$network_meta_analysis(arms[[1]], arms[[2]], arms[[3]], arms[[4]], arms[[5]])
  forest <- beam_plot(nma, "network_forest")

  pc <- DS$load_pancreas_contrast()
  sp <- as.numeric(py_to_r(pc$spearman()))
  grouped <- beam_rank_bars(
    py_to_r(pc$methods),
    list(`Tran D4` = as.numeric(py_to_r(pc$tran_mean_rank)),
         `scIB pancreas` = as.numeric(py_to_r(pc$scib_mean_rank)))) +
    labs(title = "same pancreas data, two pipelines",
         caption = sprintf("cross-pipeline Spearman %+.2f", sp))

  top <- panel_small(bump) | panel_small(variance)
  bottom <- panel_small(forest) | panel_small(grouped, "top")
  label_figure(top / bottom)
}

FIGURE4 <- list(build = build_figure4, file = "figure4_integration.pdf", height_mm = 175.0)
