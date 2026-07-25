# Notation and estimands

Let \(Y_{i,s,m}\) be the 0-100 judge score for pair \(i\), system \(s\), and interface \(m\).

\[
\Delta_m = n^{-1}\sum_i(Y_{i,\mathrm{baseline},m}-Y_{i,\mathrm{HCPC-v1},m})
\]

\[
\Gamma = \Delta_{\mathrm{context}}-\Delta_{\mathrm{answer}}
\]

Observed values:

- \(\Delta_{\mathrm{answer}}=3.3160622\);
- \(\Delta_{\mathrm{context}}=13.9378238\);
- \(\Gamma=10.6217617\).

Positive \(\Gamma\) means exposing context increases the measured system contrast. It does not imply that either interface is universally correct.
