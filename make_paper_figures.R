#!/usr/bin/env Rscript
# Regenerate the beam manuscript figures with the R backend into figures_r/.
#
#   Rscript make_paper_figures.R            # all figures
#   Rscript make_paper_figures.R 2 6        # only figures 2 and 6
#
# Each figure is a self-contained module under paper_figures_r/ exposing a
# FIGUREN list with build(), file and height_mm. The figures are deterministic:
# every beam.rank and rank_sensitivity call seeds at zero. Figures 4 and 5 fit R
# models (lme4, netmeta) through beam.heterogeneity; when the toolchain is absent
# they are skipped with a message rather than failing the run. Figure 1 is a
# Graphviz schematic (make figure1).
#
# The Python matplotlib figures under paper_figures/ (built by
# make_paper_figures.py) stay available as a second backend.

args <- commandArgs(trailingOnly = FALSE)
file_arg <- sub("^--file=", "", args[grep("^--file=", args)])
root <- if (length(file_arg)) normalizePath(dirname(file_arg)) else normalizePath(getwd())
fig_dir <- file.path(root, "paper_figures_r")

source(file.path(fig_dir, "common.R"))
for (name in c("figure2_duo", "figure3_domains", "figure4_integration",
               "figure5_attribution", "figure6_metrics")) {
  source(file.path(fig_dir, paste0(name, ".R")))
}

REGISTRY <- list(`2` = FIGURE2, `3` = FIGURE3, `4` = FIGURE4, `5` = FIGURE5, `6` = FIGURE6)

output_dir <- file.path(root, "figures_r")
dir.create(output_dir, showWarnings = FALSE)

wanted <- commandArgs(trailingOnly = TRUE)
if (length(wanted) == 0) wanted <- names(REGISTRY)

cat(sprintf("writing figures to %s\n", output_dir))
built <- 0
for (num in wanted) {
  fig <- REGISTRY[[num]]
  if (is.null(fig)) {
    message(sprintf("  figure %s: no such figure", num))
    next
  }
  start <- Sys.time()
  result <- tryCatch(fig$build(), error = function(e) e)
  if (inherits(result, "error")) {
    if (grepl("R toolchain", conditionMessage(result))) {
      cat(sprintf("  figure %s: skipped, needs R (%s)\n", num, conditionMessage(result)))
    } else {
      cat(sprintf("  figure %s: FAILED (%s)\n", num, conditionMessage(result)))
    }
    next
  }
  path <- file.path(output_dir, fig$file)
  save_figure(result, path, height_mm = fig$height_mm)
  cat(sprintf("  figure %s: %s (%.1fs)\n", num, path,
              as.numeric(difftime(Sys.time(), start, units = "secs"))))
  built <- built + 1
}
cat(sprintf("done: %d figure(s) written\n", built))
