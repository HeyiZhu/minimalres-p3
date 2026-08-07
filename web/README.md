# MinimalResolution chart reader

Serve this directory with any static web server, for example:

```sh
cd web
python3 -m http.server 4173
```

Then open `http://localhost:4173` in a browser. The small prime-3 AANSS
example is displayed initially. A generated dataset can be selected in the URL,
in the same style as SSeqCpp:

```text
http://localhost:4173/?data=10_BPAANSS_table
http://localhost:4173/?data=10_BPBocSS_table
```

The value after `?data=` is the generated JavaScript filename without `.js`.
You can also use **Open table** to read a `.txt` file directly without first
generating JavaScript.

## Generate webpage data

From the repository root, convert one or more result tables with:

```sh
python3 web/scripts/generate_web_data.py \
  run-p3-d10-l2-fixed/10_BPAANSS_table.txt \
  run-p3-d10-l2-fixed/10_BPBocSS_table.txt
```

This writes `web/data/10_BPAANSS_table.js` and
`web/data/10_BPBocSS_table.js`. If a source table changes, run the same command
again and refresh the browser. No rebuild or package installation is needed.

The reader parses data entirely in the browser; selected local files are not
uploaded anywhere.
