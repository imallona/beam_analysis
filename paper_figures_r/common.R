# Shared scaffolding for the beam manuscript figures, R backend.
#
# The figures are drawn with rbeam's native ggplot2 and patchwork builders, the
# same plots the beam HTML report shows. The numbers come from the beam Python
# package through reticulate; only the rendering is R. The Python matplotlib
# figures under paper_figures/ are kept as a second backend.
#
# Genome Biology asks for figures at most 170 mm wide (85 mm half width) and at
# most 225 mm tall, fonts embedded, thin lines legible. save_figure writes a
# vector PDF at the exact millimetre size (cairo, fonts embedded) plus a PNG
# preview, so each figureN module only lays out its panels.
#
# Shared dataset preparation is cached here because several figures use the same
# runs. Every beam.rank and rank_sensitivity call seeds at zero, so the figures
# are deterministic.

suppressWarnings(suppressMessages({
  library(reticulate)
  library(ggplot2)
  library(patchwork)
}))

# Point reticulate at the Python that has beam installed. Order: RETICULATE_PYTHON
# if set (reticulate reads it directly), else BEAM_VENV/bin/python, else the
# .venv the Makefile builds, searched from the working directory upward. Must run
# before the first import.
local({
  if (nzchar(Sys.getenv("RETICULATE_PYTHON", ""))) return(invisible())
  venv <- Sys.getenv("BEAM_VENV", "")
  candidates <- if (nzchar(venv)) file.path(venv, "bin", "python") else character(0)
  dir <- normalizePath(getwd())
  repeat {
    candidates <- c(candidates, file.path(dir, ".venv", "bin", "python"))
    parent <- dirname(dir)
    if (identical(parent, dir)) break
    dir <- parent
  }
  hit <- candidates[file.exists(candidates)]
  if (length(hit) > 0) reticulate::use_python(hit[1], required = TRUE)
})

if (!requireNamespace("rbeam", quietly = TRUE)) {
  stop("rbeam is not installed; run `R CMD INSTALL ../beam/r/beam` (see README).")
}
library(rbeam)

BEAM  <- reticulate::import("beam")
DS    <- reticulate::import("beam.datasets")
MCDA  <- reticulate::import("beam.mcda")
HET   <- reticulate::import("beam.heterogeneity")
CARDS <- reticulate::import("beam.cards")
NP    <- reticulate::import("numpy")

`%||%` <- function(a, b) if (is.null(a) || (length(a) == 1 && !nzchar(a))) b else a

# Journal geometry.
MM_PER_INCH  <- 25.4
FULL_WIDTH_MM <- 170.0
HALF_WIDTH_MM <- 85.0
MAX_HEIGHT_MM <- 225.0
mm <- function(value_mm) value_mm / MM_PER_INCH

# The shared attribution colours, taken from rbeam so the figures and the library
# use one key: analyst choice red, data blue, benchmarker green.
ROLE <- beam_palette(roles = TRUE)

# rbeam panels are sized to be saved on their own, so a multi-panel figure
# shrinks their fonts and legends to fit column width and drops their titles,
# which the figure legend states. legend is "none", "right", or "bottom".
panel_small <- function(p, legend = "none") {
  p & theme(
    plot.title = element_blank(),
    plot.subtitle = element_blank(),
    axis.title = element_text(size = 6),
    axis.text = element_text(size = 5.5),
    legend.position = legend,
    legend.title = element_text(size = 5.5),
    legend.text = element_text(size = 5),
    legend.key.size = unit(2.5, "mm"),
    plot.caption = element_text(size = 5.5, hjust = 0.5)
  )
}

# Tag the top-level panels a, b, c ... in order. The panels are shrunk with
# panel_small before composing, so here we only set the tag look.
label_figure <- function(fig) {
  (fig + plot_annotation(tag_levels = "a")) &
    theme(plot.tag = element_text(size = 10, face = "bold"))
}

# Write a figure to a vector PDF at its exact millimetre size, fonts embedded via
# cairo, plus a 300 dpi PNG preview of the same canvas.
save_figure <- function(fig, path, width_mm = FULL_WIDTH_MM, height_mm) {
  if (height_mm > MAX_HEIGHT_MM) {
    stop(sprintf("height %.0f mm exceeds the %.0f mm limit", height_mm, MAX_HEIGHT_MM))
  }
  ggsave(path, fig, device = cairo_pdf, width = mm(width_mm), height = mm(height_mm),
         units = "in", limitsize = FALSE)
  preview <- sub("\\.pdf$", ".png", path)
  ggsave(preview, fig, device = "png", width = mm(width_mm), height = mm(height_mm),
         units = "in", dpi = 300, limitsize = FALSE)
  invisible(path)
}

# ---- Shared dataset preparation, memoized so a figure that reads the Duo run
# does not rebuild it and the driver can build several figures in one process.

.cache <- new.env(parent = emptyenv())
memo <- function(key, expr) {
  if (is.null(.cache[[key]])) .cache[[key]] <- expr
  .cache[[key]]
}

DUO_METRICS <- c("ari", "runtime", "shannon_entropy_diff")

# The Duo 2018 run on the three analysis metrics, returned with the dataset.
duo_run <- function() memo("duo_run", {
  duo <- DS$load_duo2018()
  scores <- BEAM$Scores(
    values = duo$tensor(DUO_METRICS), tool_names = duo$method_names,
    metric_ids = DUO_METRICS, dataset_names = duo$dataset_names, layout = "long")
  run <- beam_rank(scores, weights = "equal", method = "saw", seed = 0L)
  list(duo = duo, run = run)
})

# Rank sensitivity over the Duo tool by dataset by metric tensor.
duo_rank_sensitivity <- function() memo("duo_rs", {
  d <- duo_run()
  ctx <- d$run$context
  MCDA$rank_sensitivity(
    d$duo$tensor(DUO_METRICS), ctx$polarity,
    normalization = ctx$normalization, bounds = ctx$bounds,
    baselines = ctx$baselines, targets = ctx$targets, missing = "worst",
    tool_names = d$duo$method_names, dataset_names = d$duo$dataset_names)
})

# The validity, reliability and dimensionality reports on the scIB metrics.
openproblems_metric_quality <- function() memo("op_quality", {
  op <- DS$load_openproblems("batch_integration")
  metrics <- setdiff(as.character(py_to_r(op$metric_ids)), "hvg_overlap")
  tensor <- py_to_r(op$tensor(metrics))
  keep <- apply(!apply(is.na(tensor), c(1, 2), all), 1, all)
  tensor <- NP$asarray(tensor[keep, , , drop = FALSE])
  bio <- c("ari", "nmi", "asw_label", "isolated_label_f1", "isolated_label_asw",
           "cell_cycle_conservation", "hvg_overlap", "clisi")
  groups <- as.list(ifelse(metrics %in% bio, "bio", "batch"))
  pol <- CARDS$polarities_for(metrics)
  list(
    validity = MCDA$metric_validity(tensor, pol, groups, metric_ids = as.list(metrics)),
    reliability = MCDA$metric_reliability(tensor, pol, groups, metric_ids = as.list(metrics)),
    dimensionality = MCDA$metric_dimensionality(tensor, pol, groups, metric_ids = as.list(metrics))
  )
})
