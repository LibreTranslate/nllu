# No Language Left Unlocked 🔓

In 2022 Meta released [NLLB](https://arxiv.org/pdf/2207.04672.pdf), a set of multi-lingual models for machine translation with impressive performance. But the model weights have been released using a restrictive non-commercial license, making them unusable for most open-source projects. The models also suffer by having a limited dictionary, which causes many translations to return unknown tokens.

This repository contains the software to run NLLU, an effort to run NLLB inference at scale to generate a corpus of bitext data that can be used to train new, permissively licensed language models.

Running NLLB inference on million of sentences is intensive and it would take years to perform on a single machine. We designed a simple server architecture which can distribute batches of sentences to be translated asynchronously across machines, which can be rented cheaply with providers such as [vast.ai](https://vast.ai) or [runpod.io](https://runpod.io).

## Datasets

**Coming soon!**

We started backtranslating 15 million sentences sampled from [Paracrawl](https://paracrawl.eu/) from English to Italian using the 3.3B NLLB model.

## Usage

### Server

We use [NodeJS](https://nodejs.org) for the server.

```bash
git clone https://github.com/LibreTranslate/nllu
cd nllu/server
npm i
```

* Create a new directory in `nllu/server/data/<dataset>`
* Place a monolingual English corpus in `nllu/server/data/<dataset>/source.txt` (one sentence per line)
* Run:

```bash
cd nllu/server
node main.js -p 5555 --batch-size 100
Listening on port 5555
```

The server has persistency built-in, so you can restart it without losing state information.

### Client

```bash
docker run -ti --rm --gpus=all libretranslate/nllu --server http://<ip>:5555 --dataset <dataset> --target-lang <langcode> --batch-size 4 --split
```

We recommend tweaking `batch-size` to increase the translation speed, although in our experience it's actually faster to set this value to `1`. `--split` will reduce memory usage on the GPU by loading only `batch-size` sentences at a time during translation.

You should tweak the `--checkout-timeout` option, expressed in seconds, if you expect a client to process a batch in longer than 1 hour (the default).

#### Rebuild Docker Image

```bash
docker build -t youruser/nllu .
```

### Download Results

Once the entire dataset is translated, one can download it by visiting:

http://<ip>/download?dataset=<dataset>&lang=<lang>

Or by issuing:

```bash
cd nllu/server/<dataset>/<lang>
cat *.txt > ../merged.txt
```

### Filtering Results

We provide a script to filter the backtranslated data, following the recommendations of the NLLB paper:

```bash
python filter.py source.txt merged.txt <lang>
```

## License

AGPLv3

