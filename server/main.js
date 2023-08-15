const { once } = require('events');
const express = require('express');
const fs = require('fs');
const promisify = require('util').promisify;
const readline = require('readline');
const app = express();
app.use(express.json());

const readFile = promisify(fs.readFile);
const exists = promisify(fs.exists);
const readdir = promisify(fs.readdir);
const writeFile = promisify(fs.writeFile);
const mkdir = promisify(fs.mkdir);
const stat = promisify(fs.stat);

const clone = (obj) => {
  return JSON.parse(JSON.stringify(obj));
}

const argv = require('minimist')(process.argv.slice(2), {
    string: ["port", "batch-size"],
    alias: {
        p: "port", 
        b: "batch-size"
    },
    default: {port: 3000, 'batch-size': 10000}
});

let datasets = {};

let getDatasetLangs = async(d) => {
  if (!d) throw new Error("Invalid call to getDatasetLangs");

  return (await readdir(`data/${d}`)).filter(d => !d.endsWith(".txt"));
}

let initBatchesForLang = async(d, lang, numPhrases) => {
  let bs = parseInt(argv['batch-size']);
  let numBatches = Math.ceil(numPhrases / bs);
  lang = sanitize(lang);
  
  let batches = new Array(numBatches);
  for (let idx = 0; idx < batches.length; idx++){
    batches[idx] = {
      batchId: idx,
      range: [idx * bs, Math.min((idx + 1) * bs - 1, numPhrases - 1)],
      done: await exists(`data/${d}/${lang}/${idx}.txt`)
    } 
  }

  return batches;
}

let initBatches = async (d, numPhrases) => {
  let langs = await getDatasetLangs(d);
  let batches = {};
  
  for (let i = 0; i < langs.length; i++){
    batches[langs[i]] = await initBatchesForLang(d, langs[i], numPhrases);
  }

  return batches;
}

let sanitize = d => {
  return d.replace(/[^A-Za-z0-9-_]/g, "");
}

let getDataset = async (d) =>{
  if (datasets[d]) return datasets[d];
  else{
    d = sanitize(d);
    let source = `data/${d}/source.txt`;
    if (await exists(source)){
      return new Promise((resolve, reject) => {
        try{
          console.log(`Reading ${source}`);
          const phrases = [];
          const instream = fs.createReadStream(source);
          const rl = readline.createInterface({input: instream, crlfDelay: Infinity});
          rl.on('line', line => {
            line = line.trim();
            if (line !== "") phrases.push(line);
          });
          rl.on('close', async () => {
            console.log(`Read ${phrases.length} phrases from ${source}`);
      
            let batches = await initBatches(d, phrases.length);
            
            datasets[d] = {
              phrases,
              batches
            };
      
            resolve(datasets[d]);
          });
        }catch(e){
          reject(e);
        }
      });
      
    }else{
      throw new Error(`${d} does not exist`);
    }
  }
}

let getBatchesForLang = async (d, batches, lang, numPhrases) => {
  if (batches[lang]) return batches[lang];
  else{
    batches[lang] = await initBatchesForLang(d, lang, numPhrases);
    return batches[lang]; 
  }
}

let handler = f => {
  return async (req, res, next) => {
    try{
      await f(req, res);
    }catch(e){
      next(e);
    }
  };
}

app.get('/', (req, res) => {
    res.send("nllu-server running");
})

app.get('/checkout', handler(async (req, res) => {
  const { dataset, lang } = req.query;
  const timeout = parseInt(req.query.timeout);

  if (!dataset) throw new Error("Invalid dataset");
  if (!lang) throw new Error("Invalid lang");
  if (!timeout) throw new Error("Invalid timeout");

  let { batches, phrases } = await getDataset(req.query.dataset);
  batches = await getBatchesForLang(dataset, batches, lang, phrases.length);

  // Any batches left?
  let now = new Date().getTime();

  let batch = batches.find(b => !b.done && (!b.timeout || b.timeout < now));
  if (batch){
    
    // Set expiry timeout
    batch.timeout = now + timeout * 1000;

    batchRes = clone(batch);
    batchRes.phrases = phrases.slice(batch.range[0], batch.range[1] + 1);

    res.json(batchRes);
  }else{
    res.json({done: batches.find(b => !b.done) === undefined});
  }
}));

app.post('/commit', handler(async (req, res) => {
  let { dataset, batchId, phrases, lang} = req.body;
  batchId = parseInt(batchId);
  lang = sanitize(lang);
  dataset = sanitize(dataset);
  if (!dataset) throw new Error("Invalid dataset")
  if (isNaN(batchId)) throw new Error("Invalid batchId")
  if (!phrases) throw new Error("Invalid phrases")
  if (!lang) throw new Error("Invalid lang");

  const ds = await getDataset(dataset);
  const batches = await getBatchesForLang(dataset, ds.batches, lang, ds.phrases.length);
  const batch = batches.find(b => b.batchId === batchId);
  if (!batch) throw new Error("Invalid batchId");
  if (phrases.length !== batch.range[1] - batch.range[0] + 1) throw new Error("Phrase length must match batch phrase length");

  // All good, write to file
  let destDir = `data/${dataset}/${lang}`;
  if (!(await exists(destDir))){
    await mkdir(destDir, { recursive: true });
  }

  const fname = `${destDir}/${batchId}.txt`;
  await writeFile(fname, phrases.join("\n") + "\n");
  console.log(`Wrote ${fname}`);

  // Clear timeout, mark done
  delete(batch.timeout);
  batch.done = true;

  res.json({success: true});
}));

app.get('/download', handler(async (req, res) => {
  let { dataset, lang } = req.query;
  dataset = sanitize(dataset);
  lang = sanitize(lang);
  if (!dataset) throw new Error("Invalid dataset");
  if (!lang) throw new Error("Invalid lang");

  const ds = await getDataset(dataset);
  const batches = await getBatchesForLang(dataset, ds.batches, lang, ds.phrases.length);
  if (!batches.find(b => !b.done)){
    for (let idx = 0; idx < batches.length; idx++){
      const filePath = `data/${dataset}/${lang}/${idx}.txt`;
      if (!await exists(filePath)) throw new Error(`batch ${idx} is missing (this should have not happened)`);
    }
    
    const fname = `${dataset}-${lang}.txt`;
    res.setHeader('Content-Disposition', `attachment; filename=${fname}`);
    res.setHeader('Content-Type', 'text/plain');
    // res.setHeader('Content-Length', );
    console.log(`Downloading ${batches.length} batches from ${dataset}/${lang}`);

    for (let idx = 0; idx < batches.length; idx++){
      const filePath = `data/${dataset}/${lang}/${idx}.txt`;
      const filestream = fs.createReadStream(filePath);
      filestream.pipe(res);
    }
  }else{
    res.json({error: `${dataset} - ${lang} not done`});
  }
}));

app.use((err, req, res, next) => {
  console.log(err.message);
  res.json({error: err.message});
});

app.listen(argv.port,  () => {
    console.log('Listening on port ' + argv.port);
});

