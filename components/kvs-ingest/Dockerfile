FROM ubuntu:24.04 AS build

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates cmake m4 g++ git make pkg-config libssl-dev libcurl4-openssl-dev liblog4cplus-dev \
    libgstreamer1.0-dev libgstreamer-plugins-base1.0-dev \
  && rm -rf /var/lib/apt/lists/*

# 依存（OpenSSL / curl / log4cplus）は OS のものを使う。SDK に自前ビルドさせると autoconf の段で落ちる。
ARG KVS_SDK_VERSION=v3.6.0
RUN git clone --depth 1 --branch "$KVS_SDK_VERSION" https://github.com/awslabs/amazon-kinesis-video-streams-producer-sdk-cpp.git /kvs \
  && cmake -S /kvs -B /kvs/build -DBUILD_GSTREAMER_PLUGIN=ON -DBUILD_DEPENDENCIES=OFF -DALIGNED_MEMORY_MODEL=ON \
  && make -C /kvs/build -j"$(nproc)" \
  && mkdir /opt/kvs \
  && cp -a /kvs/build/*.so* /kvs/build/dependency/libkvscproducer/kvscproducer-src/*.so* /opt/kvs/

FROM ubuntu:24.04

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates libssl3t64 libcurl4t64 liblog4cplus-2.0.5t64 \
    gstreamer1.0-tools gstreamer1.0-plugins-base gstreamer1.0-plugins-good gstreamer1.0-plugins-bad \
  && rm -rf /var/lib/apt/lists/*

COPY --from=build /opt/kvs /opt/kvs
ENV GST_PLUGIN_PATH=/opt/kvs LD_LIBRARY_PATH=/opt/kvs

# exec で置き換えて、停止時の SIGTERM を gst-launch に直接届ける。
CMD ["sh", "-c", "exec gst-launch-1.0 -e rtspsrc location=\"$RTSP_URL\" short-header=TRUE ! rtph264depay ! h264parse ! kvssink stream-name=\"$STREAM_NAME\" aws-region=\"$AWS_REGION\" access-key=\"$AWS_ACCESS_KEY_ID\" secret-key=\"$AWS_SECRET_ACCESS_KEY\""]
