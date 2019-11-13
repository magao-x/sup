FROM centos:centos7
# Set up all repos we might need before clearing/regenerating the cache
RUN yum groupinstall -y 'Development Tools'
RUN yum install -y epel-release
RUN yum install -y centos-release-scl
RUN yum-config-manager --add-repo https://download.opensuse.org/repositories/network:/messaging:/zeromq:/release-stable/CentOS_7/network:messaging:zeromq:release-stable.repo
# Clear / regenerate cache
RUN yum clean all && rm -rf /var/cache/yum/* && yum makecache
# Install RPM-based packages to build sup
RUN yum install -y \
    sudo \
    zeromq-devel \
    wget
# Inspired by https://github.com/jupyter/docker-stacks/blob/master/base-notebook/Dockerfile
ENV CONDA_DIR=/opt/conda \
    SHELL=/bin/bash \
    LC_ALL=en_US.UTF-8 \
    LANG=en_US.UTF-8 \
    LANGUAGE=en_US.UTF-8
ENV PATH=$CONDA_DIR/bin:$PATH
ENV MINICONDA_VERSION=4.7.10 \
    MINICONDA_MD5=1c945f2b3335c7b2b15130b1b2dc5cf4 \
    CONDA_VERSION=4.7.12
RUN cd /tmp && \
    wget --quiet https://repo.continuum.io/miniconda/Miniconda3-${MINICONDA_VERSION}-Linux-x86_64.sh && \
    echo "${MINICONDA_MD5} *Miniconda3-${MINICONDA_VERSION}-Linux-x86_64.sh" | md5sum -c - && \
    /bin/bash Miniconda3-${MINICONDA_VERSION}-Linux-x86_64.sh -f -b -p $CONDA_DIR && \
    rm Miniconda3-${MINICONDA_VERSION}-Linux-x86_64.sh && \
    echo "conda ${CONDA_VERSION}" >> $CONDA_DIR/conda-meta/pinned && \
    $CONDA_DIR/bin/conda config --system --prepend channels conda-forge && \
    $CONDA_DIR/bin/conda config --system --set auto_update_conda false && \
    $CONDA_DIR/bin/conda config --system --set show_channel_urls true && \
    $CONDA_DIR/bin/conda install --quiet --yes conda && \
    $CONDA_DIR/bin/conda update --all --quiet --yes && \
    conda list python | grep '^python ' | tr -s ' ' | cut -d '.' -f 1,2 | sed 's/$/.*/' >> $CONDA_DIR/conda-meta/pinned && \
    conda clean --all -f -y
# Install node
RUN mkdir -p /opt/node && cd /tmp && \
    curl -OL https://nodejs.org/dist/v12.13.0/node-v12.13.0-linux-x64.tar.xz && \
    tar --strip-components=1 -xvf node-v12.13.0-linux-x64.tar.xz -C /opt/node
ENV PATH=/opt/node/bin:$PATH
RUN npm install --global yarn
# Install purepyindi
ENV PUREPYINDI_COMMIT=master
RUN git clone https://github.com/magao-x/purepyindi.git /opt/purepyindi && \
    cd /opt/purepyindi && \
    git checkout ${PUREPYINDI_COMMIT} && \
    pip install -e .[all]
# Install sup
RUN mkdir -p /opt/sup
ADD . /opt/sup
RUN cd /opt/sup && \
    pip install -e . && \
    make
EXPOSE 8000
ENTRYPOINT sup -b 0.0.0.0 -n 8000