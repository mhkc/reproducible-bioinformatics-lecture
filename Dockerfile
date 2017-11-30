FROM library/python:3.6.3  # The image is based on the official python 3.6.3 image which in turn is based on Debian

# Define version of the software being installed through wget with environment variables
ENV PYTHONUNBUFFERED="true"                     \
    BWA_VERSION="0.7.15"                        \
    SAMTOOLS_VERSION="1.5"

# Install pipeline dependencies from github releases.
# set -exu tells bash to:
#   1. exit if one subcommand crashes (finishes with non 0 exit code)
#   2. prints commands and arguments when they are executing
RUN set -exu                                                                                                              \
    && mkdir -p /usr/src/deps                                                                                             \
    # bwa                                                                                                                 \
    && cd /usr/src/deps                                                                                                   \
    && wget https://github.com/lh3/bwa/releases/download/v$BWA_VERSION/bwa-$BWA_VERSION.tar.bz2                           \
    && tar xjf bwa-$BWA_VERSION.tar.bz2                                                                                   \
    && cd bwa-$BWA_VERSION                                                                                                \
    && make                                                                                                               \
    && cp ./bwa /usr/local/bin/bwa                                                                                        \
                                                                                                                          \
    # samtools                                                                                                            \
    && cd /usr/src/deps                                                                                                   \
    && wget https://github.com/samtools/samtools/releases/download/$SAMTOOLS_VERSION/samtools-$SAMTOOLS_VERSION.tar.bz2   \
    && tar xjf samtools-$SAMTOOLS_VERSION.tar.bz2                                                                         \
    && cd samtools-$SAMTOOLS_VERSION                                                                                      \
    && make                                                                                                               \
    && make install

WORKDIR /usr/src  # Set working directory
COPY ./example_pipeline/requirements.txt /usr/src/requirements.txt  # Copy python requirements file
RUN pip install --no-cache-dir -r requirements.txt  #  Install python dependencies

CMD ["/bin/bash"]  # Run bash
