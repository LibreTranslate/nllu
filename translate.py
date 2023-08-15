import requests
import ctranslate2
import sentencepiece as spm
import argparse 
import os
import time

parser = argparse.ArgumentParser(description='Translate NLLU datasets')
parser.add_argument('--server',
    type=str,
    default="http://localhost:3000",
    help='URL endpoint of nllu-server. Default: %(default)s')
parser.add_argument('--dataset',
    type=str,
    default="test-ds",
    help='Source nllu-server dataset name. Default: %(default)s')
parser.add_argument('--target-lang',
    type=str,
    default="it",
    help='Target language code to translate to. Default: %(default)s')
parser.add_argument('--device-index',
    type=str,
    default=None,
    help='CUDA device indexes. Default: %(default)s')
parser.add_argument('--batch-size',
    type=int,
    default=64,
    help='Batch size. Default: %(default)s')
parser.add_argument('--split',
    action='store_true',
    default=False,
    help='Split input in batch sizes chunks. Default: %(default)s')
parser.add_argument('--checkout-timeout',
    type=int,
    default=86400,
    help='Checkout timeout')
parser.add_argument('--model',
    type=str,
    default='./model',
    help='NLLB + sentencepiece model directory. Default: %(default)s')
parser.add_argument('--beam-size',
    type=int,
    default=4,
    help='Beam size. Default: %(default)s')
args = parser.parse_args()

nllb_langs = {
    "af":"afr_Latn",
    "ak":"aka_Latn",
    "am":"amh_Ethi",
    "ar":"arb_Arab",
    "as":"asm_Beng",
    "ay":"ayr_Latn",
    "az":"azj_Latn",
    "bm":"bam_Latn",
    "be":"bel_Cyrl",
    "bn":"ben_Beng",
    "bho":"bho_Deva",
    "bs":"bos_Latn",
    "bg":"bul_Cyrl",
    "ca":"cat_Latn",
    "ceb":"ceb_Latn",
    "cs":"ces_Latn",
    "ckb":"ckb_Arab",
    "tt":"crh_Latn",
    "cy":"cym_Latn",
    "da":"dan_Latn",
    "de":"deu_Latn",
    "el":"ell_Grek",
    "en":"eng_Latn",
    "eo":"epo_Latn",
    "et":"est_Latn",
    "eu":"eus_Latn",
    "ee":"ewe_Latn",
    "fa":"pes_Arab",
    "fi":"fin_Latn",
    "fr":"fra_Latn",
    "gd":"gla_Latn",
    "ga":"gle_Latn",
    "gl":"glg_Latn",
    "gn":"grn_Latn",
    "gu":"guj_Gujr",
    "ht":"hat_Latn",
    "ha":"hau_Latn",
    "he":"heb_Hebr",
    "hi":"hin_Deva",
    "hr":"hrv_Latn",
    "hu":"hun_Latn",
    "hy":"hye_Armn",
    "nl":"nld_Latn",
    "ig":"ibo_Latn",
    "ilo":"ilo_Latn",
    "id":"ind_Latn",
    "is":"isl_Latn",
    "it":"ita_Latn",
    "jv":"jav_Latn",
    "ja":"jpn_Jpan",
    "kn":"kan_Knda",
    "ka":"kat_Geor",
    "kk":"kaz_Cyrl",
    "km":"khm_Khmr",
    "rw":"kin_Latn",
    "ko":"kor_Hang",
    "ku":"kmr_Latn",
    "lo":"lao_Laoo",
    "lv":"lvs_Latn",
    "ln":"lin_Latn",
    "lt":"lit_Latn",
    "lb":"ltz_Latn",
    "lg":"lug_Latn",
    "lus":"lus_Latn",
    "mai":"mai_Deva",
    "ml":"mal_Mlym",
    "mr":"mar_Deva",
    "mk":"mkd_Cyrl",
    "mg":"plt_Latn",
    "mt":"mlt_Latn",
    "mni-Mtei":"mni_Beng",
    "mni":"mni_Beng",
    "mn":"khk_Cyrl",
    "mi":"mri_Latn",
    "ms":"zsm_Latn",
    "my":"mya_Mymr",
    "no":"nno_Latn",
    "ne":"npi_Deva",
    "ny":"nya_Latn",
    "om":"gaz_Latn",
    "or":"ory_Orya",
    "pl":"pol_Latn",
    "pt":"por_Latn",
    "ps":"pbt_Arab",
    "qu":"quy_Latn",
    "ro":"ron_Latn",
    "ru":"rus_Cyrl",
    "sa":"san_Deva",
    "si":"sin_Sinh",
    "sk":"slk_Latn",
    "sl":"slv_Latn",
    "sm":"smo_Latn",
    "sn":"sna_Latn",
    "sd":"snd_Arab",
    "so":"som_Latn",
    "es":"spa_Latn",
    "sq":"als_Latn",
    "sr":"srp_Cyrl",
    "su":"sun_Latn",
    "sv":"swe_Latn",
    "sw":"swh_Latn",
    "ta":"tam_Taml",
    "te":"tel_Telu",
    "tg":"tgk_Cyrl",
    "tl":"tgl_Latn",
    "th":"tha_Thai",
    "ti":"tir_Ethi",
    "ts":"tso_Latn",
    "tk":"tuk_Latn",
    "tr":"tur_Latn",
    "ug":"uig_Arab",
    "uk":"ukr_Cyrl",
    "ur":"urd_Arab",
    "uz":"uzn_Latn",
    "vi":"vie_Latn",
    "xh":"xho_Latn",
    "yi":"ydd_Hebr",
    "yo":"yor_Latn",
    "zh-CN":"zho_Hans",
    "zh":"zho_Hans",
    "zh-TW":"zho_Hant",
    "zu":"zul_Latn",
    "pa":"pan_Guru"
}

