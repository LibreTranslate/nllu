#!/usr/bin/env python
import argparse
import random
import os
import re
parser = argparse.ArgumentParser(description='Filter translation bitext')
parser.add_argument('source',
    type=str,
    default=None,
    help='Source input .txt file')
parser.add_argument('target',
    type=str,
    default=None,
    help='Target input .txt file')
parser.add_argument('target_lang',
    type=str,
    default=None,
    help='Language code of target .txt file')
parser.add_argument('--skip-length-filter',
    action='store_true',
    help='Skip length filtering')
parser.add_argument('--force',
    action='store_true',
    help='Overwrite files')

# Calculated with calculate_length_ratios.py (NLLB paper page 94)
length_ratios = {"af": 0.942520082210963, "ak": 1.0009594320162465, "am": 1.4706905058384043, "ar": 1.1320246308536708, "as": 1.0344046930513096, "ay": 0.9534812874137485, "az": 0.9152745589729718, "bm": 1.038359777388881, "be": 0.8727361449982572, "bn": 1.0155668221456093, "bho": 1.0284986650236188, "bs": 0.9892614161655591, "bg": 0.9571845803324311, "ca": 0.9068940288452484, "ceb": 0.8333488650735539, "cs": 1.0277387842219758, "ckb": 1.0325363508152645, "tt": 0.968221928338863, "cy": 0.9366041236496394, "da": 0.9683642214040408, "de": 0.8542283601031674, "el": 0.8325840604383912, "en": 1, "eo": 0.9998722146793387, "et": 1.0172667365461652, "eu": 0.9371369543086412, "ee": 1.0212165458060412, "fa": 1.0518736346832465, "fi": 0.9346253480750424, "fr": 0.8414084185199373, "gd": 0.8047593641324959, "ga": 0.8615352854144445, "gl": 0.9034907301161171, "gn": 0.9859813820152157, "gu": 1.040828712286857, "ht": 1.083180481052085, "ha": 0.9302156242105419, "he": 1.2840278561245526, "hi": 0.9984926186165589, "hr": 1.0088967684744943, "hu": 0.9482238885101871, "hy": 0.8968758283245815, "nl": 0.899860558055288, "ig": 0.9882384515803101, "ilo": 0.8254368035867343, "id": 0.9180330273076585, "is": 1.0085716587448643, "it": 0.8511387585831803, "jv": 0.960282882827601, "ja": 2.2904972739580667, "kn": 0.9487053189151504, "ka": 0.9075777676286582, "kk": 0.9730985970230461, "km": 0.8304192093393473, "rw": 0.8921081697367015, "ko": 1.9868594372411166, "ku": 0.9972121327980629, "lo": 0.9994491589695281, "lv": 0.9763923226304584, "ln": 0.9247872591892211, "lt": 0.9942818113950792, "lb": 0.890363416542209, "lg": 0.9778871314196446, "lus": 0.9165879622511659, "mai": 1.0194951140065147, "ml": 0.8810150455306751, "mr": 0.9942502263377754, "mk": 0.9590396886801847, "mg": 0.8134657119465634, "mt": 0.9057392763867085, "mni-Mtei": 0.9695040733512994, "mni": 0.9695040733512994, "mn": 0.9524150050589962, "mi": 0.9040909911536379, "ms": 0.8900279391168964, "my": 0.8040564407879103, "no": 0.9815134219769193, "ne": 1.0364599718519745, "ny": 0.8848570519843093, "om": 0.8415837590750201, "or": 0.9704058537190339, "pl": 0.9379584191796216, "pt": 0.9199285772020193, "ps": 1.0240315403742966, "qu": 0.9361208939934349, "ro": 0.8872714386959603, "ru": 0.90653285252929, "sa": 1.0108599988695912, "si": 0.9834641277621977, "sk": 0.9910547481080396, "sl": 0.9980070788559038, "sm": 0.8544907277852477, "sn": 0.8904140766134194, "sd": 1.1047829156371338, "so": 0.8804016849389245, "es": 0.8389163254776089, "sq": 0.8886633210059697, "sr": 1.0054047108519848, "su": 0.9548775837083365, "sv": 0.9898089071258588, "sw": 0.9507731097542452, "ta": 0.8567420343808169, "te": 0.9842218221554861, "tg": 0.897229349119211, "tl": 0.791850882019949, "th": 1.0390664553022317, "ti": 1.4515751272508028, "ts": 0.8333821493236766, "tk": 0.9420165537998495, "tr": 0.9735526264629263, "ug": 0.9369265540105671, "uk": 0.9712791708043694, "ur": 1.0045253951697024, "uz": 0.8828166868812231, "vi": 0.9485040646710761, "xh": 0.9359249429970471, "yi": 0.927981617374546, "yo": 1.0230441106771047, "zh-CN": 2.9678076996017446, "zh": 2.9678076996017446, "zh-TW": 3.1976399673069063, "zu": 0.8916761037869562, "pa": 0.9904275181165153}

