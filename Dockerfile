FROM nvidia/cuda:11.2.2-runtime-ubuntu20.04
ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y python3 python3-pip wget unzip && \
    pip install ctranslate2==3.18.0 requests==2.28.1 sentencepiece==0.1.99 && \
    mkdir /app && \
    cd /tmp && wget https://pretrained-nmt-models.s3.us-west-2.amazonaws.com/CTranslate2/nllb/nllb-200_3.3B_int8_ct2.zip && \
    wget https://pretrained-nmt-models.s3.us-west-2.amazonaws.com/CTranslate2/nllb/flores200_sacrebleu_tokenizer_spm.model && \
    unzip nllb-200_3.3B_int8_ct2.zip && \
    mv /tmp/nllb-200-3.3B-int8 /app/model && \
    mv /tmp/flores200_sacrebleu_tokenizer_spm.model /app/model/sp.model && \
    rm /tmp/*

ADD translate.py /app
WORKDIR /app

ENTRYPOINT ["/usr/bin/python3", "/app/translate.py"]