batch_size = args.batch_size
tgt_lang = nllb_langs[args.target_lang]
src_lang = nllb_langs["en"]
ct_model_path = args.model
sp_model_path = os.path.join(os.path.join(args.model, "sp.model"))

print("NLLU-server: %s" % args.server)
print("Target lang: %s" % args.target_lang)
device = "cuda" if ctranslate2.get_cuda_device_count() > 0 else "cpu"
print("Running on %s" % device)
device_index = [0]
if device == "cuda":
    device_index = [0]
    if args.device_index is not None:
        device_index = [int(d) for d in args.device_index.split(",")]
    print("Device index: %s" % device_index)

sp = spm.SentencePieceProcessor()
sp.load(sp_model_path)

translator = ctranslate2.Translator(ct_model_path, device, device_index=device_index)

def s_req(func, endpoint, **kwargs):
    retries = 0
    while retries < 10:
        try:
            r = func(f'{args.server}{endpoint}', timeout=60, **kwargs)
            res = r.json()
            if 'error' in res:
                print("Server: " + res['error'])
                exit(1)
            return res
        except Exception as e:
            print(e)
            print("Retrying...")
            retries += 1
            time.sleep(10)
    print("Too many retries, quitting")
    exit(1)

def s_get(endpoint):
    return s_req(requests.get, endpoint)

def s_post(endpoint, data):
    return s_req(requests.post, endpoint, json=data)

# Fetch from server
translator = ctranslate2.Translator(ct_model_path, device=device, compute_type="auto", inter_threads=os.cpu_count())

while True:
    res = s_get(f'/checkout?dataset={args.dataset}&lang={args.target_lang}&timeout={args.checkout_timeout}')
    if res['done']:
        print("Done!")
        exit(0)
    if not 'batchId' in res:
        print("Done (empty batchId)")
        exit(0)

    print("Batch ID: %s" % res['batchId'])
    print("Range: %s" % res['range'])

    now = time.time()
    print("Translating...")

    translations = []

    def translate_phrases(phrases):
        global batch_size, translations
        if len(phrases) == 0:
            return []

        src_text = [sent.strip() for sent in phrases]
        tgt_prefix = [[tgt_lang]] * len(src_text)

        # Subword the source sentences
        src_subworded = sp.encode_as_pieces(src_text)
        src_subworded = [[src_lang] + sent + ["</s>"] for sent in src_subworded]

        # Translate the source sentences
        while True:
            try:
                translations_subworded = translator.translate_batch(src_subworded, batch_type="tokens", max_batch_size=batch_size, beam_size=args.beam_size, target_prefix=tgt_prefix, return_scores=False)
                break
            except RuntimeError as e:
                if "out of memory" in str(e) and batch_size > 1:
                    batch_size //= 2
                    print(str(e) + f", setting batch size to {batch_size}")
        translations_subworded = [translation.hypotheses[0] for translation in translations_subworded]
        for translation in translations_subworded:
            if tgt_lang in translation:
                translation.remove(tgt_lang)

        # Desubword the target sentences
        translations += sp.decode(translations_subworded)
    
    if args.split:
        i = 0
        while i < len(res['phrases']):
            translate_phrases(res['phrases'][i:i+batch_size])
            i += batch_size
    else:
        translate_phrases(res['phrases'])

    
    print("Completed in %s seconds, committing..." % (time.time() - now))

    s_post('/commit', {
        'dataset': args.dataset, 'batchId': res['batchId'], 'phrases': translations, 'lang': args.target_lang
    })