args = parser.parse_args()

if not args.target_lang in length_ratios:
    print("Language not available in length ratio database")
    exit(1)

source_dst = os.path.splitext(args.source)[0] + ".filtered.txt"
target_dst = os.path.splitext(args.target)[0] + ".filtered.txt"

if os.path.isfile(source_dst) and not args.force:
    print("File exists: %s exiting... (use --force)" % source_dst)
    exit(1)
if os.path.isfile(target_dst) and not args.force:
    pritn("File exists: %s exiting... (use --force)" % target_dst)
    exit(1)

print("Reading %s" % args.source)
print("Reading %s" % args.target)

lines = []
with open(args.source, "r", encoding="utf-8") as fs:
    with open(args.target, "r", encoding="utf-8") as ft:
        while True:
            line = fs.readline().strip()
            linet = ft.readline().strip()
            if line == '' and linet == '':
                break
            elif (line == '' and linet != '') or (line != '' and linet == ''):
                print("Source and target must have the same number of lines")
                exit(1)

            lines.append((line, linet))

print("Read %s lines" % len(lines))
lr = length_ratios[args.target_lang]
count = 0
unknown_skip = 0
length_ratio_skip = 0
length_skip = 0
duplicate_skip = 0

src_filter_d = {}
tgt_filter_d = {}

with open(source_dst, "w", encoding="utf-8") as fs:
    with open(target_dst, "w", encoding="utf-8") as ft:
        for i in range(len(lines)):
            src, tgt = lines[i]
            len_tgt = len(tgt) * lr
            len_src = len(src)

            # Skip if unknown tokens were found
            if "⁇" in tgt:
                unknown_skip += 1
                continue

            if not args.skip_length_filter:
                # Skip is length ratio is exceeded
                thresh = 9.0
                if len_tgt / len_src > thresh or len_src / len_tgt > thresh:
                    length_ratio_skip += 1
                    continue

                # Skip really short translations
                if len_tgt < 15.0:
                    length_skip += 1
                    continue

            # Remove punctuation, non-printable chars
            src_k = re.sub(r'[^\w\s]+', '', src)
            if src_k in src_filter_d:
                duplicate_skip += 1
                continue
            src_filter_d[src_k] = True

            tgt_k = re.sub(r'[^\w\s]+', '', tgt)
            if tgt_k in tgt_filter_d:
                duplicate_skip += 1
                continue
            tgt_filter_d[tgt_k] = True
            
            # Filter prefix noise from NLLB
            if tgt.startswith("- ") and not src.startswith("- "):
                tgt = tgt[2:]

            fs.write(src + "\n")
            ft.write(tgt + "\n")
            count += 1

print("Skipped: unknown (%s) length ratio (%s) length (%s) duplicate (%s)" % (unknown_skip, length_ratio_skip, length_skip, duplicate_skip))

print("Wrote %s" % source_dst)
print("Wrote %s" % target_dst)

print("Total lines: %s" % count)
