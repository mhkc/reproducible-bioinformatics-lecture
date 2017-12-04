#!/bin/bash

# Download NGS sample
wget --directory-prefix=volumes/data 'ftp://ftp.sra.ebi.ac.uk/vol1/fastq/ERR418/ERR418327/ERR418327_1.fastq.gz'
wget --directory-prefix=volumes/data 'ftp://ftp.sra.ebi.ac.uk/vol1/fastq/ERR418/ERR418327/ERR418327_2.fastq.gz'

# Download reference file
wget -O ./volumes/data/blaZ.fna 'https://www.ebi.ac.uk/ena/data/view/M15526&display=fasta'
