#!/usr/bin/env Rscript
# Install and check the R toolchain for the figure R backend: reticulate (recent
# enough for numpy 2.x), ggplot2, patchwork, the heterogeneity model packages,
# and the rbeam package from the beam checkout.
#
# Usage: Rscript tools/setup_r.R [BEAM_SRC]   (BEAM_SRC defaults to ../beam)

args <- commandArgs(trailingOnly = TRUE)
beam_src <- if (length(args) >= 1) args[1] else "../beam"
repo <- "https://cloud.r-project.org"

need <- function(pkg, min = NULL) {
  have <- requireNamespace(pkg, quietly = TRUE) &&
    (is.null(min) || utils::packageVersion(pkg) >= min)
  if (!have) utils::install.packages(pkg, repos = repo)
}

# reticulate 1.40 is the first that converts numpy 2.x arrays without the C stack
# overflow that crashes the beam plots; see envs/figures-r.yml.
need("reticulate", "1.40")
need("ggplot2", "3.4")
need("patchwork")
for (p in c("lme4", "glmmTMB", "psychotree", "partykit", "PlackettLuce",
            "qvcalc", "meta", "netmeta")) {
  need(p)
}

rv <- utils::packageVersion("reticulate")
if (rv < "1.40") {
  stop(sprintf(paste0("reticulate %s is too old for numpy 2.x and will crash the ",
                      "beam plots; upgrade to 1.40 or newer, or pin numpy below 2 ",
                      "(see envs/figures-r.yml)."), rv))
}

pkg_dir <- file.path(beam_src, "r", "beam")
if (!dir.exists(pkg_dir)) {
  stop(sprintf("rbeam source not found at %s; set BEAM_SRC to the beam checkout", pkg_dir))
}
utils::install.packages(pkg_dir, repos = NULL, type = "source")

cat(sprintf("R toolchain ready: reticulate %s, rbeam %s\n",
            rv, utils::packageVersion("rbeam")))
