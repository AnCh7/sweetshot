# Using without any modifications these dockerfiles:
# https://github.com/mono/docker/blob/39b989ea0ef3e787fb75410521217cb7cb7df05e/5.0.1.1/Dockerfile
# https://github.com/JetBrains/teamcity-docker-agent/blob/master/Dockerfile

FROM jetbrains/teamcity-minimal-agent

ENV MONO_VERSION 5.0.1.1

RUN apt-get update \
  && apt-get install -y curl \
  && rm -rf /var/lib/apt/lists/*

RUN apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys 3FA7E0328081BFF6A14DA29AA6A19B38D3D831EF

RUN echo "deb http://download.mono-project.com/repo/debian jessie/snapshots/$MONO_VERSION main" > /etc/apt/sources.list.d/mono-official.list \
  && apt-get update \
  && apt-get install -y binutils mono-devel ca-certificates-mono fsharp mono-vbnc nuget referenceassemblies-pcl \
  && rm -rf /var/lib/apt/lists/* /tmp/*

RUN apt-get update && \
    apt-get install -y software-properties-common && add-apt-repository ppa:openjdk-r/ppa && apt-get update && \
    apt-get install -y git mercurial openjdk-8-jdk apt-transport-https ca-certificates && \
    \
    apt-key adv --keyserver hkp://p80.pool.sks-keyservers.net:80 --recv-keys 58118E89F3A912897C070ADBF76221572C52609D && \
    echo "deb https://apt.dockerproject.org/repo ubuntu-xenial main" > /etc/apt/sources.list.d/docker.list && \
    \
    apt-cache policy docker-engine && \
    apt-get update && \
    apt-get install -y docker-engine=1.13.0-0~ubuntu-xenial && \
    \
    apt-get clean all && \
    \
    usermod -aG docker buildagent

RUN until apt-get install --no-install-recommends --yes \
  tzdata \
 ; do apt-get --yes update ; done

COPY run-docker.sh /services/run-docker.sh