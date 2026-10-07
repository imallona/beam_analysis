# Supplementary figure S1: the Duo ranking with the method names and after
# blinding, ranking and unblinding.

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
    labs(caption = sprintf("positions identical %d of %d   seal sha256 %s...   seed %s",
                           matches, n, substr(fingerprint, 1, 16), seed_val)) +
    theme_void() +
    theme(plot.caption = element_text(size = 5, hjust = 0))
}

build_figure_s1 <- function() {
  .blinding_panel()
}

FIGURES1 <- list(build = build_figure_s1, file = "figureS1_blinding.pdf",
                 width_mm = 85.0, height_mm = 75.0)
