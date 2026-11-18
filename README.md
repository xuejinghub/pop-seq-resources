# PopSeq Atlas

A bilingual directory of population and pedigree sequencing datasets. Open `index.html` for English or `zh/index.html` for Chinese. The language selector opens the corresponding page and retains catalogue search and filters. Pages, image credits and file manifests are served locally. Study and archive links lead to the external publishers.

## GitHub Pages

Extract the contents of the distribution ZIP into the root of the GitHub repository. Include `.nojekyll`. Under **Settings → Pages**, select **Deploy from a branch**, the branch containing these files, and **/ (root)**. The site uses relative links and supports project URLs such as `https://<owner>.github.io/pop-seq-resources/`.

## Updating the directory

Edit `data/catalog.json` for study metadata. Chinese text is stored in the main record and the corresponding English text in `en`. Each source has one URL and two labels. Records can belong to both the population and pedigree views. Study counts retain their units, such as individuals, families, accessions or runs. The public VCF flag requires a study or archive release; locally derived calls alone do not qualify.

Public manifests are in `data/files/`. When adding one, update the matching count in the JSON record. Photo credits, source URLs and licences for the homepage are in `data/photos.json` and are rendered on each language edition’s photography page.

Regenerate both editions and their downloadable TSV catalogues with Python 3:

```sh
python3 tools/build.py
```

Lab quotations appear in the original English in both editions and link directly to the official lab pages.
