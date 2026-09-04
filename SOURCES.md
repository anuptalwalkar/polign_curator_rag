# Data sources

The demo is intentionally small enough to audit. Its seed corpus is a curated
fixture, not a claim to mirror the complete museum collection.

- Object identity, dates, media, object-page links, descriptions, and image
  endpoints are derived from the [National Gallery of Art collection pages](https://www.nga.gov/artworks/74796-japanese-footbridge)
  and the [NGA Open Data repository](https://github.com/NationalGalleryOfArt/opendata).
- Images are loaded on demand from NGA's IIIF service. The selected object
  pages mark their media public domain, and the NGA releases eligible images
  under [CC0](https://www.nga.gov/terms-and-notices).
- `data/context.json` contains short, demo-authored summaries. Each record
  carries the exact NGA page from which its factual basis was derived.
- Code in this repository is MIT licensed. The upstream records and images
  remain governed by their stated source terms.

The seventh candidate belongs to a different `candidate_set`. It is a control
record used to prove that Polign metadata filtering prevents an otherwise
relevant work from leaking into the active case.

