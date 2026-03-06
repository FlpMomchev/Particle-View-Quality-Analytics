The `data` directory holds input files for the pipeline.  The real project used
internal production data; for privacy reasons the repository only ships with a few
synthetic CSVs that reproduce the schema.  You can point the configuration
file at your own CSVs if you have them.

## Files

`sample/particle_view_sample.csv` – particle‑level measurements.  Each row
corresponds to a single particle and must include at least the following
columns:

* `SAMPLE_ID` – integer identifier of the sample the particle belongs to.
* `PARTICLE_ID` – unique identifier of the particle within its sample.
* `DATATIMESTAMP` – timestamp when the particle was measured.
* `LENGTH` – length of the particle (mm).
* `WIDTH` – width of the particle (mm).
* `THICKNESS_AVG` – average thickness of the particle (mm).
* `AREA` – projected area of the particle (mm²).

`sample/process_data_sample.csv` – simplified process log.  It should
contain at least `DATATIMESTAMP` and `MATERIALNO` columns; additional
columns are ignored by the current code.  The timestamps should cover the
period when particle measurements were taken so that samples can be aligned
with material numbers.

`sample/quality_data_sample.csv` – quality metrics aggregated at the
sample level.  It must contain `SAMPLE_ID` and one or more target
variables whose names are listed in the configuration file under
`correlation_targets`.

If you place your own data files into `data/`, update `configs/example_config.yaml`
accordingly.